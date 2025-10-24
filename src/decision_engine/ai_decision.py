"""
AI驱动的战斗决策引擎
- 替代原有的硬编码规则
- 通过AI实时分析战斗状况并做出决策
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.ai.strategy_engine import AIStrategyEngine, BattleAction


@dataclass
class BattleState:
    """战斗状态"""
    current_round: int
    executed_actions: List[Dict[str, Any]]
    battle_data: Dict[str, Any]  # 识别到的当前战斗数据


class AIBattleDecision:
    """AI驱动的战斗决策类"""
    
    def __init__(self, ai_strategy_engine: AIStrategyEngine, logger: Optional[logging.Logger] = None):
        """
        Args:
            ai_strategy_engine: AI策略引擎
            logger: 日志记录器
        """
        self.ai_engine = ai_strategy_engine
        self.logger = logger or logging.getLogger(__name__)
        
        # 战斗状态
        self.current_round = 0
        self.executed_actions: List[Dict[str, Any]] = []
        self.battle_started = False
    
    def start_battle(self):
        """开始新战斗"""
        self.current_round = 0
        self.executed_actions = []
        self.battle_started = True
        self.logger.info("战斗开始")
    
    def end_battle(self, result: str):
        """结束战斗"""
        self.battle_started = False
        self.logger.info(f"战斗结束：{result}")
        
        # 保存战斗记录供学习
        battle_record = {
            "rounds": self.current_round,
            "actions": self.executed_actions,
            "result": result
        }
        self.ai_engine.memory.save(f"battle_record_{int(time.time())}", battle_record)
    
    def make_decision(self) -> BattleAction:
        """
        做出战斗决策
        
        Returns:
            BattleAction: 下一步要执行的动作
        """
        if not self.battle_started:
            self.start_battle()
        
        self.current_round += 1
        self.logger.info(f"第 {self.current_round} 回合，AI正在分析...")
        
        try:
            # 让AI策略引擎分析当前状况并做决策
            action = self.ai_engine.make_battle_decision(
                current_round=self.current_round,
                executed_actions=self.executed_actions
            )
            
            # 记录动作
            action_record = {
                "round": self.current_round,
                "action_type": action.action_type,
                "character_index": action.character_index,
                "target_direction": action.target_direction,
                "reasoning": action.reasoning
            }
            self.executed_actions.append(action_record)
            
            self.logger.info(f"AI决策：{action.action_type} - {action.reasoning}")
            
            return action
            
        except Exception as e:
            self.logger.error(f"AI决策失败：{e}，使用保守策略")
            # 失败时返回保守的默认动作
            return BattleAction(
                action_type="basic_attack",
                reasoning="AI决策失败，使用保守策略（普攻）"
            )
    
    def execute_action(self, action: BattleAction, game_controller):
        """
        执行战斗动作
        
        Args:
            action: 要执行的动作
            game_controller: 游戏控制器
        """
        self.logger.info(f"执行动作：{action.action_type} - {action.reasoning}")
        
        try:
            if action.action_type == "ultimate":
                if action.character_index:
                    game_controller.use_ultimate(action.character_index)
                else:
                    self.logger.warning("大招动作缺少角色索引")
            
            elif action.action_type == "skill":
                game_controller.use_skill()
            
            elif action.action_type == "basic_attack":
                game_controller.use_basic_attack()
            
            elif action.action_type == "switch_target_left":
                game_controller.select_target_left()
            
            elif action.action_type == "switch_target_right":
                game_controller.select_target_right()
            
            elif action.action_type == "wait":
                self.logger.info("等待...")
                time.sleep(0.5)
            
            else:
                self.logger.warning(f"未知动作类型：{action.action_type}")
        
        except Exception as e:
            self.logger.error(f"执行动作失败：{e}")


# 为了兼容性，保留一个简化的接口
def make_ai_decision(ai_engine: AIStrategyEngine, battle_state: BattleState) -> Dict[str, Any]:
    """
    简化的AI决策接口
    
    Args:
        ai_engine: AI策略引擎
        battle_state: 当前战斗状态
    
    Returns:
        决策字典
    """
    action = ai_engine.make_battle_decision(
        current_round=battle_state.current_round,
        executed_actions=battle_state.executed_actions
    )
    
    return {
        "action_type": action.action_type,
        "character_index": action.character_index,
        "target_direction": action.target_direction,
        "reasoning": action.reasoning
    }


import time
