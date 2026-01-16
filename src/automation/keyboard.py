"""Keyboard automation using pynput (Windows/Linux) or AppleScript (macOS)"""
import sys
import time
import subprocess

# Platform detection
_IS_MAC = sys.platform == "darwin"

# Only import pynput keyboard on non-Mac platforms
# macOS has thread safety issues with pynput keyboard in background threads
if not _IS_MAC:
    from pynput.keyboard import Controller as KeyboardController, Key
    _keyboard = KeyboardController()

    # Key name mapping for Windows/Linux
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
        'cmd': Key.cmd,
        'alt': Key.alt,
        'shift': Key.shift,
    }


def _get_key(key: str):
    """Get pynput Key from string (Windows/Linux only)"""
    if _IS_MAC:
        return key
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
    subprocess.run(['osascript', '-e', script], capture_output=True)


def _mac_key_code(code: int, modifier: str = None) -> None:
    """
    Send key code using AppleScript on macOS.
    Key codes: 36=Return, 48=Tab, 49=Space, 51=Delete, 53=Escape
    """
    if modifier:
        script = f'tell application "System Events" to key code {code} using {modifier} down'
    else:
        script = f'tell application "System Events" to key code {code}'
    subprocess.run(['osascript', '-e', script], capture_output=True)


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


def type_text(text: str, interval: float = 0.05) -> None:
    """
    Type text using keyboard (supports Korean).

    Args:
        text: Text to type
        interval: Delay between keystrokes (ignored, pynput handles it)
    """
    if _IS_MAC:
        # Use AppleScript keystroke for text on macOS
        # Escape special characters for AppleScript
        escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
        script = f'tell application "System Events" to keystroke "{escaped_text}"'
        subprocess.run(['osascript', '-e', script], capture_output=True)
    else:
        _keyboard.type(text)


def press_key(key: str) -> None:
    """
    Press a single key.

    Args:
        key: Key to press (e.g., 'enter', 'tab', 'space')
    """
    if _IS_MAC:
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


def hotkey(*keys: str) -> None:
    """
    Press a key combination.

    Args:
        keys: Keys to press together (e.g., 'ctrl', 'c')
    """
    if _IS_MAC:
        # Map ctrl to command on Mac
        modifiers = []
        main_key = None

        for key in keys:
            key_lower = key.lower()
            if key_lower in ('ctrl', 'cmd', 'command'):
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
    Type Korean text directly using pynput.

    Args:
        text: Korean text to type
    """
    if _IS_MAC:
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
    """Select all text (Cmd+A on Mac, Ctrl+A on Windows)"""
    hotkey('ctrl', 'a')


def copy() -> None:
    """Copy selected text (Cmd+C on Mac, Ctrl+C on Windows)"""
    hotkey('ctrl', 'c')


def paste() -> None:
    """Paste from clipboard (Cmd+V on Mac, Ctrl+V on Windows)"""
    hotkey('ctrl', 'v')


def escape() -> None:
    """Press Escape key"""
    press_key('escape')
