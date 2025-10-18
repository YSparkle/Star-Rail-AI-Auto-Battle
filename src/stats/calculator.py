from typing import Dict, List
from .models import CharacterStats, EnemyStats, TeamStats


def _sum_stats(*dicts: Dict[str, float]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for d in dicts:
        for k, v in d.items():
            out[k] = out.get(k, 0.0) + float(v)
    return out


def compute_effective_character(raw: Dict) -> CharacterStats:
    name = raw.get("name", "Unknown")
    path = raw.get("path", "")
    element = raw.get("element", "")
    level = int(raw.get("level", 80))
    eidolons = int(raw.get("eidolons", 0))

    base_stats = raw.get("base_stats", {})
    lc = raw.get("light_cone", {})
    lc_stats = lc.get("stats", {}) if isinstance(lc, dict) else {}
    relics = raw.get("relics", {})
    relic_stats = relics.get("stats", {}) if isinstance(relics, dict) else {}
    trace_bonuses = raw.get("traces", {})

    sets = relics.get("sets", []) if isinstance(relics, dict) else []

    char = CharacterStats(
        name=name,
        path=path,
        element=element,
        level=level,
        eidolons=eidolons,
        base_stats=base_stats,
        light_cone_stats=lc_stats,
        relic_stats=relic_stats,
        trace_bonuses=trace_bonuses,
        sets=sets,
    )

    additive = _sum_stats(base_stats, lc_stats, relic_stats)
    # Apply trace bonuses (simple model: *_pct applies multiplicatively to base ATK/HP/DEF)
    eff = dict(additive)
    for key, val in trace_bonuses.items():
        if key.endswith("_pct"):
            base_key = key.replace("_pct", "")
            eff[base_key] = eff.get(base_key, 0.0) * (1.0 + float(val))
        else:
            eff[key] = eff.get(key, 0.0) + float(val)

    # Basic cap rules
    if "crit_rate" in eff:
        eff["crit_rate"] = max(0.0, min(1.0, eff["crit_rate"]))

    char.effective = eff
    return char


def compute_team(team_raw: Dict, enemy_raw: Dict) -> TeamStats:
    chars_raw = team_raw.get("characters", []) if isinstance(team_raw, dict) else []
    characters = [compute_effective_character(c) for c in chars_raw]

    enemy = EnemyStats(
        name=enemy_raw.get("name", "敌人"),
        level=int(enemy_raw.get("level", 80)),
        count=int(enemy_raw.get("count", 1)),
        weakness=enemy_raw.get("weakness", []),
        base_stats=enemy_raw.get("base_stats", {}),
        special_buffs=enemy_raw.get("special_buffs", []),
    )
    return TeamStats(characters=characters, enemy=enemy)
