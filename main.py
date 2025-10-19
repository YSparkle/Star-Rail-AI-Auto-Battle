"""
星穹铁道AI自动战斗系统 - 主程序
整合所有模块，提供统一的战斗自动化功能
"""

import time
import logging
from typing import Dict, Optional

from src.image_recognition.recognizer import ImageRecognizer
from src.decision_engine.decision import BattleDecision
from src.game_control.controller import GameController

# 新增：配置、AI、策略与记忆存储
from src.config import load_config
from src.ai import AIClient, AIConfig, AIProviderType
from src.storage.memory import MemoryStore
from src.models.character import character_from_config
from src.models.enemy import enemy_from_config
from src.models.combat import compute_turn_order, summarize_team_estimates, analyze_team_enemy_synergy
from src.strategy import (
    StrategyManager,
    MaterialFarmStrategy,
    AbyssStrategy,
    StrategyContext,
    CustomStrategy,
)


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

        # 新增：配置、AI、策略与记忆
        self.config: Dict = {}
        self.ai_client: Optional[AIClient] = None
        self.memory = MemoryStore()
        self.strategy_manager = StrategyManager({
            "material_farm": MaterialFarmStrategy(),
            "abyss": AbyssStrategy(),
            "custom": CustomStrategy(),
        })
        self.strategy_plan = None
        # 仅规划模式（不启动自动战斗）
        self.plan_only = False

        # 战斗状态
        self.is_running = False
        self.battle_count = 0
        self.victory_count = 0

    def _setup_ai(self):
        ai_cfg = self.config.get("ai", {})
        try:
            cfg = AIConfig(
                enabled=ai_cfg.get("enabled", False),
                provider=AIProviderType(ai_cfg.get("provider", "openai_compatible")),
                api_key=ai_cfg.get("api_key"),
                base_url=ai_cfg.get("base_url", "https://api.openai.com/v1"),
                model=ai_cfg.get("model", "gpt-4o-mini"),
                system_prompt=ai_cfg.get("system_prompt"),
                timeout=int(ai_cfg.get("timeout", 60)),
                endpoint=ai_cfg.get("endpoint"),
                headers=ai_cfg.get("headers"),
            )
        except Exception:
            # provider 解析失败等情况，回落默认
            cfg = AIConfig(enabled=False)
        self.ai_client = AIClient(cfg)

    def _prepare_strategy(self):
        # 计算角色衍生属性
        roster_cfg = self.config.get("roster", [])
        characters = [character_from_config(c) for c in roster_cfg]
        computed_chars = [{"name": c.name, **c.computed} for c in characters]

        # 计算敌人衍生属性
        enemy_cfg = self.config.get("enemy", {})
        enemy_obj = enemy_from_config(enemy_cfg or {})
        computed_enemy = {
            "name": enemy_obj.name,
            **enemy_obj.computed,
            "weaknesses": enemy_obj.weaknesses,
            "resistances": enemy_obj.resistances,
            "buffs": enemy_obj.buffs,
        }

        # 团队行动顺序与伤害估计
        turn_order = compute_turn_order(computed_chars)
        team_estimates = summarize_team_estimates(computed_chars)
        synergy = analyze_team_enemy_synergy(roster_cfg, computed_chars, enemy_cfg)

        computed_all = {
            "characters": computed_chars,
            "turn_order": turn_order,
            "team_estimates": team_estimates,
            "enemy": computed_enemy,
            "synergy": synergy,
        }

        ctx = StrategyContext(
            mode=self.config.get("mode", "material_farm"),
            preferences=self.config.get("preferences", {}),
            roster=roster_cfg,
            enemy=enemy_cfg,
            computed=computed_all,
        )

        # 生成基础方案（启用 AI 时请辅助生成详细可选策略）
        self.strategy_plan = self.strategy_manager.plan(ctx)

        # 如启用 AI，再生成更详细的文案供玩家阅读与选择
        ai_text_path = None
        if self.ai_client and self.ai_client.is_available():
            context_for_ai = {
                "mode": ctx.mode,
                "preferences": ctx.preferences,
                "roster": ctx.roster,
                "enemy": ctx.enemy,
                "computed": ctx.computed,
            }
            ai_text = self.ai_client.summarize_to_plan(context_for_ai)
            ai_text_path = self.memory.save("ai_strategy_text", {"plan": ai_text})
            self.logger.info(f"AI 策略文案已保存: {ai_text_path}")

        # 永久化保存角色、敌人与计算信息，便于后续记忆
        self.memory.save("characters", {"list": ctx.roster, "computed": computed_chars})
        self.memory.save("enemy", enemy_cfg)
        self.memory.save("computed", computed_all)
        # 同步保存 AI 与偏好配置，便于后续上下文
        self.memory.save("ai_config", self.config.get("ai", {}))
        self.memory.save("preferences", self.config.get("preferences", {}))

        if self.strategy_plan:
            self.memory.save("strategy_plan", {
                "name": self.strategy_plan.name,
                "description": self.strategy_plan.description,
                "options": self.strategy_plan.options,
                "recommends": self.strategy_plan.recommends,
                "steps": self.strategy_plan.steps,
                "requires_reroll": self.strategy_plan.requires_reroll,
                "expected_rounds": self.strategy_plan.expected_rounds,
            })

        # 记录用户偏好选择（如 A/B 策略）
        selected = (self.config.get("preferences", {}).get("selected_option") or "").upper()
        if selected in ("A", "B"):
            self.memory.save("selected_option", {"value": selected})

        # 日志提示：基础契合度与手动切换模式
        syn = computed_all.get("synergy", {})
        self.logger.info(
            f"元素覆盖: {syn.get('element_counts', {})} | 弱点命中: {syn.get('weakness_match_names', [])} | 覆盖率: {syn.get('weakness_match_ratio')}"
        )
        self.logger.info(
            f"敌方对队伍元素的平均抗性: {syn.get('avg_enemy_resistance_vs_team')} | 平均/最高速度: {syn.get('avg_speed')}/{syn.get('max_speed')}"
        )
        self.logger.info("请在游戏中手动切换到目标模式界面，然后开始执行。")
        if self.strategy_plan:
            self.logger.info(f"已为模式 {ctx.mode} 生成策略：{self.strategy_plan.name}")
            self.logger.info(f"策略说明：{self.strategy_plan.description}")
            for i, opt in enumerate(self.strategy_plan.options, 1):
                self.logger.info(f"方案 {i}: {opt}")
            if self.strategy_plan.recommends:
                self.logger.info(f"推荐：{self.strategy_plan.recommends}")
            if selected in ( "A", "B" ):
                self.logger.info(f"已选择策略：{selected}（允许凹本: {bool(ctx.preferences.get('allow_reroll', True))}）")

        # 汇总保存一个规划总览，便于查看
        summary = {
            "mode": ctx.mode,
            "preferences": ctx.preferences,
            "computed": computed_all,
            "strategy_plan": self.strategy_plan.__dict__ if self.strategy_plan else None,
            "ai_text_file": ai_text_path,
        }
        self.memory.save("planning_summary", summary)

    def initialize(self):
        """初始化系统"""
        self.logger.info("正在初始化星穹铁道AI自动战斗系统...")
        # 加载配置与模板
        self.config = load_config()
        # 读取运行模式
        self.plan_only = bool(self.config.get("run", {}).get("plan_only", False))
        self._setup_ai()
        self._prepare_strategy()
        if self.plan_only:
            self.logger.info("已启用仅规划模式：将生成策略与记忆，不会启动自动战斗。")
        self.logger.info("系统初始化完成")

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

        # 2. 决策分析
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
        if auto_battle.plan_only:
            # 仅规划模式下直接退出（已保存策略与记忆）
            return
        auto_battle.start_battle()
    except Exception as e:
        auto_battle.logger.error(f"程序出错: {e}")
    finally:
        auto_battle.stop_battle()


if __name__ == "__main__":
    main()
