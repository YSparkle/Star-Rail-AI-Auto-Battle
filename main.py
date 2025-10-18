"""
星穹铁道AI自动战斗系统 - 主程序
整合所有模块，提供统一的战斗自动化功能
"""

import time
import logging
from typing import Dict, List, Optional

from src.image_recognition.recognizer import ImageRecognizer
from src.decision_engine.decision import BattleDecision
from src.game_control.controller import GameController

# 新增：配置、AI提供商、记忆、策略与数据计算
from src.config import AppConfig
from src.ai import LLMClient
from src.ai.memory import MemoryStore
from src.stats.calculator import compute_team
from src.modes import MODE_STRATEGY_MAP
from src.strategies.base import StrategyPlan


class StarRailAutoBattle:
    """星穹铁道自动战斗主类"""

    def __init__(self):
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # 初始化各个模块
        self.image_recognizer = ImageRecognizer()
        self.decision_engine = BattleDecision()
        self.game_controller = GameController()

        # 新增：配置/AI/记忆/计划
        self.config: Optional[AppConfig] = None
        self.llm: Optional[LLMClient] = None
        self.memory: Optional[MemoryStore] = None
        self.generated_plans: List[StrategyPlan] = []
        self.selected_plan: Optional[StrategyPlan] = None

        # 战斗状态
        self.is_running = False
        self.battle_count = 0
        self.victory_count = 0

    def initialize(self):
        """初始化系统"""
        self.logger.info("正在初始化星穹铁道AI自动战斗系统...")
        # 加载配置
        self.config = AppConfig.load()
        self.logger.info(f"AI提供商: {self.config.ai_provider}, 模型: {self.config.ai_model}")
        # 初始化记忆
        self.memory = MemoryStore() if self.config.persist_memory else None
        if self.memory:
            self.logger.info("已启用记忆持久化（game_data/memory.json）")
        # 初始化AI客户端
        self.llm = LLMClient(
            provider=self.config.ai_provider,
            api_key=self.config.ai_api_key,
            base_url=self.config.ai_base_url,
            model=self.config.ai_model,
            timeout=self.config.timeout_sec,
        )

        # 模式准备：用户手动切换
        self.prepare_mode()

        # 规划阶段：根据队伍/敌人信息生成策略方案
        self.plan_phase()

        self.logger.info("系统初始化完成")

    def prepare_mode(self):
        """引导用户打开星铁并手动切换到目标模式。"""
        mode = self.config.mode if self.config else "material_farm"
        self.logger.info(
            f"请手动打开《崩坏：星穹铁道》并切换到目标模式: {mode}。按回车开始策略规划...")
        try:
            # 尽量不阻塞CI，这里加超时保护
            if self.config and self.config.interactive_select:
                input()
        except Exception:
            # 非交互环境直接继续
            pass

    def plan_phase(self):
        """生成策略方案（包含本地结构化策略与AI文本建议），并供用户选择是否凹。"""
        assert self.config is not None

        # 计算队伍与敌人有效属性
        team_stats = compute_team(self.config.team, self.config.enemies)
        if self.memory:
            self.memory.set("last_team", {
                "team": self.config.team,
                "enemies": self.config.enemies,
            })

        # 选择对应模式的策略实现
        strategy_cls = MODE_STRATEGY_MAP.get(self.config.mode)
        if not strategy_cls:
            self.logger.warning(f"未知模式: {self.config.mode}，将使用 material_farm 策略")
            strategy_cls = MODE_STRATEGY_MAP["material_farm"]
        strategy = strategy_cls(allow_rng_fishing=self.config.allow_rng_fishing)

        context: Dict = {
            "abyss_buffs": (self.config.abyss or {}).get("buffs", []),
        }
        self.generated_plans = strategy.generate_plans(team_stats, context)

        # 调用AI提供文本级策略建议（可选）
        ai_text = self._request_ai_suggestions(team_stats, context)
        if self.memory:
            self.memory.set("last_ai_text", ai_text)

        # 展示方案并选择
        self._present_plans(ai_text)
        self.selected_plan = self._select_plan()
        if self.memory and self.selected_plan:
            self.memory.set("selected_plan", {
                "name": self.selected_plan.name,
                "expected_rounds": self.selected_plan.expected_rounds,
                "rng_requirements": self.selected_plan.rng_requirements,
                "steps": [s.__dict__ for s in self.selected_plan.steps],
            })

    def _request_ai_suggestions(self, team_stats, context: Dict) -> str:
        try:
            if not self.llm:
                return ""
            # 将队伍与敌人摘要描述成提示
            team_summary = []
            for c in team_stats.characters:
                eff = c.effective
                team_summary.append(
                    f"{c.name}(spd={eff.get('spd', 0)}, atk={eff.get('atk', 0)}, crit={eff.get('crit_rate', 0)})"
                )
            enemy = team_stats.enemy
            enemy_desc = f"敌人x{enemy.count}, 弱点={','.join(enemy.weakness)}"

            messages = [
                {"role": "user", "content": (
                    "根据以下队伍和敌人信息，提供2-3个通关策略方案（标注是否需要凹），"
                    "每个方案给出期望轮数与简要执行思路。\n"
                    f"队伍: {', '.join(team_summary)}\n"
                    f"敌人: {enemy_desc}"
                )}
            ]
            return self.llm.generate(self.config.system_prompt, messages)
        except Exception as e:
            return f"[AI建议生成失败] {e}"

    def _present_plans(self, ai_text: str):
        self.logger.info("AI文本建议：\n" + (ai_text or "(无)"))
        self.logger.info("候选策略方案：")
        for idx, p in enumerate(self.generated_plans):
            self.logger.info(
                f"[{idx}] {p.name} | 期望轮数: {p.expected_rounds} | RNG: {p.rng_requirements}")

    def _select_plan(self) -> Optional[StrategyPlan]:
        if not self.generated_plans:
            return None
        choice = self.config.plan_choice if self.config else None
        if choice is None and self.config and self.config.interactive_select:
            try:
                raw = input("请输入选择的方案编号（回车默认0）: ").strip()
                choice = int(raw) if raw else 0
            except Exception:
                choice = 0
        if choice is None:
            choice = 0
        choice = max(0, min(choice, len(self.generated_plans) - 1))
        self.logger.info(f"已选择策略方案: [{choice}] {self.generated_plans[choice].name}")
        return self.generated_plans[choice]

    def start_battle(self):
        """开始自动战斗"""
        self.logger.info("开始自动战斗模式")
        self.is_running = True

        try:
            while self.is_running:
                self.battle_loop()
                time.sleep(0.1)  # 防止CPU占用过高

        except KeyboardInterrupt:
            self.logger.info("收到停止信号，正在停止...")
            self.stop_battle()

    def stop_battle(self):
        """停止自动战斗"""
        self.is_running = False
        self.logger.info("自动战斗已停止")

    def battle_loop(self):
        """主要战斗循环"""
        # 1. 图像识别
        game_data = self.collect_game_data()

        # 2. 决策分析（若存在选定策略，可在未来将步骤映射到具体操作）
        battle_analysis = self.decision_engine.analyze_battle_situation(game_data)
        action = self.decision_engine.choose_action(battle_analysis)

        # 3. 执行操作
        self.execute_action(action)

        # 4. 更新状态
        self.update_battle_status(game_data)

    def collect_game_data(self) -> Dict:
        """收集游戏数据"""
        game_data = {
            "team_health": self.image_recognizer.detect_health_bars(),
            "skill_cooldowns": self.image_recognizer.detect_skill_cooldowns(),
            "battle_state": self.image_recognizer.detect_battle_state(),
            "timestamp": time.time()
        }
        return game_data

    def execute_action(self, action: str):
        """执行决策动作"""
        self.logger.info(f"执行动作: {action}")

        if "治疗" in action:
            self.game_controller.use_skill('q')  # 假设Q是治疗技能
        elif "群体攻击" in action:
            self.game_controller.use_skill('e')  # 假设E是群体技能
        elif "单体攻击" in action:
            self.game_controller.attack()
        else:
            self.game_controller.attack()

    def update_battle_status(self, game_data: Dict):
        """更新战斗状态"""
        battle_state = game_data.get("battle_state", "非战斗")

        if battle_state == "胜利":
            self.victory_count += 1
            self.battle_count += 1
            self.logger.info(f"战斗胜利！总胜利次数: {self.victory_count}")
            time.sleep(2)  # 等待战斗结束界面

        elif battle_state == "失败":
            self.battle_count += 1
            self.logger.info(f"战斗失败！总战斗次数: {self.battle_count}")

    def get_statistics(self) -> Dict:
        """获取战斗统计"""
        if self.battle_count == 0:
            return {"message": "暂无战斗数据"}

        win_rate = (self.victory_count / self.battle_count) * 100
        return {
            "total_battles": self.battle_count,
            "victories": self.victory_count,
            "win_rate": f"{win_rate:.1f}%"
        }


def main():
    """主函数"""
    auto_battle = StarRailAutoBattle()

    try:
        auto_battle.initialize()
        auto_battle.start_battle()
    except Exception as e:
        auto_battle.logger.error(f"程序出错: {e}")
    finally:
        auto_battle.stop_battle()


if __name__ == "__main__":
    main()
