"""
敌人与关卡数据结构以及基础属性/衍生指标计算
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Enemy:
    name: str = "unknown"
    level: int = 90
    weaknesses: List[str] = field(default_factory=list)
    resistances: Dict[str, float] = field(default_factory=dict)  # 元素抗性/增伤，正为抗性，负为易伤
    buffs: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    base_stats: Dict[str, float] = field(default_factory=dict)  # 例如 {"hp": 300000, "def": 800, "spd": 100, "toughness": 240}

    computed: Dict[str, float] = field(default_factory=dict)

    def compute(self) -> Dict[str, float]:
        hp = float(self.base_stats.get("hp", 0))
        defense = float(self.base_stats.get("def", 0))
        spd = float(self.base_stats.get("spd", 0))
        toughness = float(self.base_stats.get("toughness", 0))

        # 简单威胁度估算：血量/防御/速度/韧性综合（仅作为占位，后续可替换为真实公式）
        threat = hp * 0.001 + defense * 0.5 + spd * 0.3 + toughness * 0.2

        # 弱点覆盖率（用于判断破韧策略与队伍元素匹配度）
        weakness_coverage = len(self.weaknesses)

        self.computed = {
            "hp": round(hp, 2),
            "def": round(defense, 2),
            "spd": round(spd, 2),
            "toughness": round(toughness, 2),
            "threat": round(threat, 2),
            "weakness_coverage": weakness_coverage,
        }
        return self.computed


def enemy_from_config(cfg: Dict) -> Enemy:
    e = Enemy(
        name=cfg.get("name", "unknown"),
        level=cfg.get("level", 90),
        weaknesses=cfg.get("weaknesses", []) or [],
        resistances=cfg.get("resistances", {}) or {},
        buffs=cfg.get("buffs", []) or [],
        notes=cfg.get("notes"),
        base_stats=cfg.get("base_stats", {}) or {},
    )
    e.compute()
    return e
