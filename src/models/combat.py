"""
基础战斗数值推导工具
- 基于角色与敌人配置，计算回合顺序、简单伤害期望与循环能力占位值
"""
from __future__ import annotations

from typing import Dict, List, Tuple


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
