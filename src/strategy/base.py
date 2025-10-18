"""
策略基础类型与管理器
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StrategyPlan:
    name: str
    description: str
    options: List[str] = field(default_factory=list)  # 给玩家选择的不同策略路线
    recommends: Optional[str] = None  # 给出推荐选择的理由
    steps: List[str] = field(default_factory=list)  # 执行步骤
    requires_reroll: bool = False  # 是否涉及“凹”
    expected_rounds: Optional[int] = None


@dataclass
class StrategyContext:
    mode: str  # material_farm | abyss | custom
    preferences: Dict[str, Any]
    roster: List[Dict[str, Any]]  # 原始配置中的角色
    enemy: Dict[str, Any]  # 敌人与关卡信息
    computed: Dict[str, Any] = field(default_factory=dict)  # 计算后的各类信息


class Strategy:
    def plan(self, ctx: StrategyContext) -> StrategyPlan:
        raise NotImplementedError


class StrategyManager:
    def __init__(self, strategies: Dict[str, Strategy]):
        self.strategies = strategies

    def plan(self, ctx: StrategyContext) -> StrategyPlan:
        st = self.strategies.get(ctx.mode)
        if not st:
            raise ValueError(f"未找到模式对应的策略: {ctx.mode}")
        return st.plan(ctx)
