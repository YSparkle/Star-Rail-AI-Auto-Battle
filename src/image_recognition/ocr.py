"""
OCR 识别与文本解析工具
- 基于 pytesseract 的中文/英文混合识别
- 提供基础图像预处理（灰度/二值化/膨胀/降噪）
- 支持直接对屏幕区域进行 OCR（通过 pyautogui 截图）

注意：实际识别效果依赖于 Tesseract 的安装与语言包（建议 chi_sim + eng）。
"""
from __future__ import annotations

import io
import re
import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any

import numpy as np
import cv2

# Lazy import to avoid display issues
_pyautogui = None

def _get_pyautogui():
    global _pyautogui
    if _pyautogui is None:
        import pyautogui
        _pyautogui = pyautogui
    return _pyautogui

try:
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover - 环境可能未安装 tesseract
    pytesseract = None  # type: ignore


@dataclass
class OCRConfig:
    provider: str = "tesseract"  # 目前仅支持 tesseract
    tesseract_path: Optional[str] = None
    lang: str = "chi_sim+eng"
    psm: int = 6  # Assume a single uniform block of text.
    oem: int = 3  # Default, based on what is available.
    threshold: Optional[int] = 180  # 二值化阈值，None 表示不二值化
    invert: bool = False
    blur: int = 1  # 去噪模糊核大小，1 表示不模糊（必须为奇数）

    def apply(self):
        if self.provider == "tesseract" and self.tesseract_path:
            # 配置 tesseract 可执行文件路径
            if pytesseract:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_path


class OCR:
    def __init__(self, cfg: Optional[OCRConfig] = None):
        self.cfg = cfg or OCRConfig()
        self.cfg.apply()

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        img = image.copy()
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if self.cfg.threshold is not None:
            _, img = cv2.threshold(img, int(self.cfg.threshold), 255, cv2.THRESH_BINARY)
        if self.cfg.invert:
            img = cv2.bitwise_not(img)
        if self.cfg.blur and self.cfg.blur > 1 and self.cfg.blur % 2 == 1:
            img = cv2.GaussianBlur(img, (self.cfg.blur, self.cfg.blur), 0)
        return img

    def image_to_text(self, image: np.ndarray) -> str:
        if pytesseract is None:
            return "[pytesseract 未安装：无法识别]"
        img = self.preprocess(image)
        config = f"--psm {self.cfg.psm} --oem {self.cfg.oem}"
        try:
            text = pytesseract.image_to_string(img, lang=self.cfg.lang, config=config)
        except Exception as e:  # pragma: no cover - 依赖外部环境
            return f"[OCR 失败: {e}]"
        return text.strip()

    def capture_region(self, region: Tuple[int, int, int, int]) -> np.ndarray:
        # region: (left, top, width, height)
        pyautogui = _get_pyautogui()
        ss = pyautogui.screenshot(region=region)
        arr = cv2.cvtColor(np.array(ss), cv2.COLOR_RGB2BGR)
        return arr

    def ocr_region(self, region: Tuple[int, int, int, int]) -> str:
        img = self.capture_region(region)
        return self.image_to_text(img)


# 一些基于中文 UI 的简单数值解析，尽可能容错
# 示例："攻击 1234"、"生命 12345"、"速度 134"、"暴击率 45%"、"暴击伤害 100%"、"能量回复 10%"、"击破特攻 36%"
_CH_KV = {
    "atk": [r"攻击\s*([0-9]+)"],
    "hp": [r"生命\s*([0-9]+)"],
    "def": [r"防御\s*([0-9]+)"],
    "spd": [r"速度\s*([0-9]+)"],
    "crit_rate": [r"暴击率\s*([0-9]+)%"],
    "crit_dmg": [r"暴击伤害\s*([0-9]+)%"],
    "energy_regen": [r"能量回复\s*([0-9]+)%"],
    "break_effect": [r"击破特攻\s*([0-9]+)%"],
}


def parse_basic_stats(text: str) -> Dict[str, float]:
    txt = text.replace("\n", " ")
    result: Dict[str, float] = {}
    for key, patterns in _CH_KV.items():
        for pat in patterns:
            m = re.search(pat, txt)
            if m:
                try:
                    val = float(m.group(1))
                    if key in ("crit_rate", "crit_dmg", "energy_regen", "break_effect"):
                        val = val / 100.0
                    result[key] = val
                    break
                except Exception:
                    continue
    return result


# 技能文本解析（极简）：提取技能名与关键数值百分比（如倍率、增伤、回能）
# 实际项目可扩展为更复杂的自然语言解析。
_SKILL_NAME_PAT = re.compile(r"^([\u4e00-\u9fa5A-Za-z0-9·・\-\s]{2,})", re.M)
_PERCENT_PAT = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*%")


def parse_skill_text(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {"raw": text}
    m = _SKILL_NAME_PAT.search(text)
    if m:
        data["name"] = m.group(1).strip()
    # 抽取所有百分比，便于后续手工/AI 进一步解读
    percents = [float(x) for x in _PERCENT_PAT.findall(text)]
    if percents:
        data["percents"] = percents
    return data
