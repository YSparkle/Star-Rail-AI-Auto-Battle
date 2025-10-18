from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CharacterStats:
    name: str
    path: str
    element: str
    level: int
    eidolons: int = 0
    base_stats: Dict[str, float] = field(default_factory=dict)
    light_cone_stats: Dict[str, float] = field(default_factory=dict)
    relic_stats: Dict[str, float] = field(default_factory=dict)
    trace_bonuses: Dict[str, float] = field(default_factory=dict)
    sets: List[str] = field(default_factory=list)

    # computed
    effective: Dict[str, float] = field(default_factory=dict)


@dataclass
class EnemyStats:
    name: str
    level: int
    count: int
    weakness: List[str] = field(default_factory=list)
    base_stats: Dict[str, float] = field(default_factory=dict)  # e.g., hp, def, res map
    special_buffs: List[Dict[str, float]] = field(default_factory=list)


@dataclass
class TeamStats:
    characters: List[CharacterStats]
    enemy: EnemyStats

