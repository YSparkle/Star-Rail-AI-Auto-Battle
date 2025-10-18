"""
策略帮助函数
- 提供基于当前已计算数据的粗略回合数估计
- 后续可替换为更精确的公式或学习模型
"""
from __future__ import annotations

from math import ceil
from typing import Dict


def estimate_expected_rounds(computed: Dict) -> int:
    """
    估算期望回合数（非常粗略）
    计算思路：
    - 使用队伍成员的 avg_hit 粗略估计一回合的有效输出
    - 对于刷材料场景，假设每回合每人至少打出一次有效命中（带有暴击期望折算）
    - 加入一个折损系数，考虑到溢伤、无效回合、能量与技能冷却等
    - 敌人只有一个时：rounds = ceil(enemy_hp / team_dpr)
    - 该函数仅作为占位，便于策略模块给出更贴近队伍的回合预估
    """
    if not computed:
        return 2

    enemy = computed.get("enemy", {})
    enemy_hp = float(enemy.get("hp", 0) or 0)

    team_estimates: Dict[str, Dict[str, float]] = computed.get("team_estimates", {}) or {}
    total_avg_hit = 0.0
    for est in team_estimates.values():
        total_avg_hit += float(est.get("avg_hit", 0) or 0)

    # 折损系数：考虑溢伤/非满技能倍率/目标切换等，默认 0.6
    effectiveness = 0.6

    # 简易 DPR（每回合队伍有效伤害）
    team_dpr = max(1.0, total_avg_hit * effectiveness)

    if enemy_hp <= 0:
        return 2

    rounds = ceil(enemy_hp / team_dpr)

    # 将极端值裁剪在 [1, 10] 区间以避免离谱估计影响体验
    return max(1, min(10, rounds))
