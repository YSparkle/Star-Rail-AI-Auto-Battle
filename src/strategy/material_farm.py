"""
刷材料（如历战余响、历战虚影、历战训练）模式策略
目标：减少回合数、提高通关效率
"""
from __future__ import annotations

from typing import Any, Dict, List
from .base import Strategy, StrategyPlan, StrategyContext
from .utils import estimate_expected_rounds


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
        selected = (ctx.preferences.get("selected_option") or "").upper()
        options = [
            "A 稳定速刷：不开额外凹点，以可控循环为主",
            "B 极限速刷：允许凹点（例如吃特定攻击回能、追击触发等）",
        ]
        desc = (
            "目标是尽可能减少平均回合数并缩短单局时长。优先范围清场，"
            "在保证循环不断的前提下争取开场爆发与能量管理。"
        )
        steps = self._heuristic_steps(ctx)

        # 如选择极限方案且允许凹，追加玩家可配置的凹点偏好
        if selected == "B" and allow_reroll:
            rr = ctx.preferences.get("reroll_settings", {}) or {}
            bait_target = rr.get("bait_target") or "指定角色"
            bait_condition = rr.get("bait_condition") or "满足指定敌方攻击条件"
            max_retries = rr.get("max_retries", 5)
            steps.append(
                f"凹策略（可选）：诱导敌方将攻击打到 {bait_target}（条件：{bait_condition}），以铺能/触发被动；最大重试 {max_retries} 次"
            )

        # 基于队伍与敌人数据的粗略回合估计
        expected_rounds = estimate_expected_rounds(ctx.computed)
        if selected == "B" and allow_reroll:
            # 允许适度下修一回合作为“凹”带来的收益上限
            expected_rounds = max(1, expected_rounds - 1)

        plan = StrategyPlan(
            name="刷材料 - 快速周回方案",
            description=desc,
            options=options,
            recommends=("若队伍循环稳定，建议选择A，避免反复重开；追求极限时间可选B"),
            steps=steps,
            requires_reroll=(selected == "B" and allow_reroll),
            expected_rounds=expected_rounds,
        )
        return plan
