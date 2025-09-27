"""
星穹铁道AI自动战斗系统 - 游戏控制模块
负责模拟鼠标键盘操作
"""

import pyautogui
import time
from typing import Tuple, Dict
import logging
from pynput import mouse, keyboard

class GameController:
    """游戏控制核心类"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.screen_width, self.screen_height = pyautogui.size()
        self.current_mouse_pos = (0, 0)

    def move_to(self, x: int, y: int, duration: float = 0.5):
        """移动鼠标到指定位置"""
        pyautogui.moveTo(x, y, duration=duration)
        self.current_mouse_pos = (x, y)

    def click(self, button: str = "left"):
        """点击鼠标"""
        pyautogui.click(button=button)

    def right_click(self):
        """右键点击"""
        self.click("right")

    def double_click(self):
        """双击"""
        pyautogui.doubleClick()

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 1.0):
        """拖拽操作"""
        pyautogui.drag(end_x - start_x, end_y - start_y, duration, button='left')

    def press_key(self, key: str):
        """按下键盘按键"""
        pyautogui.press(key)

    def hold_key(self, key: str, duration: float = 0.1):
        """按住键盘按键"""
        pyautogui.keyDown(key)
        time.sleep(duration)
        pyautogui.keyUp(key)

    def type_text(self, text: str, interval: float = 0.1):
        """输入文本"""
        pyautogui.write(text, interval=interval)

    def screenshot(self, region: Tuple[int, int, int, int] = None) -> object:
        """截取屏幕区域"""
        if region:
            return pyautogui.screenshot(region=region)
        return pyautogui.screenshot()

    def get_mouse_position(self) -> Tuple[int, int]:
        """获取当前鼠标位置"""
        return pyautogui.position()

    def get_pixel_color(self, x: int, y: int) -> Tuple[int, int, int]:
        """获取指定位置像素颜色"""
        return pyautogui.pixel(x, y)

    # 游戏特定操作
    def use_skill(self, skill_key: str):
        """使用技能"""
        self.press_key(skill_key)

    def switch_character(self, character_index: int):
        """切换角色"""
        # 假设数字键1-4对应角色切换
        if 1 <= character_index <= 4:
            self.press_key(str(character_index))

    def attack(self):
        """普通攻击"""
        self.press_key('space')  # 假设空格键是普通攻击

    def open_menu(self):
        """打开菜单"""
        self.press_key('esc')

    def close_dialog(self):
        """关闭对话框"""
        self.press_key('enter')