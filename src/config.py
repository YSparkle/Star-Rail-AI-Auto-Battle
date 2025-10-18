import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")


def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


DEFAULT_CONFIG: Dict[str, Any] = {
    "ai": {
        "provider": "mock",  # options: mock, openai, azure, ollama, custom
        "api_key": "",
        "base_url": "",
        "model": "gpt-4o-mini",
        "system_prompt": "你是星穹铁道战斗策划AI。根据队伍与敌人信息制定最优策略。",
        "timeout_sec": 60
    },
    "mode": "material_farm",  # options: material_farm, abyss
    "allow_rng_fishing": True,
    "interactive_select": True,
    "plan_choice": None,
    "persist_memory": True,
    "team": {
        "characters": [
            # 示例：
            # {
            #     "name": "丹恒•饮月",
            #     "path": "毁灭",
            #     "element": "冰",
            #     "level": 80,
            #     "eidolons": 0,
            #     "light_cone": {"name": "某某光锥", "level": 80, "superimpose": 1, "stats": {"atk": 0, "hp": 0, "def": 0, "spd": 0, "crit_rate": 0.0, "crit_dmg": 0.0}},
            #     "base_stats": {"atk": 1000, "hp": 5000, "def": 600, "spd": 120, "crit_rate": 0.05, "crit_dmg": 0.5, "break_effect": 0.0, "energy_regen": 1.0},
            #     "relics": {
            #         "sets": ["冰套2", "攻击2"],
            #         "stats": {"atk": 500, "hp": 0, "def": 0, "spd": 12, "crit_rate": 0.2, "crit_dmg": 0.5, "break_effect": 0.0}
            #     },
            #     "traces": {"atk_pct": 0.0, "hp_pct": 0.0, "def_pct": 0.0, "crit_rate": 0.0, "crit_dmg": 0.0, "spd": 0, "break_effect": 0.0, "energy_regen": 0.0}
            # }
        ]
    },
    "enemies": {
        "name": "默认敌人",
        "level": 80,
        "count": 3,
        "weakness": ["冰", "量子"],
        "base_stats": {"hp": 20000, "def": 1000, "res": {"冰": 0.2, "量子": 0.2}},
        "special_buffs": []
    },
    "abyss": {
        "buffs": []  # 例如：[{"type": "增伤", "value": 0.2, "desc": "冻结伤害+20%"}]
    }
}


@dataclass
class AppConfig:
    raw: Dict[str, Any]
    path: str = DEFAULT_CONFIG_PATH

    @staticmethod
    def load(path: Optional[str] = None) -> "AppConfig":
        cfg_path = path or DEFAULT_CONFIG_PATH
        if not os.path.exists(cfg_path):
            AppConfig.save_default_template(cfg_path)
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # merge defaults (shallow for top-level keys)
        merged = DEFAULT_CONFIG.copy()
        for k, v in data.items():
            if isinstance(v, dict) and k in merged and isinstance(merged[k], dict):
                merged[k] = {**merged[k], **v}
            else:
                merged[k] = v
        return AppConfig(raw=merged, path=cfg_path)

    @staticmethod
    def save_default_template(path: Optional[str] = None):
        cfg_path = path or DEFAULT_CONFIG_PATH
        _ensure_dir(cfg_path)
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)

    # convenience properties
    @property
    def ai_provider(self) -> str:
        return self.raw.get("ai", {}).get("provider", "mock")

    @property
    def ai_api_key(self) -> str:
        return self.raw.get("ai", {}).get("api_key", "")

    @property
    def ai_base_url(self) -> str:
        return self.raw.get("ai", {}).get("base_url", "")

    @property
    def ai_model(self) -> str:
        return self.raw.get("ai", {}).get("model", "gpt-4o-mini")

    @property
    def system_prompt(self) -> str:
        return self.raw.get("ai", {}).get("system_prompt", DEFAULT_CONFIG["ai"]["system_prompt"]) 

    @property
    def timeout_sec(self) -> int:
        return int(self.raw.get("ai", {}).get("timeout_sec", 60))

    @property
    def mode(self) -> str:
        return str(self.raw.get("mode", "material_farm"))

    @property
    def allow_rng_fishing(self) -> bool:
        return bool(self.raw.get("allow_rng_fishing", True))

    @property
    def interactive_select(self) -> bool:
        return bool(self.raw.get("interactive_select", True))

    @property
    def plan_choice(self) -> Optional[int]:
        value = self.raw.get("plan_choice", None)
        if value is None:
            return None
        try:
            return int(value)
        except Exception:
            return None

    @property
    def team(self) -> Dict[str, Any]:
        return dict(self.raw.get("team", {}))

    @property
    def enemies(self) -> Dict[str, Any]:
        return dict(self.raw.get("enemies", {}))

    @property
    def abyss(self) -> Dict[str, Any]:
        return dict(self.raw.get("abyss", {}))

    @property
    def persist_memory(self) -> bool:
        return bool(self.raw.get("persist_memory", True))
