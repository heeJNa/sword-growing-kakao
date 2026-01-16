"""Mouse automation using pyautogui"""
import time
import pyautogui


# Configure pyautogui
pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True


def click_at(x: int, y: int, clicks: int = 1, interval: float = 0.1) -> None:
    """
    Click at specified coordinates.

    Args:
        x: X coordinate
        y: Y coordinate
        clicks: Number of clicks
        interval: Interval between clicks
    """
    pyautogui.click(x, y, clicks=clicks, interval=interval)


def move_to(x: int, y: int, duration: float = 0.1) -> None:
    """
    Move mouse to specified coordinates.

    Args:
        x: X coordinate
        y: Y coordinate
        duration: Time to move (0 for instant)
    """
    pyautogui.moveTo(x, y, duration=duration)


def double_click(x: int, y: int) -> None:
    """
    Double click at specified coordinates.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    pyautogui.doubleClick(x, y)


def right_click(x: int, y: int) -> None:
    """
    Right click at specified coordinates.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    pyautogui.rightClick(x, y)


def get_position() -> tuple:
    """
    Get current mouse position.

    Returns:
        Tuple of (x, y) coordinates
    """
    return pyautogui.position()


def scroll(clicks: int, x: int = None, y: int = None) -> None:
    """
    Scroll at current or specified position.

    Args:
        clicks: Number of scroll clicks (positive=up, negative=down)
        x: Optional X coordinate
        y: Optional Y coordinate
    """
    pyautogui.scroll(clicks, x, y)


def drag_to(x: int, y: int, duration: float = 0.5) -> None:
    """
    Drag to specified coordinates.

    Args:
        x: Target X coordinate
        y: Target Y coordinate
        duration: Time to drag
    """
    pyautogui.dragTo(x, y, duration=duration)


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
    move_to(x, y, duration=0.1)
    time.sleep(0.05)
    pyautogui.click()
    time.sleep(delay_after)
