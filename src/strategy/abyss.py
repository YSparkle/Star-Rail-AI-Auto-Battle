"""
深渊/混沌回忆等高强度环境策略
- 结合祝福/场地 Buff 制定最少轮数方案
- 强调目标选择、控场与资源（能量/韧性）管理
"""
from __future__ import annotations

from typing import Any, Dict, List
from .base import Strategy, StrategyPlan, StrategyContext
from .utils import estimate_expected_rounds


class AbyssStrategy(Strategy):
    def _heuristic_steps(self, ctx: StrategyContext) -> List[str]:
        steps: List[str] = []
        steps.append("开场判断敌方弱点与韧性条，优先破韧再进行收割")
        steps.append("根据祝福或增益选择强势回合进行爆发（如增伤窗口）")
        steps.append("控制高威胁单位的回合（冻结/禁锢/嘲讽/击破延迟）")
        steps.append("保证治疗/护盾在关键时机覆盖，避免翻车")
        steps.append("根据回合预测安排终结技与战技，减少无效溢伤")
        return steps

    def plan(self, ctx: StrategyContext) -> StrategyPlan:
        allow_reroll = bool(ctx.preferences.get("allow_reroll", True))
        selected = (ctx.preferences.get("selected_option") or "").upper()
        options = [
            "A 稳定通关：安全优先，较少依赖凹点",
            "B 最小轮数：允许适度凹点（指定角色吃击、能量铺垫、击破时点微调）",
        ]
        desc = (
            "针对深渊/混沌回忆，围绕祝福与关卡机制制定最小轮数目标。"
            "方案会明确击破顺序、控制安排、爆发窗口与能量规划。"
        )
        steps = self._heuristic_steps(ctx)

        # 深渊通常更复杂，基于刷本估计基础上加一回合作为保守估算
        expected_rounds = max(1, estimate_expected_rounds(ctx.computed) + 1)
        if selected == "B" and allow_reroll:
            expected_rounds = max(1, expected_rounds - 1)

        plan = StrategyPlan(
            name="深渊 - 最小轮数方案",
            description=desc,
            options=options,
            recommends=("若追求一次性上分、防止翻车，推荐 A；若可接受重试以换更少轮数，选 B"),
            steps=steps,
            requires_reroll=(selected == "B" and allow_reroll),
            expected_rounds=expected_rounds,
        )
        return plan
