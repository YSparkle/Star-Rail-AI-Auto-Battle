"""
星穹铁道AI自动战斗系统 - 游戏控制模块
负责模拟鼠标键盘操作（带安全开关与可配置键位）
"""

from __future__ import annotations

import time
from typing import Tuple, Dict, Optional
import logging

# Lazy import to avoid display issues
_pyautogui = None
_pynput_mouse = None
_pynput_keyboard = None

def _get_pyautogui():
    global _pyautogui
    if _pyautogui is None:
        import pyautogui
        _pyautogui = pyautogui
    return _pyautogui

def _get_pynput():
    global _pynput_mouse, _pynput_keyboard
    if _pynput_mouse is None or _pynput_keyboard is None:
        from pynput import mouse, keyboard
        _pynput_mouse = mouse
        _pynput_keyboard = keyboard
    return _pynput_mouse, _pynput_keyboard


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
        "basic_attack": "q",  # 普通攻击
        "skill": "e",  # 战技（每个角色效果不同，由AI判断）
        "ultimate_1": "1",  # 第1个角色释放大招
        "ultimate_2": "2",  # 第2个角色释放大招
        "ultimate_3": "3",  # 第3个角色释放大招
        "ultimate_4": "4",  # 第4个角色释放大招
        "target_left": "left",  # 切换目标向左
        "target_right": "right",  # 切换目标向右
        "interact": "f",
        "open_menu": "esc",
        "confirm": "enter",
        "cancel": "backspace",
    }

    def __init__(self, keybinds: Optional[Dict[str, str]] = None, enable_inputs: bool = False):
        self.logger = logging.getLogger(__name__)
        self.screen_width = None
        self.screen_height = None
        self.current_mouse_pos = (0, 0)
        self.enable_inputs = enable_inputs
        self.keybinds: Dict[str, str] = {**self.DEFAULT_BINDS, **(keybinds or {})}
    
    def _ensure_screen_size(self):
        """Lazy initialization of screen size"""
        if self.screen_width is None:
            pyautogui = _get_pyautogui()
            self.screen_width, self.screen_height = pyautogui.size()

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
        pyautogui = _get_pyautogui()
        pyautogui.moveTo(x, y, duration=duration)
        self.current_mouse_pos = (x, y)

    def click(self, button: str = "left"):
        pyautogui = _get_pyautogui()
        pyautogui.click(button=button)

    def right_click(self):
        self.click("right")

    def double_click(self):
        pyautogui = _get_pyautogui()
        pyautogui.doubleClick()

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.6):
        pyautogui = _get_pyautogui()
        pyautogui.drag(end_x - start_x, end_y - start_y, duration, button='left')

    # ---- 键盘 ----
    def press_key(self, key: str):
        if not self.enable_inputs:
            self.logger.debug(f"[输入未启用] 忽略按键: {key}")
            return
        if not self._is_key_safe(key):
            self.logger.warning(f"[安全拦截] 忽略不安全按键: {key}")
            return
        pyautogui = _get_pyautogui()
        pyautogui.press(key)

    def hold_key(self, key: str, duration: float = 0.1):
        if not self.enable_inputs or not self._is_key_safe(key):
            self.logger.debug(f"[输入未启用/不安全] 忽略长按: {key}")
            return
        pyautogui = _get_pyautogui()
        pyautogui.keyDown(key)
        time.sleep(max(0.0, duration))
        pyautogui.keyUp(key)

    def type_text(self, text: str, interval: float = 0.05):
        if not self.enable_inputs:
            self.logger.debug("[输入未启用] 忽略文本输入")
            return
        pyautogui = _get_pyautogui()
        pyautogui.write(text, interval=interval)

    # ---- 语义动作 ----
    def press_action(self, action: str, default_key: Optional[str] = None):
        key = self.keybinds.get(action, default_key)
        if not key:
            self.logger.debug(f"未找到动作映射：{action}")
            return
        self.press_key(key)

    # 游戏特定操作（基于语义动作）
    def use_basic_attack(self):
        """使用普通攻击（Q键）"""
        self.press_action("basic_attack", default_key="q")

    def use_skill(self):
        """使用战技（E键）- 每个角色的战技效果不同，由AI决策"""
        self.press_action("skill", default_key="e")

    def use_ultimate(self, character_index: int):
        """
        释放终结技：根据队伍序号 1-4 按对应数字键
        1 = 第1个角色大招
        2 = 第2个角色大招
        3 = 第3个角色大招
        4 = 第4个角色大招
        """
        if 1 <= character_index <= 4:
            self.press_action(f"ultimate_{character_index}", default_key=str(character_index))
        else:
            self.logger.warning(f"无效的角色索引：{character_index}，必须在1-4之间")

    def select_target_left(self):
        """切换目标向左（左方向键）"""
        self.press_action("target_left", default_key="left")

    def select_target_right(self):
        """切换目标向右（右方向键）"""
        self.press_action("target_right", default_key="right")

    def attack(self):
        """普通攻击的别名"""
        self.use_basic_attack()

    def open_menu(self):
        self.press_action("open_menu", default_key="esc")

    def close_dialog(self):
        self.press_action("confirm", default_key="enter")

    # ---- 截图/像素 ----
    def screenshot(self, region: Tuple[int, int, int, int] = None) -> object:
        pyautogui = _get_pyautogui()
        if region:
            return pyautogui.screenshot(region=region)
        return pyautogui.screenshot()

    def get_mouse_position(self) -> Tuple[int, int]:
        pyautogui = _get_pyautogui()
        return pyautogui.position()

    def get_pixel_color(self, x: int, y: int):
        pyautogui = _get_pyautogui()
        return pyautogui.pixel(x, y)
