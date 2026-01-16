"""Keyboard automation using Win32 API (RDP compatible)"""
import time

# Import Win32 functions
try:
    import win32api
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

# Virtual key code mappings
VK_CODES = {
    'return': win32con.VK_RETURN if HAS_WIN32 else 0x0D,
    'enter': win32con.VK_RETURN if HAS_WIN32 else 0x0D,
    'tab': win32con.VK_TAB if HAS_WIN32 else 0x09,
    'space': win32con.VK_SPACE if HAS_WIN32 else 0x20,
    'escape': win32con.VK_ESCAPE if HAS_WIN32 else 0x1B,
    'esc': win32con.VK_ESCAPE if HAS_WIN32 else 0x1B,
    'backspace': win32con.VK_BACK if HAS_WIN32 else 0x08,
    'delete': win32con.VK_DELETE if HAS_WIN32 else 0x2E,
    'up': win32con.VK_UP if HAS_WIN32 else 0x26,
    'down': win32con.VK_DOWN if HAS_WIN32 else 0x28,
    'left': win32con.VK_LEFT if HAS_WIN32 else 0x25,
    'right': win32con.VK_RIGHT if HAS_WIN32 else 0x27,
    'home': win32con.VK_HOME if HAS_WIN32 else 0x24,
    'end': win32con.VK_END if HAS_WIN32 else 0x23,
    'ctrl': win32con.VK_CONTROL if HAS_WIN32 else 0x11,
    'alt': win32con.VK_MENU if HAS_WIN32 else 0x12,
    'shift': win32con.VK_SHIFT if HAS_WIN32 else 0x10,
}


def _get_vk_code(key: str) -> int:
    """Get virtual key code for a key name"""
    key_lower = key.lower()
    if key_lower in VK_CODES:
        return VK_CODES[key_lower]
    # Single character - get VK code from character
    if len(key) == 1:
        return ord(key.upper())
    raise ValueError(f"Unknown key: {key}")


def type_text(text: str, interval: float = 0.05) -> None:
    """
    Type text using keyboard (ASCII only).
    Note: For Korean text, use clipboard method via type_to_chat() instead.

    Args:
        text: Text to type (ASCII only)
        interval: Delay between keystrokes
    """
    if not HAS_WIN32:
        raise RuntimeError("Win32 API not available. Install pywin32: pip install pywin32")

    for char in text:
        vk_code = ord(char.upper())
        need_shift = char.isupper() or char in '~!@#$%^&*()_+{}|:"<>?'

        if need_shift:
            win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
            time.sleep(0.01)

        win32api.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.01)
        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)

        if need_shift:
            time.sleep(0.01)
            win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)

        time.sleep(interval)


def press_key(key: str) -> None:
    """
    Press a single key.

    Args:
        key: Key to press (e.g., 'enter', 'tab', 'space')
    """
    if not HAS_WIN32:
        raise RuntimeError("Win32 API not available. Install pywin32: pip install pywin32")

    vk_code = _get_vk_code(key)
    win32api.keybd_event(vk_code, 0, 0, 0)
    time.sleep(0.01)
    win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)


def hotkey(*keys: str) -> None:
    """
    Press a key combination.

    Args:
        keys: Keys to press together (e.g., 'ctrl', 'c')
    """
    if not HAS_WIN32:
        raise RuntimeError("Win32 API not available. Install pywin32: pip install pywin32")

    vk_codes = [_get_vk_code(k) for k in keys]

    # Press all keys
    for vk in vk_codes:
        win32api.keybd_event(vk, 0, 0, 0)
        time.sleep(0.01)

    # Release all keys in reverse order
    for vk in reversed(vk_codes):
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.01)


def type_korean(text: str) -> None:
    """
    Type Korean text using clipboard method.
    Note: Use type_to_chat() from clipboard module for proper Korean input.

    Args:
        text: Korean text to type
    """
    from .clipboard import copy_to_clipboard, paste_from_clipboard

    # Save current clipboard
    try:
        old_clipboard = paste_from_clipboard()
    except Exception:
        old_clipboard = ""

    # Copy text to clipboard
    copy_to_clipboard(text)
    time.sleep(0.05)

    # Paste using Ctrl+V
    hotkey('ctrl', 'v')
    time.sleep(0.05)

    # Press Enter to send
    press_key('enter')

    # Restore clipboard
    try:
        time.sleep(0.1)
        copy_to_clipboard(old_clipboard)
    except Exception:
        pass


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
