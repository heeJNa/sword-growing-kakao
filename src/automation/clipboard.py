"""Clipboard operations for reading chat and typing Korean (Win32 API)"""
import time
from typing import Optional
from ..config.coordinates import Coordinates, DEFAULT_COORDINATES
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Import win32 automation
try:
    from .win32_automation import (
        Win32Window,
        WindowFinder,
        copy_to_clipboard,
        paste_from_clipboard,
        is_win32_available,
        VK_RETURN,
    )
    HAS_WIN32 = is_win32_available()
except ImportError:
    HAS_WIN32 = False
    logger.error("win32 모듈을 불러올 수 없습니다. pywin32를 설치하세요: pip install pywin32")

# Global window reference
_kakao_window: Optional[Win32Window] = None


class KakaoWindowNotFoundError(Exception):
    """KakaoTalk 창을 찾을 수 없을 때 발생하는 예외"""
    pass


def set_kakao_window(window: Optional[Win32Window]) -> None:
    """Set the KakaoTalk window handle"""
    global _kakao_window
    _kakao_window = window
    if window:
        logger.info(f"KakaoTalk 창 설정됨: '{window.title}'")


def get_kakao_window() -> Optional[Win32Window]:
    """Get the KakaoTalk window handle"""
    global _kakao_window
    return _kakao_window


def find_and_set_kakao_window() -> Win32Window:
    """
    Find and set KakaoTalk window automatically.

    Returns:
        Win32Window instance

    Raises:
        KakaoWindowNotFoundError: If KakaoTalk window is not found
    """
    if not HAS_WIN32:
        raise KakaoWindowNotFoundError(
            "win32 모듈을 사용할 수 없습니다. "
            "Windows에서 pywin32를 설치하세요: pip install pywin32"
        )

    window = WindowFinder.find_kakao_chat()
    if window:
        set_kakao_window(window)
        return window

    # 창을 찾지 못한 경우 열린 창 목록 로그
    windows = WindowFinder.list_windows()
    logger.error("KakaoTalk 창을 찾을 수 없습니다.")
    logger.info("현재 열린 창 목록:")
    for hwnd, title in windows[:10]:  # 상위 10개만
        logger.info(f"  - {title}")

    raise KakaoWindowNotFoundError(
        "KakaoTalk 창을 찾을 수 없습니다.\n"
        "카카오톡을 실행하고 채팅방을 열어주세요."
    )


def _ensure_window() -> Win32Window:
    """Ensure KakaoTalk window is available"""
    global _kakao_window

    if _kakao_window and _kakao_window.is_valid:
        return _kakao_window

    # Try to find window again
    return find_and_set_kakao_window()


def copy_chat_output(coords: Coordinates = None) -> str:
    """
    Copy chat output from KakaoTalk window.

    Args:
        coords: Coordinates configuration (uses default if None)

    Returns:
        Chat text from clipboard

    Raises:
        KakaoWindowNotFoundError: If KakaoTalk window is not found
    """
    if coords is None:
        coords = DEFAULT_COORDINATES

    window = _ensure_window()

    try:
        # Convert screen coordinates to client coordinates
        client_x, client_y = window.screen_to_client(
            coords.chat_output_x, coords.chat_output_y
        )

        logger.debug(f"채팅 출력 클릭: ({client_x}, {client_y})")

        # Click on chat output area
        window.click(client_x, client_y)
        time.sleep(0.1)

        # Select all (Ctrl+A)
        logger.debug("Ctrl+A (전체 선택)")
        window.send_ctrl_key('a')
        time.sleep(0.1)

        # Copy (Ctrl+C)
        logger.debug("Ctrl+C (복사)")
        window.send_ctrl_key('c')
        time.sleep(0.1)

        # Get clipboard contents
        result = paste_from_clipboard()
        logger.debug(f"클립보드 내용 길이: {len(result)}자")
        return result

    except Exception as e:
        logger.error(f"copy_chat_output 실패: {e}")
        raise


def type_to_chat(text: str, coords: Coordinates = None) -> None:
    """
    Type text into chat input using clipboard.

    Args:
        text: Text to type
        coords: Coordinates configuration (uses default if None)

    Raises:
        KakaoWindowNotFoundError: If KakaoTalk window is not found
    """
    if coords is None:
        coords = DEFAULT_COORDINATES

    window = _ensure_window()

    logger.debug(f"type_to_chat: '{text}'")

    try:
        # Save current clipboard
        old_clipboard = ""
        try:
            old_clipboard = paste_from_clipboard()
        except Exception:
            pass

        # Convert screen coordinates to client coordinates
        client_x, client_y = window.screen_to_client(
            coords.chat_input_x, coords.chat_input_y
        )

        logger.debug(f"입력창 클릭: ({client_x}, {client_y})")

        # Click on chat input area
        window.click(client_x, client_y)
        time.sleep(0.1)

        # Copy text to clipboard
        copy_to_clipboard(text)
        time.sleep(0.05)

        # Paste (Ctrl+V)
        logger.debug("Ctrl+V (붙여넣기)")
        window.send_ctrl_key('v')
        time.sleep(0.05)

        # Press Enter to send
        logger.debug("Enter 키 전송")
        window.send_key(VK_RETURN)
        time.sleep(0.1)

        # Restore clipboard
        try:
            copy_to_clipboard(old_clipboard)
        except Exception:
            pass

        logger.debug("type_to_chat 완료")

    except Exception as e:
        logger.error(f"type_to_chat 실패: {e}")
        raise


def clear_clipboard() -> None:
    """Clear clipboard contents"""
    copy_to_clipboard("")
