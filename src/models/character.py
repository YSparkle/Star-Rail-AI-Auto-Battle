"""
角色与遗器数据结构以及基础属性计算工具
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RelicStats:
    atk_percent: float = 0.0
    atk_flat: float = 0.0
    hp_percent: float = 0.0
    hp_flat: float = 0.0
    def_percent: float = 0.0
    def_flat: float = 0.0
    crit_rate: float = 0.0
    crit_dmg: float = 0.0
    speed: float = 0.0
    break_effect: float = 0.0
    effect_hit: float = 0.0
    energy_regen: float = 0.0


@dataclass
class LightCone:
    name: str
    level: int = 80
    superimpose: int = 1
    stats: Optional[RelicStats] = None


@dataclass
class Character:
    name: str
    path: str
    element: str
    level: int = 80
    eidolon: int = 0
    base_stats: Dict[str, float] = field(default_factory=dict)
    relics: RelicStats = field(default_factory=RelicStats)
    light_cone: Optional[LightCone] = None
    skill_levels: Dict[str, int] = field(default_factory=dict)

    # 计算后的属性
    computed: Dict[str, float] = field(default_factory=dict)

    def compute(self):
        base_atk = float(self.base_stats.get("atk", 0))
        base_hp = float(self.base_stats.get("hp", 0))
        base_def = float(self.base_stats.get("def", 0))
        base_speed = float(self.base_stats.get("spd", 0))

        atk = base_atk * (1 + self.relics.atk_percent) + self.relics.atk_flat
        hp = base_hp * (1 + self.relics.hp_percent) + self.relics.hp_flat
        defense = base_def * (1 + self.relics.def_percent) + self.relics.def_flat
        speed = base_speed + self.relics.speed
        crit_rate = min(1.0, self.relics.crit_rate)
        crit_dmg = self.relics.crit_dmg
        energy_regen = self.relics.energy_regen
        break_effect = self.relics.break_effect

        # 叠加光锥属性
        if self.light_cone and self.light_cone.stats:
            s = self.light_cone.stats
            atk += base_atk * s.atk_percent + s.atk_flat
            hp += base_hp * s.hp_percent + s.hp_flat
            defense += base_def * s.def_percent + s.def_flat
            speed += s.speed
            crit_rate = min(1.0, crit_rate + s.crit_rate)
            crit_dmg += s.crit_dmg
            energy_regen += s.energy_regen
            break_effect += s.break_effect

        self.computed = {
            "atk": round(atk, 2),
            "hp": round(hp, 2),
            "def": round(defense, 2),
            "spd": round(speed, 2),
            "crit_rate": round(crit_rate, 4),
            "crit_dmg": round(crit_dmg, 4),
            "energy_regen": round(energy_regen, 4),
            "break_effect": round(break_effect, 4),
        }
        return self.computed


def character_from_config(cfg: Dict) -> Character:
    relics_cfg = cfg.get("relics", {})
    relics = RelicStats(
        atk_percent=relics_cfg.get("atk_percent", 0.0),
        atk_flat=relics_cfg.get("atk_flat", 0.0),
        hp_percent=relics_cfg.get("hp_percent", 0.0),
        hp_flat=relics_cfg.get("hp_flat", 0.0),
        def_percent=relics_cfg.get("def_percent", 0.0),
        def_flat=relics_cfg.get("def_flat", 0.0),
        crit_rate=relics_cfg.get("crit_rate", 0.0),
        crit_dmg=relics_cfg.get("crit_dmg", 0.0),
        speed=relics_cfg.get("speed", 0.0),
        break_effect=relics_cfg.get("break_effect", 0.0),
        effect_hit=relics_cfg.get("effect_hit", 0.0),
        energy_regen=relics_cfg.get("energy_regen", 0.0),
    )

    lc_cfg = cfg.get("light_cone")
    light_cone = None
    if lc_cfg:
        lc_stats_cfg = lc_cfg.get("stats") or {}
        lc_stats = RelicStats(
            atk_percent=lc_stats_cfg.get("atk_percent", 0.0),
            atk_flat=lc_stats_cfg.get("atk_flat", 0.0),
            hp_percent=lc_stats_cfg.get("hp_percent", 0.0),
            hp_flat=lc_stats_cfg.get("hp_flat", 0.0),
            def_percent=lc_stats_cfg.get("def_percent", 0.0),
            def_flat=lc_stats_cfg.get("def_flat", 0.0),
            crit_rate=lc_stats_cfg.get("crit_rate", 0.0),
            crit_dmg=lc_stats_cfg.get("crit_dmg", 0.0),
            speed=lc_stats_cfg.get("speed", 0.0),
            break_effect=lc_stats_cfg.get("break_effect", 0.0),
            effect_hit=lc_stats_cfg.get("effect_hit", 0.0),
            energy_regen=lc_stats_cfg.get("energy_regen", 0.0),
        )
        light_cone = LightCone(
            name=lc_cfg.get("name", ""),
            level=lc_cfg.get("level", 80),
            superimpose=lc_cfg.get("superimpose", 1),
            stats=lc_stats,
        )

    c = Character(
        name=cfg.get("name", "unknown"),
        path=cfg.get("path", "unknown"),
        element=cfg.get("element", "unknown"),
        level=cfg.get("level", 80),
        eidolon=cfg.get("eidolon", 0),
        base_stats=cfg.get("base_stats", {}),
        relics=relics,
        light_cone=light_cone,
        skill_levels=cfg.get("skill_levels", {}),
    )
    c.compute()
    return c
