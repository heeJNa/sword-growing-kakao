"""Clipboard operations for reading chat and typing Korean"""
import time
import pyperclip
import pyautogui
from ..config.coordinates import Coordinates, DEFAULT_COORDINATES
from ..utils.logger import get_logger

logger = get_logger(__name__)


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

    logger.debug(f"copy_chat_output 시작: 좌표=({coords.chat_output_x}, {coords.chat_output_y})")

    try:
        # Click on chat output area
        logger.debug(f"클릭: ({coords.chat_output_x}, {coords.chat_output_y})")
        pyautogui.click(coords.chat_output_x, coords.chat_output_y)
        time.sleep(0.15)

        # Select all (Ctrl+A)
        logger.debug("Ctrl+A (전체 선택)")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.15)

        # Copy (Ctrl+C)
        logger.debug("Ctrl+C (복사)")
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.15)

        # Get clipboard contents
        result = pyperclip.paste()
        logger.debug(f"클립보드 내용 길이: {len(result)}자")
        return result

    except Exception as e:
        logger.error(f"copy_chat_output 에러: {type(e).__name__}: {e}")
        return ""


def type_to_chat(text: str, coords: Coordinates = None) -> bool:
    """
    Type text into chat input using clipboard.

    This is necessary for Korean text input.

    Args:
        text: Text to type
        coords: Coordinates configuration (uses default if None)

    Returns:
        True if successful, False otherwise
    """
    if coords is None:
        coords = DEFAULT_COORDINATES

    logger.debug(f"type_to_chat 시작: text='{text}', 좌표=({coords.chat_input_x}, {coords.chat_input_y})")

    # Save current clipboard
    old_clipboard = ""
    try:
        old_clipboard = pyperclip.paste()
        logger.debug(f"기존 클립보드 백업 (길이: {len(old_clipboard)})")
    except Exception as e:
        logger.warning(f"클립보드 백업 실패: {e}")

    try:
        # Click on chat input area
        logger.debug(f"입력창 클릭: ({coords.chat_input_x}, {coords.chat_input_y})")
        pyautogui.click(coords.chat_input_x, coords.chat_input_y)
        time.sleep(0.15)

        # Copy text to clipboard
        logger.debug(f"클립보드에 텍스트 복사: '{text}'")
        pyperclip.copy(text)
        time.sleep(0.1)

        # Paste (Ctrl+V)
        logger.debug("Ctrl+V (붙여넣기)")
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)

        # Press Enter to send
        logger.debug("Enter 키 전송")
        pyautogui.press('enter')
        time.sleep(0.15)

        logger.debug("type_to_chat 완료")
        return True

    except Exception as e:
        logger.error(f"type_to_chat 에러: {type(e).__name__}: {e}")
        return False

    finally:
        # Restore clipboard
        try:
            pyperclip.copy(old_clipboard)
            logger.debug("클립보드 복원 완료")
        except Exception as e:
            logger.warning(f"클립보드 복원 실패: {e}")


def clear_clipboard() -> None:
    """Clear clipboard contents"""
    pyperclip.copy("")
