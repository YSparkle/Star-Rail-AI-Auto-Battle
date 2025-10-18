"""
策略模块：按模式分离的战斗/规划策略
- MaterialFarmStrategy: 刷材料，追求更少回合、更快结算
- AbyssStrategy: 深渊/混沌回忆，结合祝福制定最少轮数与行动顺序
"""
from .base import StrategyPlan, StrategyContext, Strategy, StrategyManager
from .material_farm import MaterialFarmStrategy
from .abyss import AbyssStrategy

__all__ = [
    "StrategyPlan",
    "StrategyContext",
    "Strategy",
    "StrategyManager",
    "MaterialFarmStrategy",
    "AbyssStrategy",
]
