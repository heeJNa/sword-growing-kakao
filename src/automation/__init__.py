"""Automation modules for keyboard, mouse, and clipboard control"""
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
