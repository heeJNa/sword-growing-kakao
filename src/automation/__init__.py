"""Automation modules for keyboard, mouse, and clipboard control"""
import pyautogui

# pyautogui 설정 최적화
pyautogui.PAUSE = 0.05  # 각 명령 사이 딜레이 (기본 0.1초 → 0.05초)
pyautogui.FAILSAFE = True  # 마우스를 좌상단으로 이동하면 중단 (안전장치)

from .keyboard import type_text, press_key, hotkey
from .mouse import click_at, move_to
from .clipboard import copy_to_clipboard, paste_from_clipboard, copy_chat_output

__all__ = [
    "type_text",
    "press_key",
    "hotkey",
    "click_at",
    "move_to",
    "copy_to_clipboard",
    "paste_from_clipboard",
    "copy_chat_output",
]
