"""Clipboard operations for reading chat and typing Korean"""
import time
import pyperclip
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button
from ..config.coordinates import Coordinates, DEFAULT_COORDINATES

# pynput controllers for direct input
_keyboard = KeyboardController()
_mouse = MouseController()


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
    _mouse.position = (coords.chat_output_x, coords.chat_output_y)
    time.sleep(0.05)
    _mouse.click(Button.left)
    time.sleep(0.1)

    # Select all (Ctrl+A)
    with _keyboard.pressed(Key.ctrl):
        _keyboard.press('a')
        _keyboard.release('a')
    time.sleep(0.1)

    # Copy (Ctrl+C)
    with _keyboard.pressed(Key.ctrl):
        _keyboard.press('c')
        _keyboard.release('c')
    time.sleep(0.1)

    # Get clipboard contents
    return pyperclip.paste()


def type_to_chat(text: str, coords: Coordinates = None) -> None:
    """
    Type text into chat input using pynput direct typing.

    Args:
        text: Text to type (supports Korean)
        coords: Coordinates configuration (uses default if None)
    """
    if coords is None:
        coords = DEFAULT_COORDINATES

    # Click on chat input area
    _mouse.position = (coords.chat_input_x, coords.chat_input_y)
    time.sleep(0.05)
    _mouse.click(Button.left)
    time.sleep(0.1)

    # Type text directly using pynput (supports Korean)
    _keyboard.type(text)
    time.sleep(0.1)

    # Press Enter to send
    _keyboard.press(Key.enter)
    _keyboard.release(Key.enter)
    time.sleep(0.1)


def clear_clipboard() -> None:
    """Clear clipboard contents"""
    pyperclip.copy("")
