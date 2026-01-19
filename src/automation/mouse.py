"""Mouse automation - cross-platform with RDP support for Windows"""
import sys
import time

# Platform detection
_IS_WINDOWS = sys.platform == "win32"
_IS_MAC = sys.platform == "darwin"

# Windows: Use SendInput API via ctypes (works in RDP)
# macOS/Linux: Use pynput
if _IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    # Windows API constants
    INPUT_MOUSE = 0
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP = 0x0040
    MOUSEEVENTF_WHEEL = 0x0800
    MOUSEEVENTF_ABSOLUTE = 0x8000
    MOUSEEVENTF_VIRTUALDESK = 0x4000

    # GetSystemMetrics constants
    SM_CXSCREEN = 0
    SM_CYSCREEN = 1
    SM_XVIRTUALSCREEN = 76
    SM_YVIRTUALSCREEN = 77
    SM_CXVIRTUALSCREEN = 78
    SM_CYVIRTUALSCREEN = 79

    # Structures for SendInput
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class INPUT(ctypes.Structure):
        class _INPUT_UNION(ctypes.Union):
            _fields_ = [("mi", MOUSEINPUT)]
        _anonymous_ = ("_input",)
        _fields_ = [
            ("type", wintypes.DWORD),
            ("_input", _INPUT_UNION),
        ]

    # Load Windows API
    user32 = ctypes.windll.user32
    user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
    user32.SetCursorPos.restype = wintypes.BOOL
    user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
    user32.GetCursorPos.restype = wintypes.BOOL
    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT
    user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    user32.GetSystemMetrics.restype = ctypes.c_int

    def _get_screen_size() -> tuple:
        """Get primary screen size."""
        width = user32.GetSystemMetrics(SM_CXSCREEN)
        height = user32.GetSystemMetrics(SM_CYSCREEN)
        return (width, height)

    def _normalize_coords(x: int, y: int) -> tuple:
        """
        Normalize screen coordinates to 0-65535 range for SendInput ABSOLUTE mode.
        This is required for MOUSEEVENTF_ABSOLUTE to work correctly.
        """
        screen_width, screen_height = _get_screen_size()
        # Formula: normalized = (coord * 65536 / screen_size) + offset for rounding
        norm_x = int((x * 65536) / screen_width)
        norm_y = int((y * 65536) / screen_height)
        return (norm_x, norm_y)

    def _send_mouse_input(flags: int, dx: int = 0, dy: int = 0, data: int = 0) -> None:
        """Send mouse input using Windows SendInput API."""
        extra = ctypes.c_ulong(0)
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.mi.dx = dx
        inp.mi.dy = dy
        inp.mi.mouseData = data
        inp.mi.dwFlags = flags
        inp.mi.time = 0
        inp.mi.dwExtraInfo = ctypes.pointer(extra)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    def _win_click(button: str = "left") -> None:
        """Perform mouse click using SendInput."""
        if button == "left":
            _send_mouse_input(MOUSEEVENTF_LEFTDOWN)
            time.sleep(0.01)
            _send_mouse_input(MOUSEEVENTF_LEFTUP)
        elif button == "right":
            _send_mouse_input(MOUSEEVENTF_RIGHTDOWN)
            time.sleep(0.01)
            _send_mouse_input(MOUSEEVENTF_RIGHTUP)
        elif button == "middle":
            _send_mouse_input(MOUSEEVENTF_MIDDLEDOWN)
            time.sleep(0.01)
            _send_mouse_input(MOUSEEVENTF_MIDDLEUP)

    def _win_move(x: int, y: int) -> None:
        """
        Move mouse cursor using SendInput with ABSOLUTE coordinates.
        This works in RDP sessions where SetCursorPos fails.
        """
        norm_x, norm_y = _normalize_coords(x, y)
        _send_mouse_input(
            MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE,
            dx=norm_x,
            dy=norm_y
        )

    def _win_get_position() -> tuple:
        """Get current mouse position."""
        point = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(point))
        return (point.x, point.y)

    def _win_scroll(clicks: int) -> None:
        """Scroll mouse wheel."""
        # WHEEL_DELTA is 120
        _send_mouse_input(MOUSEEVENTF_WHEEL, data=clicks * 120)

    def _win_press(button: str = "left") -> None:
        """Press mouse button down."""
        if button == "left":
            _send_mouse_input(MOUSEEVENTF_LEFTDOWN)
        elif button == "right":
            _send_mouse_input(MOUSEEVENTF_RIGHTDOWN)

    def _win_release(button: str = "left") -> None:
        """Release mouse button."""
        if button == "left":
            _send_mouse_input(MOUSEEVENTF_LEFTUP)
        elif button == "right":
            _send_mouse_input(MOUSEEVENTF_RIGHTUP)

else:
    # macOS/Linux: Use pynput
    from pynput.mouse import Controller as MouseController, Button
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
    if _IS_WINDOWS:
        _win_move(x, y)
        time.sleep(0.05)
        for i in range(clicks):
            _win_click("left")
            if i < clicks - 1:
                time.sleep(interval)
    else:
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
    if _IS_WINDOWS:
        _win_move(x, y)
    else:
        _mouse.position = (x, y)


def double_click(x: int, y: int) -> None:
    """
    Double click at specified coordinates.

    Args:
        x: X coordinate
        y: Y coordinate
    """
    if _IS_WINDOWS:
        _win_move(x, y)
        time.sleep(0.05)
        _win_click("left")
        time.sleep(0.05)
        _win_click("left")
    else:
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
    if _IS_WINDOWS:
        _win_move(x, y)
        time.sleep(0.05)
        _win_click("right")
    else:
        _mouse.position = (x, y)
        time.sleep(0.05)
        _mouse.click(Button.right)


def get_position() -> tuple:
    """
    Get current mouse position.

    Returns:
        Tuple of (x, y) coordinates
    """
    if _IS_WINDOWS:
        return _win_get_position()
    else:
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
        if _IS_WINDOWS:
            _win_move(x, y)
        else:
            _mouse.position = (x, y)
        time.sleep(0.05)

    if _IS_WINDOWS:
        _win_scroll(clicks)
    else:
        _mouse.scroll(0, clicks)


def drag_to(x: int, y: int, duration: float = 0.5) -> None:
    """
    Drag to specified coordinates.

    Args:
        x: Target X coordinate
        y: Target Y coordinate
        duration: Time to drag (ignored)
    """
    if _IS_WINDOWS:
        _win_press("left")
        time.sleep(0.05)
        _win_move(x, y)
        time.sleep(0.05)
        _win_release("left")
    else:
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
    if _IS_WINDOWS:
        _win_move(x, y)
        time.sleep(0.05)
        _win_click("left")
    else:
        _mouse.position = (x, y)
        time.sleep(0.05)
        _mouse.click(Button.left)
    time.sleep(delay_after)
