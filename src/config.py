"""
配置加载器
- 支持从项目根目录的 config.json 读取用户配置
- 若不存在，返回默认配置
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

CONFIG_PATH = os.path.join(os.getcwd(), "config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "ai": {
        "enabled": False,
        "provider": "openai_compatible",
        "api_key": None,
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "system_prompt": None,
        "timeout": 60,
        "endpoint": None,   # 仅 custom_http 使用
        "headers": {},      # 仅 custom_http 使用
    },
    "mode": "material_farm",  # material_farm | abyss | custom
    "preferences": {
        "allow_reroll": True,   # 是否允许凹本
        "selected_option": None # 选择的策略："A"(稳定) 或 "B"(极限)，不填则仅给出推荐
    },
    "roster": [],  # 用户的角色与装备信息
    "enemy": {},   # 敌人/关卡信息
}


logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user = json.load(f)
            # 浅合并
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(user)
            # ai 子项也做合并，避免缺项
            ai = DEFAULT_CONFIG["ai"].copy()
            ai.update(cfg.get("ai", {}))
            cfg["ai"] = ai
            # preferences 子项也做合并，避免缺项
            pref = DEFAULT_CONFIG["preferences"].copy()
            pref.update(cfg.get("preferences", {}))
            cfg["preferences"] = pref
            return cfg
        except Exception as e:
            logger.error(f"读取配置失败，使用默认配置: {e}")
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()
