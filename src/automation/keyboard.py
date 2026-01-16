"""Keyboard automation using pynput"""
import time
from pynput.keyboard import Controller as KeyboardController, Key

# pynput keyboard controller
_keyboard = KeyboardController()

# Key name mapping
_KEY_MAP = {
    'enter': Key.enter,
    'return': Key.enter,
    'tab': Key.tab,
    'space': Key.space,
    'escape': Key.esc,
    'esc': Key.esc,
    'backspace': Key.backspace,
    'delete': Key.delete,
    'up': Key.up,
    'down': Key.down,
    'left': Key.left,
    'right': Key.right,
    'home': Key.home,
    'end': Key.end,
    'ctrl': Key.ctrl,
    'alt': Key.alt,
    'shift': Key.shift,
}


def _get_key(key: str):
    """Get pynput Key from string"""
    key_lower = key.lower()
    if key_lower in _KEY_MAP:
        return _KEY_MAP[key_lower]
    if len(key) == 1:
        return key
    return key


def type_text(text: str, interval: float = 0.05) -> None:
    """
    Type text using keyboard (supports Korean).

    Args:
        text: Text to type
        interval: Delay between keystrokes (ignored, pynput handles it)
    """
    _keyboard.type(text)


def press_key(key: str) -> None:
    """
    Press a single key.

    Args:
        key: Key to press (e.g., 'enter', 'tab', 'space')
    """
    k = _get_key(key)
    _keyboard.press(k)
    _keyboard.release(k)


def hotkey(*keys: str) -> None:
    """
    Press a key combination.

    Args:
        keys: Keys to press together (e.g., 'ctrl', 'c')
    """
    pressed = []
    for key in keys:
        k = _get_key(key)
        _keyboard.press(k)
        pressed.append(k)
        time.sleep(0.01)

    for k in reversed(pressed):
        _keyboard.release(k)
        time.sleep(0.01)


def type_korean(text: str) -> None:
    """
    Type Korean text directly using pynput.

    Args:
        text: Korean text to type
    """
    _keyboard.type(text)
    time.sleep(0.05)
    press_key('enter')


def select_all() -> None:
    """Select all text (Ctrl+A)"""
    hotkey('ctrl', 'a')


def copy() -> None:
    """Copy selected text (Ctrl+C)"""
    hotkey('ctrl', 'c')


def paste() -> None:
    """Paste from clipboard (Ctrl+V)"""
    hotkey('ctrl', 'v')


def escape() -> None:
    """Press Escape key"""
    press_key('escape')
