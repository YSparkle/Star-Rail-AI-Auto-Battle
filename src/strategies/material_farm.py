from typing import Any, Dict, List
from .base import Strategy, StrategyPlan, PlanStep
from src.stats.models import TeamStats


class MaterialFarmStrategy(Strategy):
    """
    刷材料策略：追求最少轮数和最快节奏。
    简化实现：
    - 如果队伍中存在群攻角色，则优先两轮解决；
    - 否则提供稳健三轮方案。
    """

    def generate_plans(self, team: TeamStats, context: Dict[str, Any]) -> List[StrategyPlan]:
        chars = [c.name for c in team.characters]
        has_aoe_hint = any(c.effective.get("spd", 0) >= 120 and (c.effective.get("atk", 0) > 1500 or c.effective.get("crit_rate", 0) > 0.3) for c in team.characters)

        plan_a = StrategyPlan(
            name="极速两轮",
            expected_rounds=2,
            rng_requirements="需要较高暴击或破韧",
            steps=[
                PlanStep(turn=1, actor=chars[0] if chars else "角色1", action="群体攻击", notes="提速清小怪"),
                PlanStep(turn=1, actor=chars[1] if len(chars) > 1 else "角色2", action="单体速杀", notes="集火精英"),
                PlanStep(turn=2, actor=chars[0] if chars else "角色1", action="收尾", notes="确保通关"),
            ],
        )

        plan_b = StrategyPlan(
            name="稳健三轮",
            expected_rounds=3,
            rng_requirements="无需凹",
            steps=[
                PlanStep(turn=1, actor=chars[2] if len(chars) > 2 else (chars[0] if chars else "角色1"), action="上增伤/减抗", notes="提升全队伤害"),
                PlanStep(turn=2, actor=chars[0] if chars else "角色1", action="群体或单体", notes="根据场上情况选择"),
                PlanStep(turn=3, actor=chars[1] if len(chars) > 1 else "角色2", action="收尾", notes="收尾清场"),
            ],
        )

        if has_aoe_hint:
            return [plan_a, plan_b]
        else:
            return [plan_b, plan_a]
