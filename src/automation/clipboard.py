"""Clipboard operations for reading chat and typing Korean"""
import sys
import time
import subprocess
import pyperclip
from .mouse import click_at, move_to
from . import keyboard as kb
from ..config.coordinates import Coordinates, DEFAULT_COORDINATES
from ..utils.logger import get_logger

# Logger for this module
logger = get_logger(__name__)

# Platform detection
_IS_MAC = sys.platform == "darwin"
_IS_WINDOWS = sys.platform == "win32"


def _mac_activate_app(app_name: str = "KakaoTalk") -> bool:
    """
    Activate (bring to front) an application on macOS.
    This is CRITICAL - AppleScript keystrokes go to the frontmost app.

    Returns:
        True if activation succeeded
    """
    script = f'tell application "{app_name}" to activate'
    logger.debug(f"앱 활성화: {app_name}")
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
        if result.returncode != 0:
            logger.warning(f"앱 활성화 실패: {result.stderr.decode()}")
            return False
        # Wait for activation to complete
        time.sleep(0.3)
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"앱 활성화 타임아웃: {app_name}")
        return False
    except Exception as e:
        logger.error(f"앱 활성화 에러: {e}")
        return False


def _mac_is_app_running(app_name: str = "KakaoTalk") -> bool:
    """Check if an application is running on macOS."""
    script = f'tell application "System Events" to (name of processes) contains "{app_name}"'
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
        return result.stdout.decode().strip().lower() == "true"
    except Exception:
        return False


def _mac_select_all_and_copy() -> bool:
    """
    Select all and copy text using AppleScript on macOS.
    All commands in one script for reliable background thread operation.
    Uses keyboard shortcuts (Cmd+A, Cmd+C) instead of menu clicks for reliability.

    Returns:
        True if successful
    """
    script = '''
    tell application "KakaoTalk" to activate
    delay 0.3
    tell application "System Events"
        tell process "KakaoTalk"
            set frontmost to true
            delay 0.1
            -- Use keyboard shortcuts instead of menu clicks
            keystroke "a" using command down
            delay 0.2
            keystroke "c" using command down
            delay 0.1
        end tell
    end tell
    '''

    logger.debug("[KEYBOARD] macOS: Select All (Cmd+A) + Copy (Cmd+C) via AppleScript")

    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, timeout=10)
        if result.returncode != 0:
            logger.warning(f"Select All + Copy 실패: {result.stderr.decode()}")
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error("Select All + Copy 타임아웃")
        return False
    except Exception as e:
        logger.error(f"Select All + Copy 에러: {e}")
        return False


def _mac_paste_and_send(text: str) -> bool:
    """
    Paste text and send (Enter x2) using AppleScript on macOS.
    Copies text to clipboard first, then pastes and sends.

    Args:
        text: Text to paste and send

    Returns:
        True if successful
    """
    # Copy to clipboard first
    pyperclip.copy(text)
    time.sleep(0.1)

    script = '''
    tell application "KakaoTalk" to activate
    delay 0.2
    tell application "System Events"
        tell process "KakaoTalk"
            set frontmost to true
            delay 0.1
            click menu item "Paste" of menu "편집" of menu bar 1
            delay 0.15
            key code 36
            delay 0.1
            key code 36
        end tell
    end tell
    '''

    logger.debug(f"[KEYBOARD] macOS: Paste (Cmd+V) + Enter x2 via AppleScript: '{text}'")

    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, timeout=10)
        if result.returncode != 0:
            logger.warning(f"Paste + Send 실패: {result.stderr.decode()}")
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error("Paste + Send 타임아웃")
        return False
    except Exception as e:
        logger.error(f"Paste + Send 에러: {e}")
        return False


def _mac_key_code(code: int, modifier: str = None) -> None:
    """
    Send key code using AppleScript on macOS.

    Key codes: 36=Return, 51=Delete, 53=Escape

    Args:
        code: macOS virtual key code
        modifier: Optional modifier ('command' for Cmd key)
    """
    if modifier:
        script = f'tell application "System Events" to key code {code} using {modifier} down'
    else:
        script = f'tell application "System Events" to key code {code}'

    logger.debug(f"AppleScript key code: {code} modifier={modifier}")

    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
        if result.returncode != 0:
            logger.warning(f"AppleScript key code 실패: {result.stderr.decode()}")
    except subprocess.TimeoutExpired:
        logger.error(f"AppleScript key code 타임아웃: {code}")
    except Exception as e:
        logger.error(f"AppleScript key code 에러: {e}")


def _mac_type_and_send(text: str) -> None:
    """
    Type text and send using clipboard paste on macOS.
    Uses unified AppleScript for reliable operation from background threads.
    """
    logger.debug(f"_mac_type_and_send() 시작: '{text}'")

    # Paste text and send using the unified function
    _mac_paste_and_send(text)
    time.sleep(0.15)  # Wait for completion

    logger.debug("_mac_type_and_send() 완료")


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


def copy_chat_output(coords: Coordinates = None, y_offset: int = 0) -> str:
    """
    Copy chat output from KakaoTalk window.

    This clicks on the chat output area, selects all text,
    copies it, and returns the contents.

    Args:
        coords: Coordinates configuration (uses default if None)
        y_offset: Y coordinate offset (negative to move up, for avoiding images)

    Returns:
        Chat text from clipboard
    """
    logger.debug("copy_chat_output() 시작")
    if coords is None:
        coords = DEFAULT_COORDINATES

    if _IS_MAC:
        # macOS: Use AppleScript for keyboard operations (thread-safe)
        # Pre-flight check: Is KakaoTalk running?
        if not _mac_is_app_running("KakaoTalk"):
            logger.error("KakaoTalk이 실행되지 않음!")
            return ""

        # Click on chat output area (with y_offset)
        output_x = coords.chat_output_x
        output_y = coords.chat_output_y + y_offset
        logger.debug(f"[MOUSE] 채팅 출력 영역 클릭: ({output_x}, {output_y}) [y_offset={y_offset}]")
        click_at(output_x, output_y)
        time.sleep(0.2)

        # Use AppleScript for Select All + Copy (thread-safe)
        if not _mac_select_all_and_copy():
            logger.warning("AppleScript Select All + Copy 실패")
            return ""

        # Get clipboard contents
        result = pyperclip.paste()
        logger.debug(f"copy_chat_output() 완료: {len(result)}자")
        return result

    else:
        # Windows/Linux: Use keyboard module with SendInput API

        # Click on chat output area (with y_offset)
        output_x = coords.chat_output_x
        output_y = coords.chat_output_y + y_offset
        logger.debug(f"[MOUSE] 채팅 출력 영역 클릭: ({output_x}, {output_y}) [y_offset={y_offset}]")
        click_at(output_x, output_y)
        time.sleep(0.2)

        # Select All (Ctrl+A)
        logger.debug("[KEYBOARD] 전체 선택: Ctrl+A")
        kb.select_all()
        time.sleep(0.15)

        # Copy (Ctrl+C)
        logger.debug("[KEYBOARD] 복사: Ctrl+C")
        kb.copy()
        time.sleep(0.2)

        # Get clipboard contents
        result = pyperclip.paste()
        logger.debug(f"copy_chat_output() 완료: {len(result)}자")
        return result


def type_to_chat(text: str, coords: Coordinates = None) -> None:
    """
    Type text into chat input.

    Uses clipboard paste for Korean text support on all platforms.

    Args:
        text: Text to type (supports Korean)
        coords: Coordinates configuration (uses default if None)
    """
    logger.debug(f"type_to_chat() 시작: text='{text}'")
    if coords is None:
        coords = DEFAULT_COORDINATES

    if _IS_MAC:
        # macOS: Use AppleScript for keyboard operations (thread-safe)
        # Pre-flight check: Is KakaoTalk running?
        if not _mac_is_app_running("KakaoTalk"):
            logger.error("KakaoTalk이 실행되지 않음!")
            return

        # Click on chat input area
        logger.debug(f"[MOUSE] 채팅 입력 영역 클릭: ({coords.chat_input_x}, {coords.chat_input_y})")
        click_at(coords.chat_input_x, coords.chat_input_y)
        time.sleep(0.2)

        # Use AppleScript for paste + send (thread-safe)
        _mac_paste_and_send(text)
        logger.debug("type_to_chat() 완료")

    else:
        # Windows/Linux: Use keyboard module with SendInput API

        # Click on chat input area
        logger.debug(f"[MOUSE] 채팅 입력 영역 클릭: ({coords.chat_input_x}, {coords.chat_input_y})")
        click_at(coords.chat_input_x, coords.chat_input_y)
        time.sleep(0.2)

        # Split text: type "/" directly, paste Korean part separately
        if text.startswith("/"):
            # Type "/" directly with prefix delay
            logger.debug("[KEYBOARD] '/' 직접 입력 (슬래시 딜레이 0.3초)")
            kb.type_text("/")
            time.sleep(0.3)  # Slash delay - prevents command not being recognized

            # Paste Korean part via clipboard
            korean_part = text[1:]
            if korean_part:
                logger.debug(f"클립보드에 복사: '{korean_part}'")
                pyperclip.copy(korean_part)
                time.sleep(0.2)  # Wait for clipboard to update

                # Verify clipboard content
                clipboard_content = pyperclip.paste()
                if clipboard_content != korean_part:
                    logger.warning(f"클립보드 불일치! 예상: '{korean_part}', 실제: '{clipboard_content}'")
                    # Retry copy
                    pyperclip.copy(korean_part)
                    time.sleep(0.2)

                # Paste (Ctrl+V)
                logger.debug("[KEYBOARD] 붙여넣기: Ctrl+V")
                kb.paste()
                time.sleep(0.3)  # Wait after paste before Enter
        else:
            # No slash prefix - paste entire text
            logger.debug(f"클립보드에 복사: '{text}'")
            pyperclip.copy(text)
            time.sleep(0.1)

            # Paste (Ctrl+V)
            logger.debug("[KEYBOARD] 붙여넣기: Ctrl+V")
            kb.paste()
            time.sleep(0.3)  # Wait after paste before Enter

        # Press Enter twice - required for KakaoTalk
        logger.debug("[KEYBOARD] Enter 키 전송 (2회)")
        kb.press_key('enter')
        time.sleep(0.1)
        kb.press_key('enter')
        time.sleep(0.1)

        logger.debug("type_to_chat() 완료")


def clear_clipboard() -> None:
    """Clear clipboard contents"""
    pyperclip.copy("")
