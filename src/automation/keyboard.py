"""Keyboard automation - cross-platform with SendInput API for Windows (Python 3.14 compatible)"""
import sys
import time
import subprocess

# Platform detection
_IS_WINDOWS = sys.platform == "win32"
_IS_MAC = sys.platform == "darwin"

# Windows: Use SendInput API via ctypes (works in RDP, Python 3.14 compatible)
# macOS: Use AppleScript
# Linux: Use pynput
if _IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    # Windows API constants
    INPUT_KEYBOARD = 1
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004
    KEYEVENTF_SCANCODE = 0x0008

    # Virtual key codes
    VK_RETURN = 0x0D
    VK_TAB = 0x09
    VK_SHIFT = 0x10
    VK_CONTROL = 0x11
    VK_MENU = 0x12  # Alt key
    VK_ESCAPE = 0x1B
    VK_SPACE = 0x20
    VK_DELETE = 0x2E
    VK_BACK = 0x08  # Backspace
    VK_UP = 0x26
    VK_DOWN = 0x28
    VK_LEFT = 0x25
    VK_RIGHT = 0x27
    VK_HOME = 0x24
    VK_END = 0x23

    # Letter keys (A-Z) are 0x41-0x5A
    # Number keys (0-9) are 0x30-0x39

    # Structures for SendInput
    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD),
        ]

    class INPUT(ctypes.Structure):
        class _INPUT_UNION(ctypes.Union):
            _fields_ = [
                ("ki", KEYBDINPUT),
                ("mi", MOUSEINPUT),
                ("hi", HARDWAREINPUT),
            ]
        _anonymous_ = ("_input",)
        _fields_ = [
            ("type", wintypes.DWORD),
            ("_input", _INPUT_UNION),
        ]

    # Load Windows API
    user32 = ctypes.windll.user32
    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT
    user32.VkKeyScanW.argtypes = [wintypes.WCHAR]
    user32.VkKeyScanW.restype = ctypes.c_short
    user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
    user32.MapVirtualKeyW.restype = wintypes.UINT

    # Windows key name to VK code mapping
    _WIN_KEY_MAP = {
        'enter': VK_RETURN,
        'return': VK_RETURN,
        'tab': VK_TAB,
        'space': VK_SPACE,
        'escape': VK_ESCAPE,
        'esc': VK_ESCAPE,
        'backspace': VK_BACK,
        'delete': VK_DELETE,
        'up': VK_UP,
        'down': VK_DOWN,
        'left': VK_LEFT,
        'right': VK_RIGHT,
        'home': VK_HOME,
        'end': VK_END,
        'ctrl': VK_CONTROL,
        'control': VK_CONTROL,
        'alt': VK_MENU,
        'shift': VK_SHIFT,
    }

    def _send_keyboard_input(vk: int, scan: int = 0, flags: int = 0) -> None:
        """Send keyboard input using Windows SendInput API."""
        extra = ctypes.c_ulong(0)
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.ki.wVk = vk
        inp.ki.wScan = scan
        inp.ki.dwFlags = flags
        inp.ki.time = 0
        inp.ki.dwExtraInfo = ctypes.pointer(extra)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def _send_unicode_char(char: str) -> None:
        """Send a single unicode character using SendInput."""
        extra = ctypes.c_ulong(0)
        # Press
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.ki.wVk = 0
        inp.ki.wScan = ord(char)
        inp.ki.dwFlags = KEYEVENTF_UNICODE
        inp.ki.time = 0
        inp.ki.dwExtraInfo = ctypes.pointer(extra)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

        # Release
        inp2 = INPUT()
        inp2.type = INPUT_KEYBOARD
        inp2.ki.wVk = 0
        inp2.ki.wScan = ord(char)
        inp2.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
        inp2.ki.time = 0
        inp2.ki.dwExtraInfo = ctypes.pointer(extra)
        user32.SendInput(1, ctypes.byref(inp2), ctypes.sizeof(INPUT))

    def _char_to_vk(char: str) -> tuple:
        """
        Convert character to virtual key code and shift state.

        Returns:
            (vk_code, needs_shift)
        """
        # Handle common special characters
        if char == '/':
            return (0xBF, False)  # VK_OEM_2 (/ ?)
        elif char == '-':
            return (0xBD, False)  # VK_OEM_MINUS
        elif char == '=':
            return (0xBB, False)  # VK_OEM_PLUS (= +)
        elif char == '[':
            return (0xDB, False)  # VK_OEM_4
        elif char == ']':
            return (0xDD, False)  # VK_OEM_6
        elif char == '\\':
            return (0xDC, False)  # VK_OEM_5
        elif char == ';':
            return (0xBA, False)  # VK_OEM_1
        elif char == "'":
            return (0xDE, False)  # VK_OEM_7
        elif char == ',':
            return (0xBC, False)  # VK_OEM_COMMA
        elif char == '.':
            return (0xBE, False)  # VK_OEM_PERIOD
        elif char == '`':
            return (0xC0, False)  # VK_OEM_3
        elif char == ' ':
            return (VK_SPACE, False)
        elif char.isalpha():
            # A-Z
            vk = ord(char.upper())
            return (vk, char.isupper())
        elif char.isdigit():
            # 0-9
            return (ord(char), False)
        else:
            # Use VkKeyScanW for other characters
            result = user32.VkKeyScanW(char)
            if result == -1:
                return (0, False)
            vk = result & 0xFF
            shift = (result >> 8) & 0x01
            return (vk, bool(shift))

    def _win_key_press(key: str) -> None:
        """Press a key down on Windows."""
        key_lower = key.lower()
        if key_lower in _WIN_KEY_MAP:
            _send_keyboard_input(_WIN_KEY_MAP[key_lower])
        elif len(key) == 1:
            vk, _ = _char_to_vk(key)
            if vk:
                _send_keyboard_input(vk)

    def _win_key_release(key: str) -> None:
        """Release a key on Windows."""
        key_lower = key.lower()
        if key_lower in _WIN_KEY_MAP:
            _send_keyboard_input(_WIN_KEY_MAP[key_lower], flags=KEYEVENTF_KEYUP)
        elif len(key) == 1:
            vk, _ = _char_to_vk(key)
            if vk:
                _send_keyboard_input(vk, flags=KEYEVENTF_KEYUP)

    def _win_key_tap(key: str) -> None:
        """Press and release a key on Windows."""
        _win_key_press(key)
        time.sleep(0.01)
        _win_key_release(key)

    def _win_type_char(char: str) -> None:
        """Type a single character on Windows using the appropriate method."""
        # For ASCII characters that can be typed with VK codes
        if char.isascii() and (char.isalnum() or char in "/-=[]\\;',. `"):
            vk, needs_shift = _char_to_vk(char)
            if vk:
                if needs_shift:
                    _send_keyboard_input(VK_SHIFT)
                    time.sleep(0.01)
                _send_keyboard_input(vk)
                time.sleep(0.01)
                _send_keyboard_input(vk, flags=KEYEVENTF_KEYUP)
                if needs_shift:
                    time.sleep(0.01)
                    _send_keyboard_input(VK_SHIFT, flags=KEYEVENTF_KEYUP)
                return

        # For Unicode characters (Korean, etc.), use Unicode input
        _send_unicode_char(char)

    def _win_type_text(text: str) -> None:
        """Type a string of text on Windows."""
        for char in text:
            _win_type_char(char)
            time.sleep(0.01)

    def _win_hotkey(*keys: str) -> None:
        """
        Press a key combination (hotkey) on Windows.

        Example: _win_hotkey('ctrl', 'a') for Ctrl+A
        """
        # Press all modifier keys first
        for key in keys[:-1]:
            _win_key_press(key)
            time.sleep(0.01)

        # Press and release the final key
        _win_key_tap(keys[-1])

        # Release modifier keys in reverse order
        for key in reversed(keys[:-1]):
            time.sleep(0.01)
            _win_key_release(key)

elif not _IS_MAC:
    # Linux: Use pynput
    from pynput.keyboard import Controller as KeyboardController, Key
    _keyboard = KeyboardController()

    # Key name mapping for Linux
    _KEY_MAP = {
        'enter': Key.enter,
        'return': Key.enter,
        'tab': Key.tab,
        'space': Key.space,
        'escape': Key.esc,
        'esc': Key.esc,
        'backspace': Key.backspace,
        'delete': Key.delete,
        'up': Key.up,
        'down': Key.down,
        'left': Key.left,
        'right': Key.right,
        'home': Key.home,
        'end': Key.end,
        'ctrl': Key.ctrl,
        'control': Key.ctrl,
        'cmd': Key.cmd,
        'alt': Key.alt,
        'shift': Key.shift,
    }

    def _get_key(key: str):
        """Get pynput Key from string (Linux only)"""
        key_lower = key.lower()
        if key_lower in _KEY_MAP:
            return _KEY_MAP[key_lower]
        if len(key) == 1:
            return key
        return key


# macOS AppleScript helpers
def _mac_keystroke(key: str, modifier: str = None) -> None:
    """
    Send keystroke using AppleScript on macOS.
    This avoids the thread safety issues with pynput keyboard.
    """
    if modifier:
        script = f'tell application "System Events" to keystroke "{key}" using {modifier} down'
    else:
        script = f'tell application "System Events" to keystroke "{key}"'
    try:
        subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
    except subprocess.TimeoutExpired:
        print(f"AppleScript keystroke timeout: {key}")


def _mac_key_code(code: int, modifier: str = None) -> None:
    """
    Send key code using AppleScript on macOS.
    Key codes: 36=Return, 48=Tab, 49=Space, 51=Delete, 53=Escape
    """
    if modifier:
        script = f'tell application "System Events" to key code {code} using {modifier} down'
    else:
        script = f'tell application "System Events" to key code {code}'
    try:
        subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
    except subprocess.TimeoutExpired:
        print(f"AppleScript key code timeout: {code}")


# macOS key code mapping
_MAC_KEY_CODES = {
    'enter': 36,
    'return': 36,
    'tab': 48,
    'space': 49,
    'backspace': 51,
    'delete': 117,
    'escape': 53,
    'esc': 53,
    'up': 126,
    'down': 125,
    'left': 123,
    'right': 124,
}


# ============================================================
# Cross-platform public interface
# ============================================================

def type_text(text: str, interval: float = 0.05) -> None:
    """
    Type text using keyboard (supports Korean).

    Args:
        text: Text to type
        interval: Delay between keystrokes (used on Windows)
    """
    if _IS_WINDOWS:
        _win_type_text(text)
    elif _IS_MAC:
        # Use AppleScript keystroke for text on macOS
        # Escape special characters for AppleScript
        escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
        script = f'tell application "System Events" to keystroke "{escaped_text}"'
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
        except subprocess.TimeoutExpired:
            print(f"AppleScript type_text timeout: {text}")
    else:
        _keyboard.type(text)


def press_key(key: str) -> None:
    """
    Press a single key.

    Args:
        key: Key to press (e.g., 'enter', 'tab', 'space')
    """
    if _IS_WINDOWS:
        _win_key_tap(key)
    elif _IS_MAC:
        key_lower = key.lower()
        if key_lower in _MAC_KEY_CODES:
            _mac_key_code(_MAC_KEY_CODES[key_lower])
        else:
            # Single character key
            _mac_keystroke(key)
    else:
        k = _get_key(key)
        _keyboard.press(k)
        _keyboard.release(k)


def key_down(key: str) -> None:
    """
    Press a key down (without releasing).

    Args:
        key: Key to press down
    """
    if _IS_WINDOWS:
        _win_key_press(key)
    elif _IS_MAC:
        # macOS doesn't have a good way to hold keys via AppleScript
        pass
    else:
        k = _get_key(key)
        _keyboard.press(k)


def key_up(key: str) -> None:
    """
    Release a key.

    Args:
        key: Key to release
    """
    if _IS_WINDOWS:
        _win_key_release(key)
    elif _IS_MAC:
        pass
    else:
        k = _get_key(key)
        _keyboard.release(k)


def hotkey(*keys: str) -> None:
    """
    Press a key combination.

    Args:
        keys: Keys to press together (e.g., 'ctrl', 'c')
    """
    if _IS_WINDOWS:
        _win_hotkey(*keys)
    elif _IS_MAC:
        # Map ctrl to command on Mac
        modifiers = []
        main_key = None

        for key in keys:
            key_lower = key.lower()
            if key_lower in ('ctrl', 'cmd', 'command', 'control'):
                modifiers.append('command')
            elif key_lower in ('alt', 'option'):
                modifiers.append('option')
            elif key_lower == 'shift':
                modifiers.append('shift')
            else:
                main_key = key

        if main_key:
            if modifiers:
                modifier_str = ' & '.join(f'{m}' for m in modifiers)
                _mac_keystroke(main_key, modifier_str)
            else:
                _mac_keystroke(main_key)
    else:
        pressed = []
        for key in keys:
            k = _get_key(key)
            _keyboard.press(k)
            pressed.append(k)
            time.sleep(0.01)

        for k in reversed(pressed):
            _keyboard.release(k)
            time.sleep(0.01)


def type_korean(text: str) -> None:
    """
    Type Korean text directly.

    Args:
        text: Korean text to type
    """
    if _IS_WINDOWS:
        _win_type_text(text)
    elif _IS_MAC:
        # Use clipboard paste for Korean on macOS
        import pyperclip
        old_clipboard = ""
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            pass

        pyperclip.copy(text)
        time.sleep(0.05)
        _mac_keystroke('v', 'command')  # Cmd+V
        time.sleep(0.05)
        _mac_key_code(36)  # Enter

        # Restore clipboard
        try:
            time.sleep(0.1)
            pyperclip.copy(old_clipboard)
        except Exception:
            pass
    else:
        _keyboard.type(text)
        time.sleep(0.05)
        press_key('enter')


def select_all() -> None:
    """Select all text (Cmd+A on Mac, Ctrl+A on Windows/Linux)"""
    hotkey('ctrl', 'a')


def copy() -> None:
    """Copy selected text (Cmd+C on Mac, Ctrl+C on Windows/Linux)"""
    hotkey('ctrl', 'c')


def paste() -> None:
    """Paste from clipboard (Cmd+V on Mac, Ctrl+V on Windows/Linux)"""
    hotkey('ctrl', 'v')


def escape() -> None:
    """Press Escape key"""
    press_key('escape')
