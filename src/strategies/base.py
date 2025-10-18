from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.stats.models import TeamStats


@dataclass
class PlanStep:
    turn: int
    actor: str
    action: str
    target: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class StrategyPlan:
    name: str
    expected_rounds: int
    rng_requirements: str  # e.g., "需要1次暴击" or "无需凹"
    steps: List[PlanStep] = field(default_factory=list)


class Strategy:
    """Base class for game mode strategies."""

    def __init__(self, allow_rng_fishing: bool = True):
        self.allow_rng_fishing = allow_rng_fishing

    def generate_plans(self, team: TeamStats, context: Dict[str, Any]) -> List[StrategyPlan]:
        raise NotImplementedError
