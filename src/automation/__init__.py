"""Automation modules for keyboard, mouse, and clipboard control (Win32 API)"""
from .keyboard import type_text, press_key, hotkey
from .mouse import click_at, move_to
from .clipboard import (
    copy_to_clipboard,
    paste_from_clipboard,
    copy_chat_output,
    type_to_chat,
    set_kakao_window,
    get_kakao_window,
    find_and_set_kakao_window,
    clear_clipboard,
    KakaoWindowNotFoundError,
)

# Win32 automation
try:
    from .win32_automation import (
        Win32Window,
        WindowFinder,
        is_win32_available,
    )
    HAS_WIN32 = is_win32_available()
except ImportError:
    HAS_WIN32 = False
    Win32Window = None
    WindowFinder = None

    def is_win32_available():
        return False

__all__ = [
    # Keyboard
    "type_text",
    "press_key",
    "hotkey",
    # Mouse
    "click_at",
    "move_to",
    # Clipboard
    "copy_to_clipboard",
    "paste_from_clipboard",
    "copy_chat_output",
    "type_to_chat",
    "clear_clipboard",
    # Window management
    "set_kakao_window",
    "get_kakao_window",
    "find_and_set_kakao_window",
    # Exceptions
    "KakaoWindowNotFoundError",
    # Win32
    "Win32Window",
    "WindowFinder",
    "is_win32_available",
    "HAS_WIN32",
]
