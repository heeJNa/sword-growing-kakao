"""Clipboard operations for reading chat and typing Korean"""
import sys
import time
import subprocess
import pyperclip
from pynput.mouse import Controller as MouseController, Button
from ..config.coordinates import Coordinates, DEFAULT_COORDINATES
from ..utils.logger import get_logger

# Logger for this module
logger = get_logger(__name__)

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
    logger.debug(f"AppleScript 실행: keystroke '{key}' modifier={modifier}")
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
        if result.returncode != 0:
            logger.warning(f"AppleScript 실패: {result.stderr.decode()}")
    except subprocess.TimeoutExpired:
        logger.error(f"AppleScript keystroke 타임아웃: {key}")
    except Exception as e:
        logger.error(f"AppleScript 에러: {e}")


def _mac_key_code(code: int, modifier: str = None) -> None:
    """
    Send key code using AppleScript on macOS.
    Key codes: 36=Return, 51=Delete, 53=Escape
    """
    if modifier:
        script = f'tell application "System Events" to key code {code} using {modifier} down'
    else:
        script = f'tell application "System Events" to key code {code}'
    logger.debug(f"AppleScript 실행: key code {code} modifier={modifier}")
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
        if result.returncode != 0:
            logger.warning(f"AppleScript key code 실패: {result.stderr.decode()}")
    except subprocess.TimeoutExpired:
        logger.error(f"AppleScript key code 타임아웃: {code}")
    except Exception as e:
        logger.error(f"AppleScript key code 에러: {e}")


def _mac_type_text(text: str) -> None:
    """
    Type text using clipboard paste on macOS.
    This is more reliable for Korean text.
    """
    logger.debug(f"_mac_type_text() 시작: '{text}'")
    # Save current clipboard
    try:
        old_clipboard = pyperclip.paste()
    except Exception:
        old_clipboard = ""

    # Copy text to clipboard and paste
    logger.debug("클립보드에 텍스트 복사")
    pyperclip.copy(text)
    time.sleep(0.05)
    logger.debug("Cmd+V로 붙여넣기")
    _mac_keystroke('v', 'command')
    time.sleep(0.05)

    # Restore clipboard
    try:
        time.sleep(0.1)
        pyperclip.copy(old_clipboard)
    except Exception:
        pass
    logger.debug("_mac_type_text() 완료")


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
    logger.debug("copy_chat_output() 시작")
    if coords is None:
        coords = DEFAULT_COORDINATES

    # Click on chat output area
    logger.debug(f"채팅 출력 영역 클릭: ({coords.chat_output_x}, {coords.chat_output_y})")
    _mouse.position = (coords.chat_output_x, coords.chat_output_y)
    time.sleep(0.05)
    _mouse.click(Button.left)
    time.sleep(0.1)

    if _IS_MAC:
        # Use AppleScript for keyboard on macOS
        logger.debug("macOS: Cmd+A 실행")
        _mac_keystroke('a', 'command')  # Cmd+A
        time.sleep(0.1)
        logger.debug("macOS: Cmd+C 실행")
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
    logger.debug("클립보드 내용 가져오기")
    result = pyperclip.paste()
    logger.debug(f"copy_chat_output() 완료: {len(result)}자")
    return result


def type_to_chat(text: str, coords: Coordinates = None) -> None:
    """
    Type text into chat input.

    Args:
        text: Text to type (supports Korean)
        coords: Coordinates configuration (uses default if None)
    """
    logger.debug(f"type_to_chat() 시작: text='{text}'")
    if coords is None:
        coords = DEFAULT_COORDINATES

    # Click on chat input area
    logger.debug(f"채팅 입력 영역 클릭: ({coords.chat_input_x}, {coords.chat_input_y})")
    _mouse.position = (coords.chat_input_x, coords.chat_input_y)
    time.sleep(0.05)
    _mouse.click(Button.left)
    time.sleep(0.1)

    if _IS_MAC:
        # Use clipboard paste for Korean text on macOS
        logger.debug("macOS: 텍스트 붙여넣기")
        _mac_type_text(text)
        time.sleep(0.1)
        # Press Enter (key code 36)
        logger.debug("macOS: Enter 키 전송")
        _mac_key_code(36)
        time.sleep(0.1)
    else:
        # Use pynput on Windows/Linux
        _keyboard.type(text)
        time.sleep(0.1)
        _keyboard.press(Key.enter)
        _keyboard.release(Key.enter)
        time.sleep(0.1)
    logger.debug("type_to_chat() 완료")


def clear_clipboard() -> None:
    """Clear clipboard contents"""
    pyperclip.copy("")
