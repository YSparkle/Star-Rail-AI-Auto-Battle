"""
星穹铁道AI自动战斗系统 - 主程序
基于AI视觉识别和策略生成的自动战斗系统
"""

import time
import logging
from typing import Dict, Optional

from src.image_recognition.recognizer import ImageRecognizer
from src.game_control.controller import GameController

# AI策略引擎
from src.config import load_config
from src.ai import AIClient, AIConfig, AIProviderType, AIStrategyEngine
from src.storage.memory import MemoryStore
from src.decision_engine.ai_decision import AIBattleDecision


class StarRailAutoBattle:
    """星穹铁道AI自动战斗主类"""

    def __init__(self):
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # 初始化基础模块
        self.image_recognizer = ImageRecognizer()
        self.game_controller = GameController()
        self.memory = MemoryStore()

        # 配置与AI
        self.config: Dict = {}
        self.ai_client: Optional[AIClient] = None
        self.ai_strategy_engine: Optional[AIStrategyEngine] = None
        self.ai_decision: Optional[AIBattleDecision] = None

        # 运行模式
        self.plan_only = False  # 仅规划模式
        self.scan_only = False  # 仅扫描模式

        # 战斗状态
        self.is_running = False
        self.battle_count = 0
        self.victory_count = 0

    def _setup_ai(self):
        """设置AI客户端和策略引擎"""
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
        except Exception as e:
            self.logger.warning(f"AI配置解析失败：{e}，使用默认配置")
            cfg = AIConfig(enabled=False)
        
        self.ai_client = AIClient(cfg)
        
        if self.ai_client.is_available():
            self.logger.info("AI已启用，使用视觉识别和智能决策")
            self.ai_strategy_engine = AIStrategyEngine(
                ai_client=self.ai_client,
                game_controller=self.game_controller,
                memory_store=self.memory,
                logger=self.logger
            )
            self.ai_decision = AIBattleDecision(
                ai_strategy_engine=self.ai_strategy_engine,
                logger=self.logger
            )
        else:
            self.logger.warning("AI未启用，将无法使用自动战斗功能")

    def _apply_input_settings(self):
        """应用键位与输入安全设置"""
        inp = (self.config.get("input", {}) or {})
        keybinds = (inp.get("keybinds") or {})
        enabled = bool(inp.get("enable_inputs", False))
        try:
            self.game_controller.update_settings(keybinds=keybinds, enable_inputs=enabled)
        except Exception as e:
            self.logger.warning(f"更新游戏控制器设置失败：{e}")

    def scan_characters_and_enemies(self):
        """扫描角色和敌人信息（使用AI识图）"""
        if not self.ai_strategy_engine:
            self.logger.error("AI策略引擎未初始化，无法扫描")
            return
        
        self.logger.info("="*60)
        self.logger.info("开始扫描模式")
        self.logger.info("="*60)
        
        ui_regions = self.config.get("ui_regions", {})
        roster_config = self.config.get("roster", [])
        enemy_config = self.config.get("enemy", {})
        
        # 扫描角色
        self.logger.info(f"准备扫描 {len(roster_config)} 个角色...")
        self.logger.info("请确保已在游戏中打开角色详情界面")
        time.sleep(2)
        
        for char_cfg in roster_config:
            name = char_cfg.get("name", "未知角色")
            element = char_cfg.get("element", "Physical")
            path = char_cfg.get("path", "Hunt")
            
            self.logger.info(f"正在扫描角色：{name}")
            try:
                char_info = self.ai_strategy_engine.scan_character_with_ai(
                    name=name,
                    element=element,
                    path=path,
                    ui_regions=ui_regions
                )
                self.ai_strategy_engine.characters.append(char_info)
                self.logger.info(f"✓ 角色 {name} 扫描完成")
                self.logger.info(f"  属性：{char_info.stats}")
                self.logger.info(f"  技能数：{len(char_info.skills)}")
            except Exception as e:
                self.logger.error(f"✗ 角色 {name} 扫描失败：{e}")
            
            time.sleep(1)
        
        # 扫描敌人
        if enemy_config:
            enemy_name = enemy_config.get("name", "未知敌人")
            self.logger.info(f"正在扫描敌人：{enemy_name}")
            self.logger.info("请确保已在游戏中打开敌人信息界面")
            time.sleep(2)
            
            try:
                enemy_info = self.ai_strategy_engine.scan_enemy_with_ai(
                    name=enemy_name,
                    ui_regions=ui_regions
                )
                self.ai_strategy_engine.enemies.append(enemy_info)
                self.logger.info(f"✓ 敌人 {enemy_name} 扫描完成")
                self.logger.info(f"  属性：{enemy_info.stats}")
                self.logger.info(f"  弱点：{enemy_info.weaknesses}")
            except Exception as e:
                self.logger.error(f"✗ 敌人 {enemy_name} 扫描失败：{e}")
        
        self.logger.info("="*60)
        self.logger.info("扫描完成！所有信息已保存到记忆中")
        self.logger.info("="*60)

    def generate_strategy(self):
        """生成战斗策略"""
        if not self.ai_strategy_engine:
            self.logger.error("AI策略引擎未初始化，无法生成策略")
            return
        
        self.logger.info("="*60)
        self.logger.info("开始生成战斗策略")
        self.logger.info("="*60)
        
        mode = self.config.get("mode", "material_farm")
        preferences = self.config.get("preferences", {})
        
        try:
            strategy = self.ai_strategy_engine.generate_strategy(mode, preferences)
            
            self.logger.info("策略生成完成！")
            self.logger.info("")
            
            # 显示分析结果
            analysis = strategy.get("analysis", {})
            self.logger.info("【战斗分析】")
            for key, value in analysis.items():
                self.logger.info(f"  {key}: {value}")
            self.logger.info("")
            
            # 显示方案A
            plan_a = strategy.get("plan_a", {})
            self.logger.info("【方案A - 稳定】")
            self.logger.info(f"  名称：{plan_a.get('name')}")
            self.logger.info(f"  描述：{plan_a.get('description')}")
            self.logger.info(f"  预计回合数：{plan_a.get('expected_rounds')}")
            self.logger.info("")
            
            # 显示方案B
            plan_b = strategy.get("plan_b", {})
            self.logger.info("【方案B - 极限】")
            self.logger.info(f"  名称：{plan_b.get('name')}")
            self.logger.info(f"  描述：{plan_b.get('description')}")
            self.logger.info(f"  预计回合数：{plan_b.get('expected_rounds')}")
            if plan_b.get("requires_reroll"):
                reroll = plan_b.get("reroll_condition", {})
                self.logger.info(f"  需要凹本：")
                self.logger.info(f"    - 目标角色：{reroll.get('target_character')}")
                self.logger.info(f"    - 触发时机：{reroll.get('trigger_timing')}")
                self.logger.info(f"    - 目的：{reroll.get('purpose')}")
                self.logger.info(f"    - 最大重试：{reroll.get('max_retries')}")
            self.logger.info("")
            
            # 显示推荐
            recommendation = strategy.get("recommendation", "")
            self.logger.info(f"【推荐】{recommendation}")
            self.logger.info("")
            
            self.logger.info("="*60)
            self.logger.info("请选择方案（在config.json中设置preferences.selected_option为A或B）")
            self.logger.info("然后在游戏中切换到对应模式界面，准备开始自动战斗")
            self.logger.info("="*60)
            
        except Exception as e:
            self.logger.error(f"策略生成失败：{e}")

    def initialize(self):
        """初始化系统"""
        self.logger.info("正在初始化星穹铁道AI自动战斗系统...")
        
        # 加载配置
        self.config = load_config()
        
        # 读取运行模式
        run_cfg = self.config.get("run", {})
        self.plan_only = bool(run_cfg.get("plan_only", False))
        self.scan_only = bool(run_cfg.get("scan_only", False))
        
        # 设置AI
        self._setup_ai()
        
        # 应用输入设置
        self._apply_input_settings()
        
        if self.scan_only:
            self.logger.info("已启用仅扫描模式：将扫描角色和敌人信息并保存")
        elif self.plan_only:
            self.logger.info("已启用仅规划模式：将生成策略，不会启动自动战斗")
        
        self.logger.info("系统初始化完成")

    def start_battle(self):
        """开始自动战斗"""
        if not self.ai_decision:
            self.logger.error("AI决策引擎未初始化，无法开始战斗")
            return
        
        self.logger.info("="*60)
        self.logger.info("开始AI自动战斗模式")
        self.logger.info("="*60)
        self.logger.info("提示：")
        self.logger.info("  - 请确保已在游戏中切换到战斗模式")
        self.logger.info("  - AI将实时分析画面并做出决策")
        self.logger.info("  - 按 Ctrl+C 可以随时停止")
        self.logger.info("="*60)
        
        self.is_running = True
        
        try:
            while self.is_running:
                self.battle_loop()
                time.sleep(0.5)  # 控制决策频率
        
        except KeyboardInterrupt:
            self.logger.info("收到停止信号...")
            self.stop_battle()

    def stop_battle(self):
        """停止自动战斗"""
        self.is_running = False
        self.logger.info("自动战斗已停止")
        
        # 显示统计
        stats = self.get_statistics()
        self.logger.info("="*60)
        self.logger.info("战斗统计")
        self.logger.info(f"  总战斗数：{stats.get('total_battles', 0)}")
        self.logger.info(f"  胜利次数：{stats.get('victories', 0)}")
        self.logger.info(f"  胜率：{stats.get('win_rate', 'N/A')}")
        self.logger.info("="*60)

    def battle_loop(self):
        """AI驱动的战斗循环"""
        try:
            # AI做出决策
            action = self.ai_decision.make_decision()
            
            # 执行动作
            self.ai_decision.execute_action(action, self.game_controller)
            
            # 检测战斗结果（简化版，实际可以让AI识别）
            # TODO: 让AI识别战斗是否结束
            
        except Exception as e:
            self.logger.error(f"战斗循环出错：{e}")

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
        
        # 根据运行模式执行不同操作
        if auto_battle.scan_only:
            # 仅扫描模式
            auto_battle.scan_characters_and_enemies()
            return
        
        if auto_battle.plan_only:
            # 仅规划模式：先扫描，再生成策略
            auto_battle.scan_characters_and_enemies()
            auto_battle.generate_strategy()
            return
        
        # 完整模式：扫描 -> 生成策略 -> 自动战斗
        if not auto_battle.ai_strategy_engine:
            auto_battle.logger.error("AI未启用，无法继续")
            return
        
        # 检查是否已有扫描数据
        if not auto_battle.ai_strategy_engine.characters:
            auto_battle.logger.info("未找到角色数据，开始扫描...")
            auto_battle.scan_characters_and_enemies()
        
        # 生成策略
        auto_battle.generate_strategy()
        
        # 确认后开始战斗
        auto_battle.logger.info("准备开始自动战斗...")
        auto_battle.logger.info("请确保：")
        auto_battle.logger.info("  1. 已在config.json中选择了方案（A或B）")
        auto_battle.logger.info("  2. 已在游戏中切换到对应模式界面")
        auto_battle.logger.info("  3. 已在config.json中启用了输入（enable_inputs: true）")
        auto_battle.logger.info("")
        input("按回车键开始自动战斗...")
        
        auto_battle.start_battle()
        
    except Exception as e:
        auto_battle.logger.error(f"程序出错：{e}", exc_info=True)
    finally:
        auto_battle.stop_battle()


if __name__ == "__main__":
    main()
