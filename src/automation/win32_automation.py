"""
Windows API-based automation for RDP compatibility.

This module uses win32api/win32gui to send messages directly to windows,
which works even in RDP sessions where pyautogui fails.
"""
import time
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple, List
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Try to import win32 modules (Windows only)
try:
    import win32gui
    import win32con
    import win32api
    import win32clipboard
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    logger.warning("win32 modules not available - RDP mode disabled")


# Windows API constants
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102
WM_SETFOCUS = 0x0007
WM_ACTIVATE = 0x0006
WM_MOUSEACTIVATE = 0x0021
MK_LBUTTON = 0x0001

# Virtual key codes
VK_RETURN = 0x0D
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12  # Alt key
VK_ESCAPE = 0x1B
VK_TAB = 0x09
VK_BACK = 0x08
VK_DELETE = 0x2E
VK_HOME = 0x24
VK_END = 0x23
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28


def _make_lparam(x: int, y: int) -> int:
    """Create LPARAM from x, y coordinates"""
    return (y << 16) | (x & 0xFFFF)


class Win32Window:
    """
    Wrapper for Windows window handle with automation methods.

    Uses PostMessage/SendMessage to interact with windows,
    which works in RDP sessions.
    """

    def __init__(self, hwnd: int):
        self.hwnd = hwnd

    @property
    def is_valid(self) -> bool:
        """Check if window handle is still valid"""
        if not HAS_WIN32:
            return False
        return win32gui.IsWindow(self.hwnd)

    @property
    def title(self) -> str:
        """Get window title"""
        if not HAS_WIN32:
            return ""
        try:
            return win32gui.GetWindowText(self.hwnd)
        except Exception:
            return ""

    @property
    def rect(self) -> Tuple[int, int, int, int]:
        """Get window rectangle (left, top, right, bottom)"""
        if not HAS_WIN32:
            return (0, 0, 0, 0)
        try:
            return win32gui.GetWindowRect(self.hwnd)
        except Exception:
            return (0, 0, 0, 0)

    @property
    def client_rect(self) -> Tuple[int, int, int, int]:
        """Get client area rectangle"""
        if not HAS_WIN32:
            return (0, 0, 0, 0)
        try:
            return win32gui.GetClientRect(self.hwnd)
        except Exception:
            return (0, 0, 0, 0)

    def screen_to_client(self, x: int, y: int) -> Tuple[int, int]:
        """Convert screen coordinates to client coordinates"""
        if not HAS_WIN32:
            return (x, y)
        try:
            point = win32gui.ScreenToClient(self.hwnd, (x, y))
            return point
        except Exception:
            return (x, y)

    def client_to_screen(self, x: int, y: int) -> Tuple[int, int]:
        """Convert client coordinates to screen coordinates"""
        if not HAS_WIN32:
            return (x, y)
        try:
            point = win32gui.ClientToScreen(self.hwnd, (x, y))
            return point
        except Exception:
            return (x, y)

    def activate(self) -> bool:
        """Activate (bring to foreground) the window"""
        if not HAS_WIN32:
            return False
        try:
            win32gui.SetForegroundWindow(self.hwnd)
            return True
        except Exception as e:
            logger.warning(f"Failed to activate window: {e}")
            return False

    def click(self, x: int, y: int, button: str = "left") -> bool:
        """
        Send a click to the window at client coordinates using hardware-level events.

        Uses SendInput/mouse_event instead of PostMessage because many applications
        (like KakaoTalk) ignore synthetic PostMessage-based clicks.

        Args:
            x: Client X coordinate
            y: Client Y coordinate
            button: "left" or "right"

        Returns:
            True if successful
        """
        if not HAS_WIN32:
            logger.error("win32 not available for click")
            return False

        try:
            # Convert client coordinates to screen coordinates
            screen_x, screen_y = self.client_to_screen(x, y)
            return self.click_screen(screen_x, screen_y, button)

        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False

    def click_screen(self, screen_x: int, screen_y: int, button: str = "left") -> bool:
        """
        Send a click at absolute screen coordinates using hardware-level events.

        Uses mouse_event which generates actual hardware input that applications
        cannot ignore (unlike PostMessage).

        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate
            button: "left" or "right"

        Returns:
            True if successful
        """
        if not HAS_WIN32:
            logger.error("win32 not available for click")
            return False

        try:
            # Move cursor to position
            win32api.SetCursorPos((screen_x, screen_y))
            time.sleep(0.01)

            # Send hardware-level mouse events
            if button == "left":
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, screen_x, screen_y, 0, 0)
                time.sleep(0.01)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, screen_x, screen_y, 0, 0)
            elif button == "right":
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, screen_x, screen_y, 0, 0)
                time.sleep(0.01)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, screen_x, screen_y, 0, 0)

            logger.debug(f"Click sent: screen({screen_x}, {screen_y}) button={button}")
            return True

        except Exception as e:
            logger.error(f"Click (screen) failed: {e}")
            return False

    def send_key(self, vk_code: int) -> bool:
        """
        Send a key press to the window.

        Args:
            vk_code: Virtual key code

        Returns:
            True if successful
        """
        if not HAS_WIN32:
            return False

        try:
            # Get scan code
            scan_code = win32api.MapVirtualKey(vk_code, 0)
            lparam_down = (scan_code << 16) | 1
            lparam_up = (scan_code << 16) | 1 | (1 << 30) | (1 << 31)

            win32gui.PostMessage(self.hwnd, WM_KEYDOWN, vk_code, lparam_down)
            time.sleep(0.01)
            win32gui.PostMessage(self.hwnd, WM_KEYUP, vk_code, lparam_up)

            logger.debug(f"Key sent: vk={vk_code}")
            return True

        except Exception as e:
            logger.error(f"Send key failed: {e}")
            return False

    def send_char(self, char: str) -> bool:
        """
        Send a character to the window using WM_CHAR.

        Args:
            char: Single character to send

        Returns:
            True if successful
        """
        if not HAS_WIN32:
            return False

        try:
            win32gui.PostMessage(self.hwnd, WM_CHAR, ord(char), 0)
            return True
        except Exception as e:
            logger.error(f"Send char failed: {e}")
            return False

    def send_text(self, text: str) -> bool:
        """
        Send text to the window character by character.

        Args:
            text: Text to send

        Returns:
            True if successful
        """
        if not HAS_WIN32:
            return False

        try:
            for char in text:
                win32gui.PostMessage(self.hwnd, WM_CHAR, ord(char), 0)
                time.sleep(0.005)  # Small delay between characters

            logger.debug(f"Text sent: {text[:20]}...")
            return True

        except Exception as e:
            logger.error(f"Send text failed: {e}")
            return False

    def send_hotkey(self, *keys: int) -> bool:
        """
        Send a hotkey combination (e.g., Ctrl+A, Ctrl+V).

        Args:
            keys: Virtual key codes (modifier keys first)

        Returns:
            True if successful
        """
        if not HAS_WIN32:
            return False

        try:
            # Press all keys
            for vk in keys:
                scan_code = win32api.MapVirtualKey(vk, 0)
                lparam = (scan_code << 16) | 1
                win32gui.PostMessage(self.hwnd, WM_KEYDOWN, vk, lparam)
                time.sleep(0.01)

            # Release in reverse order
            for vk in reversed(keys):
                scan_code = win32api.MapVirtualKey(vk, 0)
                lparam = (scan_code << 16) | 1 | (1 << 30) | (1 << 31)
                win32gui.PostMessage(self.hwnd, WM_KEYUP, vk, lparam)
                time.sleep(0.01)

            logger.debug(f"Hotkey sent: {keys}")
            return True

        except Exception as e:
            logger.error(f"Send hotkey failed: {e}")
            return False

    def send_ctrl_key(self, key_char: str) -> bool:
        """
        Send Ctrl+Key combination.

        Args:
            key_char: Character key (e.g., 'a', 'c', 'v')

        Returns:
            True if successful
        """
        vk_code = ord(key_char.upper())
        return self.send_hotkey(VK_CONTROL, vk_code)


class WindowFinder:
    """
    Utility to find windows by title or class name.
    """

    @staticmethod
    def find_by_title(title: str, partial: bool = True) -> Optional[Win32Window]:
        """
        Find a window by its title.

        Args:
            title: Window title to search for
            partial: If True, match partial title

        Returns:
            Win32Window or None if not found
        """
        if not HAS_WIN32:
            return None

        result = None

        def callback(hwnd, extra):
            nonlocal result
            window_title = win32gui.GetWindowText(hwnd)

            if partial:
                if title.lower() in window_title.lower():
                    result = hwnd
                    return False
            else:
                if title == window_title:
                    result = hwnd
                    return False
            return True

        try:
            win32gui.EnumWindows(callback, None)
            if result:
                return Win32Window(result)
        except Exception as e:
            logger.error(f"Window search failed: {e}")

        return None

    @staticmethod
    def find_by_class(class_name: str) -> Optional[Win32Window]:
        """
        Find a window by its class name.

        Args:
            class_name: Window class name

        Returns:
            Win32Window or None if not found
        """
        if not HAS_WIN32:
            return None

        try:
            hwnd = win32gui.FindWindow(class_name, None)
            if hwnd:
                return Win32Window(hwnd)
        except Exception as e:
            logger.error(f"Window search by class failed: {e}")

        return None

    @staticmethod
    def find_kakao_chat() -> Optional[Win32Window]:
        """
        Find KakaoTalk chat window.

        Returns:
            Win32Window or None if not found
        """
        # Try common KakaoTalk window titles
        titles = ["카카오톡", "KakaoTalk", "검키우기"]

        for title in titles:
            window = WindowFinder.find_by_title(title, partial=True)
            if window:
                logger.info(f"Found KakaoTalk window: '{window.title}'")
                return window

        logger.warning("KakaoTalk window not found")
        return None

    @staticmethod
    def list_windows() -> List[Tuple[int, str]]:
        """
        List all visible windows.

        Returns:
            List of (hwnd, title) tuples
        """
        if not HAS_WIN32:
            return []

        windows = []

        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append((hwnd, title))
            return True

        try:
            win32gui.EnumWindows(callback, None)
        except Exception as e:
            logger.error(f"List windows failed: {e}")

        return windows


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to clipboard using win32 API.

    Args:
        text: Text to copy

    Returns:
        True if successful
    """
    if not HAS_WIN32:
        logger.error("win32 not available for clipboard")
        return False

    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
        logger.debug(f"Copied to clipboard: {text[:20]}...")
        return True
    except Exception as e:
        logger.error(f"Copy to clipboard failed: {e}")
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
        return False


def paste_from_clipboard() -> str:
    """
    Get text from clipboard using win32 API.

    Returns:
        Clipboard text or empty string on error
    """
    if not HAS_WIN32:
        return ""

    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
        elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
            if isinstance(data, bytes):
                data = data.decode('utf-8', errors='ignore')
        else:
            data = ""
        win32clipboard.CloseClipboard()
        return data
    except Exception as e:
        logger.error(f"Paste from clipboard failed: {e}")
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
        return ""


def is_win32_available() -> bool:
    """Check if win32 modules are available"""
    return HAS_WIN32


# Key mappings for common keys
KEY_MAP = {
    'return': VK_RETURN,
    'enter': VK_RETURN,
    'tab': VK_TAB,
    'escape': VK_ESCAPE,
    'esc': VK_ESCAPE,
    'backspace': VK_BACK,
    'delete': VK_DELETE,
    'home': VK_HOME,
    'end': VK_END,
    'left': VK_LEFT,
    'up': VK_UP,
    'right': VK_RIGHT,
    'down': VK_DOWN,
    'ctrl': VK_CONTROL,
    'shift': VK_SHIFT,
    'alt': VK_MENU,
}


def get_vk_code(key: str) -> int:
    """
    Get virtual key code for a key name or character.

    Args:
        key: Key name (e.g., 'enter', 'ctrl') or single character

    Returns:
        Virtual key code
    """
    key_lower = key.lower()
    if key_lower in KEY_MAP:
        return KEY_MAP[key_lower]

    # Single character - get its VK code
    if len(key) == 1:
        return ord(key.upper())

    # Try to parse as function key (F1-F12)
    if key_lower.startswith('f') and key_lower[1:].isdigit():
        num = int(key_lower[1:])
        if 1 <= num <= 12:
            return 0x70 + (num - 1)  # VK_F1 = 0x70

    logger.warning(f"Unknown key: {key}")
    return 0
