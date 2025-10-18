"""
自定义模式策略
- 用于在非预设（材料/深渊）场景下，生成基础方案框架
"""
from __future__ import annotations

from typing import List
from .base import Strategy, StrategyPlan, StrategyContext


class CustomStrategy(Strategy):
    def _heuristic_steps(self, ctx: StrategyContext) -> List[str]:
        steps: List[str] = []
        steps.append("根据队伍定位（主C/副C/生存/辅助）安排开场与收割顺序")
        steps.append("结合敌方弱点先破韧，再在增伤窗口爆发")
        steps.append("能量管理：保证核心角色在关键回合拥有终结技")
        steps.append("必要时通过嘲讽/控制降低翻车概率")
        return steps

    def plan(self, ctx: StrategyContext) -> StrategyPlan:
        allow_reroll = bool(ctx.preferences.get("allow_reroll", True))
        selected = (ctx.preferences.get("selected_option") or "").upper()
        options = [
            "A 稳定策略：安全优先，放弃部分极限回合",
            "B 极限策略：允许适度凹点以压缩轮数",
        ]
        desc = (
            "自定义模式的通用方案框架。请结合具体关卡机制（如地形/环境/祝福）微调。"
        )
        expected_rounds = 3
        if selected == "B" and allow_reroll:
            expected_rounds = 2
        plan = StrategyPlan(
            name="自定义 - 通用作战方案",
            description=desc,
            options=options,
            recommends=(
                "若对流程不熟或不追求最少轮数，推荐 A；想要压缩回合可选择 B"
            ),
            steps=self._heuristic_steps(ctx),
            requires_reroll=(selected == "B" and allow_reroll),
            expected_rounds=expected_rounds,
        )
        return plan
