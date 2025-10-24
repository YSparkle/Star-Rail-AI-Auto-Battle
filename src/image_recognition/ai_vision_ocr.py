"""
AI 视觉 OCR（多模态）
- 使用支持图像输入的对话模型（如 OpenAI 兼容 gpt-4o/mini 等）对截图进行识别与理解
- 通过 AIClient.chat_vision 将区域截图以 base64 形式发送，获取返回文本

注意：
- 需要在 config.ai 中配置支持视觉的模型与网关（openai_compatible 或 custom_http）
- 需要在 config.ocr 中设置 provider = "ai_vision"
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import base64
import cv2
import numpy as np

from src.ai import AIClient

# Lazy import to avoid display issues
_pyautogui = None

def _get_pyautogui():
    global _pyautogui
    if _pyautogui is None:
        import pyautogui
        _pyautogui = pyautogui
    return _pyautogui


DEFAULT_VISION_PROMPT = (
    "请阅读这张游戏截图中指定区域的所有可见文字，"
    "尽量按自然阅读顺序输出，保留数值、百分比、词条与段落。"
)


class AIVisionOCR:
    def __init__(self, ai: AIClient, vision_prompt: Optional[str] = None):
        self.ai = ai
        self.vision_prompt = vision_prompt or DEFAULT_VISION_PROMPT

    def _encode_png_b64(self, image: np.ndarray) -> str:
        # 避免超大图片：缩放到宽不超过 1600 保留清晰度
        h, w = image.shape[:2]
        max_w = 1600
        if w > max_w:
            scale = max_w / float(w)
            image = cv2.resize(image, (int(w * scale), int(h * scale)))
        ok, buf = cv2.imencode('.png', image)
        if not ok:
            raise RuntimeError('PNG 编码失败')
        return base64.b64encode(buf.tobytes()).decode('utf-8')

    def image_to_text(self, image: np.ndarray, prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        if not self.ai or not self.ai.is_available():
            return "[AI 未启用或未配置：无法视觉识别]"
        b64 = self._encode_png_b64(image)
        user_prompt = prompt or self.vision_prompt
        try:
            return self.ai.chat_vision([b64], user_prompt=user_prompt, max_tokens=max_tokens)
        except Exception as e:
            return f"[AI 视觉识别失败: {e}]"

    def capture_region(self, region: Tuple[int, int, int, int]) -> np.ndarray:
        pyautogui = _get_pyautogui()
        ss = pyautogui.screenshot(region=region)
        return cv2.cvtColor(np.array(ss), cv2.COLOR_RGB2BGR)

    def ocr_region(self, region: Tuple[int, int, int, int], prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        img = self.capture_region(region)
        return self.image_to_text(img, prompt=prompt, max_tokens=max_tokens)
