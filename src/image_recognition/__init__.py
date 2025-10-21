"""
图像识别模块
Image Recognition Module
"""

from .recognizer import ImageRecognizer
from .ocr import OCR, OCRConfig, parse_basic_stats, parse_skill_text
from .ai_vision_ocr import AIVisionOCR
from .scanner import UIRegions, CharacterScanner, EnemyScanner

__all__ = [
    'ImageRecognizer',
    'OCR', 'OCRConfig', 'parse_basic_stats', 'parse_skill_text',
    'AIVisionOCR',
    'UIRegions', 'CharacterScanner', 'EnemyScanner',
]
