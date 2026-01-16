"""Clipboard operations for reading chat and typing Korean"""
import sys
import time
import subprocess
import pyperclip
from pynput.mouse import Controller as MouseController, Button
from ..config.coordinates import Coordinates, DEFAULT_COORDINATES

# Platform detection
_IS_MAC = sys.platform == "darwin"

# pynput mouse controller (works fine on all platforms)
_mouse = MouseController()

# Only import pynput keyboard on non-Mac platforms
# macOS has thread safety issues with pynput keyboard in background threads
if not _IS_MAC:
    from pynput.keyboard import Controller as KeyboardController, Key
    _keyboard = KeyboardController()


def _mac_keystroke(key: str, modifier: str = None) -> None:
    """
    Send keystroke using AppleScript on macOS.
    This avoids the thread safety issues with pynput keyboard.
    """
    if modifier:
        script = f'tell application "System Events" to keystroke "{key}" using {modifier} down'
    else:
        script = f'tell application "System Events" to keystroke "{key}"'
    subprocess.run(['osascript', '-e', script], capture_output=True)


def _mac_key_code(code: int, modifier: str = None) -> None:
    """
    Send key code using AppleScript on macOS.
    Key codes: 36=Return, 51=Delete, 53=Escape
    """
    if modifier:
        script = f'tell application "System Events" to key code {code} using {modifier} down'
    else:
        script = f'tell application "System Events" to key code {code}'
    subprocess.run(['osascript', '-e', script], capture_output=True)


def _mac_type_text(text: str) -> None:
    """
    Type text using clipboard paste on macOS.
    This is more reliable for Korean text.
    """
    # Save current clipboard
    try:
        old_clipboard = pyperclip.paste()
    except Exception:
        old_clipboard = ""

    # Copy text to clipboard and paste
    pyperclip.copy(text)
    time.sleep(0.05)
    _mac_keystroke('v', 'command')
    time.sleep(0.05)

    # Restore clipboard
    try:
        time.sleep(0.1)
        pyperclip.copy(old_clipboard)
    except Exception:
        pass


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

    if _IS_MAC:
        # Use AppleScript for keyboard on macOS
        _mac_keystroke('a', 'command')  # Cmd+A
        time.sleep(0.1)
        _mac_keystroke('c', 'command')  # Cmd+C
        time.sleep(0.1)
    else:
        # Use pynput on Windows/Linux
        with _keyboard.pressed(Key.ctrl):
            _keyboard.press('a')
            _keyboard.release('a')
        time.sleep(0.1)
        with _keyboard.pressed(Key.ctrl):
            _keyboard.press('c')
            _keyboard.release('c')
        time.sleep(0.1)

    # Get clipboard contents
    return pyperclip.paste()


def type_to_chat(text: str, coords: Coordinates = None) -> None:
    """
    Type text into chat input.

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

    if _IS_MAC:
        # Use clipboard paste for Korean text on macOS
        _mac_type_text(text)
        time.sleep(0.1)
        # Press Enter (key code 36)
        _mac_key_code(36)
        time.sleep(0.1)
    else:
        # Use pynput on Windows/Linux
        _keyboard.type(text)
        time.sleep(0.1)
        _keyboard.press(Key.enter)
        _keyboard.release(Key.enter)
        time.sleep(0.1)


def clear_clipboard() -> None:
    """Clear clipboard contents"""
    pyperclip.copy("")
