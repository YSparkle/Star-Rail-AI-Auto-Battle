"""
星穹铁道AI自动战斗系统 - 主程序
整合所有模块，提供统一的战斗自动化功能
"""

import time
import logging
from typing import Dict, List
from src.image_recognition.recognizer import ImageRecognizer
from src.decision_engine.decision import BattleDecision
from src.game_control.controller import GameController

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

        # 战斗状态
        self.is_running = False
        self.battle_count = 0
        self.victory_count = 0

    def initialize(self):
        """初始化系统"""
        self.logger.info("正在初始化星穹铁道AI自动战斗系统...")
        # TODO: 加载配置文件和模板图像
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
        auto_battle.start_battle()
    except Exception as e:
        auto_battle.logger.error(f"程序出错: {e}")
    finally:
        auto_battle.stop_battle()

if __name__ == "__main__":
    main()