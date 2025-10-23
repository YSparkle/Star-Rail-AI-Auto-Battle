"""
星穹铁道AI自动战斗系统 - 游戏控制模块
负责模拟鼠标键盘操作（带安全开关与可配置键位）
"""

from __future__ import annotations

import time
from typing import Tuple, Dict, Optional
import logging

import pyautogui
from pynput import mouse, keyboard  # 保留以便后续扩展录制/监听


class GameController:
    """游戏控制核心类
    - 提供鼠标/键盘操作
    - 支持通过 config 提供的 keybinds 自定义键位
    - 内置安全开关：未开启 enable_inputs 时不发送任何按键事件
    - 简单安全白名单：忽略包含 ctrl/alt/win/command 等组合键，避免危险操作
    """

    SAFE_KEYS = {
        # 字母
        *list("abcdefghijklmnopqrstuvwxyz"),
        # 数字
        *list("0123456789"),
        # 常用功能键
        "space", "enter", "esc", "tab", "backspace",
        "up", "down", "left", "right",
        # F1-F12
        *[f"f{i}" for i in range(1, 13)],
    }

    DEFAULT_BINDS = {
        "attack": "space",
        "single_skill": "space",  # 若单体技能是普攻，则与 attack 一致
        "aoe_skill": "e",
        "heal_skill": "q",
        "ultimate": "t",
        "interact": "f",
        "open_menu": "esc",
        "confirm": "enter",
        "cancel": "backspace",
        "switch_1": "1",
        "switch_2": "2",
        "switch_3": "3",
        "switch_4": "4",
    }

    def __init__(self, keybinds: Optional[Dict[str, str]] = None, enable_inputs: bool = False):
        self.logger = logging.getLogger(__name__)
        self.screen_width, self.screen_height = pyautogui.size()
        self.current_mouse_pos = (0, 0)
        self.enable_inputs = enable_inputs
        self.keybinds: Dict[str, str] = {**self.DEFAULT_BINDS, **(keybinds or {})}

    # ---- 设置与安全 ----
    def update_settings(self, keybinds: Optional[Dict[str, str]] = None, enable_inputs: Optional[bool] = None):
        if keybinds is not None:
            self.keybinds = {**self.DEFAULT_BINDS, **keybinds}
        if enable_inputs is not None:
            self.enable_inputs = bool(enable_inputs)
        self.logger.info(f"输入{'已启用' if self.enable_inputs else '未启用'}，键位: {self.keybinds}")

    def _is_key_safe(self, key: str) -> bool:
        if not key:
            return False
        k = key.lower().strip()
        # 拒绝包含危险组合的键
        if any(x in k for x in ["ctrl", "alt", "win", "command", "+"]):
            return False
        # 允许 SAFE_KEYS 或者单字符（如 'z'）
        return k in self.SAFE_KEYS or (len(k) == 1 and k.isprintable())

    # ---- 鼠标 ----
    def move_to(self, x: int, y: int, duration: float = 0.2):
        pyautogui.moveTo(x, y, duration=duration)
        self.current_mouse_pos = (x, y)

    def click(self, button: str = "left"):
        pyautogui.click(button=button)

    def right_click(self):
        self.click("right")

    def double_click(self):
        pyautogui.doubleClick()

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.6):
        pyautogui.drag(end_x - start_x, end_y - start_y, duration, button='left')

    # ---- 键盘 ----
    def press_key(self, key: str):
        if not self.enable_inputs:
            self.logger.debug(f"[输入未启用] 忽略按键: {key}")
            return
        if not self._is_key_safe(key):
            self.logger.warning(f"[安全拦截] 忽略不安全按键: {key}")
            return
        pyautogui.press(key)

    def hold_key(self, key: str, duration: float = 0.1):
        if not self.enable_inputs or not self._is_key_safe(key):
            self.logger.debug(f"[输入未启用/不安全] 忽略长按: {key}")
            return
        pyautogui.keyDown(key)
        time.sleep(max(0.0, duration))
        pyautogui.keyUp(key)

    def type_text(self, text: str, interval: float = 0.05):
        if not self.enable_inputs:
            self.logger.debug("[输入未启用] 忽略文本输入")
            return
        pyautogui.write(text, interval=interval)

    # ---- 语义动作 ----
    def press_action(self, action: str, default_key: Optional[str] = None):
        key = self.keybinds.get(action, default_key)
        if not key:
            self.logger.debug(f"未找到动作映射：{action}")
            return
        self.press_key(key)

    # 游戏特定操作（基于语义动作）
    def use_skill(self, skill_action: str):
        """skill_action 可为 'single_skill'/'aoe_skill'/'heal_skill'/'ultimate' 等"""
        self.press_action(skill_action, default_key=self.DEFAULT_BINDS.get(skill_action, "space"))

    def switch_character(self, character_index: int):
        if 1 <= character_index <= 4:
            self.press_action(f"switch_{character_index}", default_key=str(character_index))

    def attack(self):
        self.press_action("attack", default_key="space")

    def open_menu(self):
        self.press_action("open_menu", default_key="esc")

    def close_dialog(self):
        self.press_action("confirm", default_key="enter")

    # ---- 截图/像素 ----
    def screenshot(self, region: Tuple[int, int, int, int] = None) -> object:
        if region:
            return pyautogui.screenshot(region=region)
        return pyautogui.screenshot()

    def get_mouse_position(self) -> Tuple[int, int]:
        return pyautogui.position()

    def get_pixel_color(self, x: int, y: int):
        return pyautogui.pixel(x, y)
