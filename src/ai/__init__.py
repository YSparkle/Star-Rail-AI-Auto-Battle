"""
AI 接入模块
提供统一的对话式大模型调用接口，支持自定义提供商与 API Key
包含AI策略引擎用于游戏决策
"""

from .client import AIClient, AIConfig, AIProviderType
from .strategy_engine import AIStrategyEngine, CharacterInfo, EnemyInfo, BattleAction

__all__ = [
    "AIClient",
    "AIConfig",
    "AIProviderType",
    "AIStrategyEngine",
    "CharacterInfo",
    "EnemyInfo",
    "BattleAction",
]
