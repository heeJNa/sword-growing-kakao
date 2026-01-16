"""Clipboard operations for reading chat and typing Korean"""
import time
import pyperclip
import pyautogui
from ..config.coordinates import Coordinates, DEFAULT_COORDINATES


def copy_to_clipboard(text: str) -> None:
    """
    Copy text to clipboard.

    Args:
        text: Text to copy
    """
    pyperclip.copy(text)


def paste_from_clipboard() -> str:
    """
    Get text from clipboard.

    Returns:
        Clipboard contents
    """
    return pyperclip.paste()


def copy_chat_output(coords: Coordinates = None) -> str:
    """
    Copy chat output from KakaoTalk window.

    This clicks on the chat output area, selects all text,
    copies it, and returns the contents.

    Args:
        coords: Coordinates configuration (uses default if None)

    Returns:
        Chat text from clipboard
    """
    if coords is None:
        coords = DEFAULT_COORDINATES

    # Click on chat output area
    pyautogui.click(coords.chat_output_x, coords.chat_output_y)
    time.sleep(0.1)

    # Select all (Ctrl+A)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)

    # Copy (Ctrl+C)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.1)

    # Get clipboard contents
    return pyperclip.paste()


def type_to_chat(text: str, coords: Coordinates = None) -> None:
    """
    Type text into chat input using clipboard.

    This is necessary for Korean text input.

    Args:
        text: Text to type
        coords: Coordinates configuration (uses default if None)
    """
    if coords is None:
        coords = DEFAULT_COORDINATES

    # Save current clipboard
    try:
        old_clipboard = pyperclip.paste()
    except Exception:
        old_clipboard = ""

    # Click on chat input area
    pyautogui.click(coords.chat_input_x, coords.chat_input_y)
    time.sleep(0.1)

    # Copy text to clipboard
    pyperclip.copy(text)
    time.sleep(0.05)

    # Paste (Ctrl+V)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.05)

    # Press Enter to send
    pyautogui.press('enter')
    time.sleep(0.1)

    # Restore clipboard
    try:
        pyperclip.copy(old_clipboard)
    except Exception:
        pass


def clear_clipboard() -> None:
    """Clear clipboard contents"""
    pyperclip.copy("")
