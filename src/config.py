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
    # OCR 与扫描配置（可在 UI 中编辑）
    "ocr": {
        "provider": "tesseract",
        "tesseract_path": None,
        "lang": "chi_sim+eng",
        "psm": 6,
        "oem": 3,
        "threshold": 180,
        "invert": False,
        "blur": 1
    },
    # 简易 UI 区域坐标（左、上、宽、高），用于 OCR 扫描
    "ui_regions": {
        "character_stats": [100, 100, 400, 300],
        "skill_buttons": [[300, 800], [420, 800], [540, 800], [660, 800]],
        "skill_detail_region": [600, 200, 600, 600],
        "enemy_panel": [1000, 100, 400, 300],
        "detail_button": None
    },
    # 运行模式：plan_only 为 true 时仅生成策略与保存记忆，不启动自动战斗
    "run": {
        "plan_only": False
    },
    "mode": "material_farm",  # material_farm | abyss | custom
    "preferences": {
        "allow_reroll": True,   # 是否允许凹本
        "selected_option": None, # 选择的策略："A"(稳定) 或 "B"(极限)，不填则仅给出推荐
        "reroll_settings": {
            "bait_target": None,
            "bait_condition": None,
            "max_retries": 5,
        },
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
            # ocr 子项合并
            ocr = DEFAULT_CONFIG["ocr"].copy()
            ocr.update(cfg.get("ocr", {}))
            cfg["ocr"] = ocr
            # ui_regions 子项合并
            ui_regions = DEFAULT_CONFIG["ui_regions"].copy()
            ui_regions.update(cfg.get("ui_regions", {}))
            cfg["ui_regions"] = ui_regions
            # preferences 子项也做合并，避免缺项
            pref = DEFAULT_CONFIG["preferences"].copy()
            pref.update(cfg.get("preferences", {}))
            cfg["preferences"] = pref
            # run 子项也做合并
            run = DEFAULT_CONFIG["run"].copy()
            run.update(cfg.get("run", {}))
            cfg["run"] = run
            return cfg
        except Exception as e:
            logger.error(f"读取配置失败，使用默认配置: {e}")
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()
