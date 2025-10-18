from typing import Any, Dict, List
from .base import Strategy, StrategyPlan, PlanStep
from src.stats.models import TeamStats


class AbyssStrategy(Strategy):
    """
    深渊策略：结合BUFF，目标最少轮数且稳定。
    简化实现：
    - 若BUFF对特定元素或群攻增益明显，优先相应打法；
    - 提供“凹”与“不凹”两套方案。
    """

    def generate_plans(self, team: TeamStats, context: Dict[str, Any]) -> List[StrategyPlan]:
        buffs = context.get("abyss_buffs", [])
        chars = [c.name for c in team.characters]
        prefer_element = None
        for b in buffs:
            desc = str(b.get("desc", ""))
            if "冰" in desc:
                prefer_element = "冰"
                break
        if prefer_element is None and buffs:
            prefer_element = "泛用"

        rng_plan = StrategyPlan(
            name="最优最少轮（可凹）",
            expected_rounds=2,
            rng_requirements="可能需要指定目标承伤回能/暴击",
            steps=[
                PlanStep(turn=1, actor=chars[0] if chars else "角色1", action="卡行动顺序", notes="利用速度差与BUFF触发"),
                PlanStep(turn=1, actor=chars[1] if len(chars) > 1 else "角色2", action="针对性破韧/控制", notes=f"利用BUFF: {prefer_element or '通用'}"),
                PlanStep(turn=2, actor=chars[0] if chars else "角色1", action="爆发清场", notes="形成2轮杀"),
            ],
        )

        safe_plan = StrategyPlan(
            name="稳定少轮（不凹）",
            expected_rounds=3,
            rng_requirements="无需凹",
            steps=[
                PlanStep(turn=1, actor=chars[2] if len(chars) > 2 else (chars[0] if chars else "角色1"), action="上盾/上增伤", notes="容错"),
                PlanStep(turn=2, actor=chars[0] if chars else "角色1", action="破韧/增伤", notes="为最后收尾做准备"),
                PlanStep(turn=3, actor=chars[1] if len(chars) > 1 else "角色2", action="爆发收割", notes="稳定通关"),
            ],
        )
        return [rng_plan, safe_plan] if self.allow_rng_fishing else [safe_plan]
