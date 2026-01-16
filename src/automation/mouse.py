"""Mouse automation using Win32 API (RDP compatible)"""
import time
from typing import Tuple

# Import Win32 functions
try:
    import win32api
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


def get_position() -> Tuple[int, int]:
    """
    Get current mouse position.

    Returns:
        Tuple of (x, y) coordinates
    """
    if not HAS_WIN32:
        raise RuntimeError("Win32 API not available. Install pywin32: pip install pywin32")
    return win32api.GetCursorPos()


def click_at(x: int, y: int, clicks: int = 1, interval: float = 0.1) -> None:
    """
    Click at specified coordinates using Win32 API.
    Note: For clicking inside a specific window, use Win32Window.click() instead.

    Args:
        x: X coordinate (screen)
        y: Y coordinate (screen)
        clicks: Number of clicks
        interval: Interval between clicks
    """
    if not HAS_WIN32:
        raise RuntimeError("Win32 API not available. Install pywin32: pip install pywin32")

    for i in range(clicks):
        # Move cursor to position
        win32api.SetCursorPos((x, y))
        time.sleep(0.01)

        # Mouse down
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        time.sleep(0.01)

        # Mouse up
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

        if i < clicks - 1:
            time.sleep(interval)


def move_to(x: int, y: int, duration: float = 0.1) -> None:
    """
    Move mouse to specified coordinates.

    Args:
        x: X coordinate
        y: Y coordinate
        duration: Time to move (ignored, instant move)
    """
    if not HAS_WIN32:
        raise RuntimeError("Win32 API not available. Install pywin32: pip install pywin32")
    win32api.SetCursorPos((x, y))


def double_click(x: int, y: int) -> None:
    """
    Double click at specified coordinates.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    click_at(x, y, clicks=2, interval=0.05)


def right_click(x: int, y: int) -> None:
    """
    Right click at specified coordinates.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    if not HAS_WIN32:
        raise RuntimeError("Win32 API not available. Install pywin32: pip install pywin32")

    win32api.SetCursorPos((x, y))
    time.sleep(0.01)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, x, y, 0, 0)
    time.sleep(0.01)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, x, y, 0, 0)


def scroll(clicks: int, x: int = None, y: int = None) -> None:
    """
    Scroll at current or specified position.

    Args:
        clicks: Number of scroll clicks (positive=up, negative=down)
        x: Optional X coordinate
        y: Optional Y coordinate
    """
    if not HAS_WIN32:
        raise RuntimeError("Win32 API not available. Install pywin32: pip install pywin32")

    if x is not None and y is not None:
        win32api.SetCursorPos((x, y))
        time.sleep(0.01)

    # WHEEL_DELTA is 120
    win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, clicks * 120, 0)


def drag_to(x: int, y: int, duration: float = 0.5) -> None:
    """
    Drag to specified coordinates.

    Args:
        x: Target X coordinate
        y: Target Y coordinate
        duration: Time to drag (ignored, instant drag)
    """
    if not HAS_WIN32:
        raise RuntimeError("Win32 API not available. Install pywin32: pip install pywin32")

    # Get current position
    curr_x, curr_y = win32api.GetCursorPos()

    # Mouse down at current position
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, curr_x, curr_y, 0, 0)
    time.sleep(0.05)

    # Move to target
    win32api.SetCursorPos((x, y))
    time.sleep(0.05)

    # Mouse up at target
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)


def safe_click(x: int, y: int, delay_before: float = 0.05, delay_after: float = 0.05) -> None:
    """
    Click with delays for stability.

    Args:
        x: X coordinate
        y: Y coordinate
        delay_before: Delay before click
        delay_after: Delay after click
    """
    time.sleep(delay_before)
    move_to(x, y)
    time.sleep(0.05)
    click_at(x, y)
    time.sleep(delay_after)
