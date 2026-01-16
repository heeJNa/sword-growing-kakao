"""Mouse automation using pynput"""
import time
from pynput.mouse import Controller as MouseController, Button

# pynput mouse controller
_mouse = MouseController()


def click_at(x: int, y: int, clicks: int = 1, interval: float = 0.1) -> None:
    """
    Click at specified coordinates.

    Args:
        x: X coordinate
        y: Y coordinate
        clicks: Number of clicks
        interval: Interval between clicks
    """
    _mouse.position = (x, y)
    time.sleep(0.05)
    for i in range(clicks):
        _mouse.click(Button.left)
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
    _mouse.position = (x, y)


def double_click(x: int, y: int) -> None:
    """
    Double click at specified coordinates.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    _mouse.position = (x, y)
    time.sleep(0.05)
    _mouse.click(Button.left, 2)


def right_click(x: int, y: int) -> None:
    """
    Right click at specified coordinates.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    _mouse.position = (x, y)
    time.sleep(0.05)
    _mouse.click(Button.right)


def get_position() -> tuple:
    """
    Get current mouse position.

    Returns:
        Tuple of (x, y) coordinates
    """
    return _mouse.position


def scroll(clicks: int, x: int = None, y: int = None) -> None:
    """
    Scroll at current or specified position.

    Args:
        clicks: Number of scroll clicks (positive=up, negative=down)
        x: Optional X coordinate
        y: Optional Y coordinate
    """
    if x is not None and y is not None:
        _mouse.position = (x, y)
        time.sleep(0.05)
    _mouse.scroll(0, clicks)


def drag_to(x: int, y: int, duration: float = 0.5) -> None:
    """
    Drag to specified coordinates.

    Args:
        x: Target X coordinate
        y: Target Y coordinate
        duration: Time to drag (ignored)
    """
    _mouse.press(Button.left)
    time.sleep(0.05)
    _mouse.position = (x, y)
    time.sleep(0.05)
    _mouse.release(Button.left)


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
    _mouse.position = (x, y)
    time.sleep(0.05)
    _mouse.click(Button.left)
    time.sleep(delay_after)
