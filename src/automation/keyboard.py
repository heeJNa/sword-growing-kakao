"""Keyboard automation using pyautogui"""
import time
import pyautogui


# Configure pyautogui
pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True


def type_text(text: str, interval: float = 0.05) -> None:
    """
    Type text using keyboard.
    Note: For Korean text, use clipboard method instead.

    Args:
        text: Text to type (ASCII only)
        interval: Delay between keystrokes
    """
    pyautogui.write(text, interval=interval)


def press_key(key: str) -> None:
    """
    Press a single key.

    Args:
        key: Key to press (e.g., 'enter', 'tab', 'space')
    """
    pyautogui.press(key)


def hotkey(*keys: str) -> None:
    """
    Press a key combination.

    Args:
        keys: Keys to press together (e.g., 'ctrl', 'c')
    """
    pyautogui.hotkey(*keys)


def type_korean(text: str) -> None:
    """
    Type Korean text using clipboard method.
    This is necessary because pyautogui.write() doesn't support Korean.

    Args:
        text: Korean text to type
    """
    import pyperclip

    # Save current clipboard
    try:
        old_clipboard = pyperclip.paste()
    except Exception:
        old_clipboard = ""

    # Copy text to clipboard
    pyperclip.copy(text)
    time.sleep(0.05)

    # Paste using Ctrl+V (Windows)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.05)

    # Press Enter to send
    pyautogui.press('enter')

    # Restore clipboard (optional)
    try:
        time.sleep(0.1)
        pyperclip.copy(old_clipboard)
    except Exception:
        pass


def select_all() -> None:
    """Select all text (Ctrl+A)"""
    pyautogui.hotkey('ctrl', 'a')


def copy() -> None:
    """Copy selected text (Ctrl+C)"""
    pyautogui.hotkey('ctrl', 'c')


def paste() -> None:
    """Paste from clipboard (Ctrl+V)"""
    pyautogui.hotkey('ctrl', 'v')


def escape() -> None:
    """Press Escape key"""
    pyautogui.press('escape')
