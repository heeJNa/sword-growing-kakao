"""Hotkey listener for keyboard shortcuts"""
import threading
from typing import Callable, Dict, Optional
from pynput import keyboard


class HotkeyListener:
    """
    Listener for keyboard hotkeys.

    Supports F1-F12 keys and Escape for emergency stop.
    """

    def __init__(self):
        self._callbacks: Dict[str, Callable] = {}
        self._listener: Optional[keyboard.Listener] = None
        self._running = False

    def register(self, key: str, callback: Callable) -> None:
        """
        Register a callback for a hotkey.

        Args:
            key: Key name (e.g., 'f1', 'f2', 'escape')
            callback: Function to call when key is pressed
        """
        self._callbacks[key.lower()] = callback

    def unregister(self, key: str) -> None:
        """
        Unregister a callback for a hotkey.

        Args:
            key: Key name to unregister
        """
        key = key.lower()
        if key in self._callbacks:
            del self._callbacks[key]

    def _on_press(self, key) -> None:
        """Handle key press event"""
        try:
            # Get key name
            if hasattr(key, 'name'):
                key_name = key.name.lower()
            elif hasattr(key, 'char'):
                key_name = key.char.lower() if key.char else None
            else:
                key_name = str(key).lower()

            # Check for registered callback
            if key_name and key_name in self._callbacks:
                # Run callback in separate thread to avoid blocking
                callback = self._callbacks[key_name]
                threading.Thread(target=callback, daemon=True).start()

        except Exception as e:
            print(f"Hotkey error: {e}")

    def start(self) -> None:
        """Start listening for hotkeys"""
        if self._running:
            return

        self._running = True
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.start()

    def stop(self) -> None:
        """Stop listening for hotkeys"""
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None

    def is_running(self) -> bool:
        """Check if listener is running"""
        return self._running

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


# Global hotkey listener instance
_global_listener: Optional[HotkeyListener] = None


def get_global_listener() -> HotkeyListener:
    """Get or create the global hotkey listener"""
    global _global_listener
    if _global_listener is None:
        _global_listener = HotkeyListener()
    return _global_listener


def register_hotkey(key: str, callback: Callable) -> None:
    """
    Register a global hotkey.

    Args:
        key: Key name (e.g., 'f1', 'f2', 'escape')
        callback: Function to call when key is pressed
    """
    listener = get_global_listener()
    listener.register(key, callback)


def start_listening() -> None:
    """Start the global hotkey listener"""
    listener = get_global_listener()
    listener.start()


def stop_listening() -> None:
    """Stop the global hotkey listener"""
    global _global_listener
    if _global_listener:
        _global_listener.stop()
        _global_listener = None
