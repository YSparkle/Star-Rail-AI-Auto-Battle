"""
刷材料（如历战余响、历战虚影、历战训练）模式策略
目标：减少回合数、提高通关效率
"""
from __future__ import annotations

from typing import Any, Dict, List
from .base import Strategy, StrategyPlan, StrategyContext


class MaterialFarmStrategy(Strategy):
    def _heuristic_steps(self, ctx: StrategyContext) -> List[str]:
        steps: List[str] = []
        steps.append("优先开怪弱点的群攻或范围类技能以快速清场")
        steps.append("保证主C能连续释放终结技/战技，副C补刀")
        steps.append("若可提前回能，利用普攻触发追加攻击/充能")
        steps.append("必要时通过换位/延缓行动，保证击杀顺序与溢伤最小化")
        return steps

    def plan(self, ctx: StrategyContext) -> StrategyPlan:
        allow_reroll = bool(ctx.preferences.get("allow_reroll", True))
        options = [
            "A 稳定速刷：不开额外凹点，以可控循环为主",
            "B 极限速刷：允许凹点（例如吃特定攻击回能、追击触发等）",
        ]
        desc = (
            "目标是尽可能减少平均回合数并缩短单局时长。优先范围清场，"
            "在保证循环不断的前提下争取开场爆发与能量管理。"
        )
        steps = self._heuristic_steps(ctx)
        plan = StrategyPlan(
            name="刷材料 - 快速周回方案",
            description=desc,
            options=options,
            recommends=("若队伍循环稳定，建议选择A，避免反复重开；追求极限时间可选B"),
            steps=steps,
            requires_reroll=allow_reroll,
            expected_rounds=2,
        )
        return plan
