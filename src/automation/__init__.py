"""Automation modules for keyboard, mouse, and clipboard control (pynput/AppleScript)"""
from .keyboard import type_text, press_key, hotkey
from .mouse import click_at, move_to
from .clipboard import (
    copy_to_clipboard,
    paste_from_clipboard,
    copy_chat_output,
    type_to_chat,
    clear_clipboard,
)

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
]
