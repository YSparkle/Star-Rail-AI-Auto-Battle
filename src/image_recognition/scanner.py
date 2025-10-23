"""
UI 扫描器
- 借助 OCR 与简单的点击序列，从游戏界面读取角色/敌人信息
- 通过配置的 UI 区域（坐标）来定位扫描位置，避免复杂的模板匹配依赖

限制：
- 需要玩家先切换到对应界面（角色详情 / 敌人详情 / 关卡信息）
- 需要用户预先在 config.json 中填写 approximate 区域坐标
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import time
import logging

from .ocr import OCR, OCRConfig, parse_basic_stats, parse_skill_text
from src.game_control.controller import GameController


@dataclass
class UIRegions:
    # 角色面板的属性区域（用于读取基础属性）
    character_stats: Tuple[int, int, int, int] = (100, 100, 400, 300)
    # 技能按钮位置列表（点击后再点击“详情”）
    skill_buttons: List[Tuple[int, int]] = None  # type: ignore
    # 技能详情弹窗的文本区域
    skill_detail_region: Tuple[int, int, int, int] = (600, 200, 600, 600)
    # 敌人信息区域
    enemy_panel: Tuple[int, int, int, int] = (1000, 100, 400, 300)
    # 详情按钮位置（技能面板打开后，用于打开详细描述）
    detail_button: Optional[Tuple[int, int]] = None


class CharacterScanner:
    def __init__(self, ocr: OCR, controller: Optional[GameController] = None, logger: Optional[logging.Logger] = None):
        self.ocr = ocr
        self.ctrl = controller or GameController()
        self.logger = logger or logging.getLogger(__name__)

    def scan_character_basic(self, ui: UIRegions) -> Dict[str, Any]:
        text = self.ocr.ocr_region(ui.character_stats)
        stats = parse_basic_stats(text)
        return {
            "raw_text": text,
            "stats": stats,
        }

    def scan_skills(self, ui: UIRegions, delay: float = 0.3) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        if not ui.skill_buttons:
            return results
        for (x, y) in ui.skill_buttons:
            # 点击技能按钮，先读取“粗略描述”，再（可选）点击“详情”读取更详细描述
            try:
                self.ctrl.move_to(x, y, duration=0.2)
                self.ctrl.click()
                time.sleep(delay)

                # 先读取粗略描述（通常为技能面板初始文本区域）
                brief_txt = self.ocr.ocr_region(ui.skill_detail_region)
                brief_parsed = parse_skill_text(brief_txt)

                detail_txt: Optional[str] = None
                detail_parsed: Optional[Dict[str, Any]] = None

                # 若提供了“详情”按钮坐标，则点击后读取更详细描述
                if ui.detail_button:
                    self.ctrl.move_to(ui.detail_button[0], ui.detail_button[1], duration=0.2)
                    self.ctrl.click()
                    time.sleep(delay)
                    detail_txt = self.ocr.ocr_region(ui.skill_detail_region)
                    detail_parsed = parse_skill_text(detail_txt)

                results.append({
                    "brief": brief_parsed,
                    "brief_raw": brief_txt,
                    "detail": detail_parsed,
                    "detail_raw": detail_txt,
                })

                # 关闭详情/面板（若有）
                self.ctrl.press_key('esc')
                time.sleep(0.2)
            except Exception as e:
                self.logger.warning(f"扫描技能失败：{e}")
        return results

    def scan_character_all(self, ui: UIRegions) -> Dict[str, Any]:
        basic = self.scan_character_basic(ui)
        skills = self.scan_skills(ui)
        return {
            "basic": basic,
            "skills": skills,
        }


class EnemyScanner:
    def __init__(self, ocr: OCR, controller: Optional[GameController] = None, logger: Optional[logging.Logger] = None):
        self.ocr = ocr
        self.ctrl = controller or GameController()
        self.logger = logger or logging.getLogger(__name__)

    def scan_enemy_panel(self, ui: UIRegions) -> Dict[str, Any]:
        text = self.ocr.ocr_region(ui.enemy_panel)
        # 敌人信息更多依赖手工/AI 解析，这里仅保留原始文本
        return {"raw_text": text}


# 将扫描结果转换为项目配置中的 roster/enemy 结构占位
# 由于从 UI 文本无法直接区分 relic/base 等，这里采用保守策略：
# - 将读到的基础数值填入 base_stats
# - 其余字段保留空白，由用户/AI 后续补充

def assemble_character_from_scan(name: str, element: str, path: str, basic_stats: Dict[str, float]) -> Dict[str, Any]:
    return {
        "name": name,
        "path": path,
        "element": element,
        "level": 80,
        "eidolon": 0,
        "base_stats": {
            "atk": basic_stats.get("atk", 0),
            "hp": basic_stats.get("hp", 0),
            "def": basic_stats.get("def", 0),
            "spd": basic_stats.get("spd", 0),
        },
        "relics": {  # 留空，由用户/AI 补全
            "atk_percent": 0.0,
            "atk_flat": 0.0,
            "hp_percent": 0.0,
            "hp_flat": 0.0,
            "def_percent": 0.0,
            "def_flat": 0.0,
            "crit_rate": basic_stats.get("crit_rate", 0.0),
            "crit_dmg": basic_stats.get("crit_dmg", 0.0),
            "speed": 0.0,
            "break_effect": basic_stats.get("break_effect", 0.0),
            "effect_hit": 0.0,
            "energy_regen": basic_stats.get("energy_regen", 0.0),
        },
        "light_cone": None,
        "skill_levels": {},
    }


def assemble_enemy_from_scan(name: str, raw_text: str) -> Dict[str, Any]:
    # 目前仅保留名称与 raw_text；弱点/抗性/基础数值可后续由 AI/用户填充
    return {
        "name": name,
        "level": 90,
        "weaknesses": [],
        "resistances": {},
        "buffs": [],
        "base_stats": {},
        "notes": raw_text,
    }
