"""
基础战斗数值推导工具
- 基于角色与敌人配置，计算回合顺序、简单伤害期望与循环能力占位值
"""
from __future__ import annotations

from typing import Dict, List, Tuple, Any


def compute_turn_order(characters: List[Dict[str, float]]) -> List[Tuple[str, float]]:
    """
    根据角色的速度（spd）估算首轮行动顺序。
    传入的 characters 列表中每项应包含 {"name": str, "spd": float}
    返回按速度从高到低排序的 (name, spd) 列表。
    """
    items = []
    for c in characters:
        name = c.get("name", "unknown")
        spd = float(c.get("spd", 0))
        items.append((name, spd))
    items.sort(key=lambda x: x[1], reverse=True)
    return items


def estimate_damage_profile(character: Dict[str, float]) -> Dict[str, float]:
    """
    粗略估计角色的单次伤害与爆发潜力（占位公式）。
    - avg_hit: 按暴击率与暴击伤害折算的平均一击伤害系数（与具体技能倍率相乘才得到实际伤害）。
    - burst_potential: 以攻击力与暴击系数估计的爆发潜力，用于极粗略比较。
    """
    atk = float(character.get("atk", 0))
    cr = float(character.get("crit_rate", 0))
    cd = float(character.get("crit_dmg", 0))

    avg_crit_multiplier = 1.0 + cr * cd
    avg_hit = atk * avg_crit_multiplier
    burst_potential = atk * (1.0 + cr * cd) * 2.0

    return {
        "avg_hit": round(avg_hit, 2),
        "burst_potential": round(burst_potential, 2),
    }


def summarize_team_estimates(characters: List[Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """
    为队伍每名角色生成简要的伤害估计。
    输入应包含每个角色的 computed 字段（atk/crit_rate/crit_dmg 以及 name）。
    返回 {name: {avg_hit, burst_potential}}
    """
    result: Dict[str, Dict[str, float]] = {}
    for c in characters:
        name = c.get("name", "unknown")
        est = estimate_damage_profile(c)
        result[name] = est
    return result


def analyze_team_enemy_synergy(
    roster: List[Dict[str, Any]],
    computed_chars: List[Dict[str, float]],
    enemy: Dict[str, Any],
) -> Dict[str, Any]:
    """
    计算队伍与敌人的基础“契合度/克制关系”指标，用于辅助策略规划：
    - 元素覆盖：队伍中与敌方弱点相同元素的角色数量与占比
    - 元素抗性：按队伍元素在敌方抗性表中的平均值（负值代表易伤）
    - 路径分布：队伍各命途（path）的数量，用于判断输出/生存/辅助占比
    - 速度概况：队伍平均/最高速度，辅助安排首轮行动
    """
    weaknesses = set((enemy or {}).get("weaknesses", []) or [])
    resistances = (enemy or {}).get("resistances", {}) or {}

    element_counts: Dict[str, int] = {}
    path_counts: Dict[str, int] = {}
    team_elements: List[str] = []

    for raw in roster:
        elem = raw.get("element", "unknown") or "unknown"
        path = raw.get("path", "unknown") or "unknown"
        team_elements.append(elem)
        element_counts[elem] = element_counts.get(elem, 0) + 1
        path_counts[path] = path_counts.get(path, 0) + 1

    match_names: List[str] = []
    for raw in roster:
        if (raw.get("element") or "") in weaknesses:
            match_names.append(raw.get("name", "unknown"))

    team_size = max(1, len(roster))
    weakness_match_ratio = round(len(match_names) / team_size, 3)

    # 敌方抗性：对团队元素取平均
    if team_elements:
        avg_res = 0.0
        for e in team_elements:
            avg_res += float(resistances.get(e, 0.0) or 0.0)
        avg_resistance = round(avg_res / len(team_elements), 4)
    else:
        avg_resistance = 0.0

    speeds = [float(c.get("spd", 0.0) or 0.0) for c in computed_chars]
    avg_speed = round(sum(speeds) / max(1, len(speeds)), 2) if speeds else 0.0
    max_speed = round(max(speeds), 2) if speeds else 0.0

    return {
        "element_counts": element_counts,
        "path_counts": path_counts,
        "weakness_match_names": match_names,
        "weakness_match_ratio": weakness_match_ratio,
        "avg_enemy_resistance_vs_team": avg_resistance,
        "avg_speed": avg_speed,
        "max_speed": max_speed,
    }
