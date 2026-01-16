"""Single instance enforcement using lock file"""
import sys
import os
import atexit
from pathlib import Path
from typing import Optional

from .logger import get_logger

logger = get_logger(__name__)


class SingleInstance:
    """
    Ensures only one instance of the application is running.

    Uses a lock file with the process ID to detect other instances.
    """

    def __init__(self, app_name: str = "sword-macro"):
        self.app_name = app_name
        self.lock_file = Path.home() / f".{app_name}.lock"
        self._lock_acquired = False

    def is_running(self) -> bool:
        """
        Check if another instance is already running.

        Returns:
            True if another instance is running
        """
        if not self.lock_file.exists():
            return False

        try:
            pid = int(self.lock_file.read_text().strip())

            # Check if process with this PID exists
            if sys.platform == "win32":
                # Windows: use tasklist
                import subprocess
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}"],
                    capture_output=True,
                    text=True
                )
                if str(pid) in result.stdout:
                    logger.warning(f"다른 인스턴스 감지됨: PID {pid}")
                    return True
            else:
                # Unix: check /proc or use kill(0)
                try:
                    os.kill(pid, 0)
                    logger.warning(f"다른 인스턴스 감지됨: PID {pid}")
                    return True
                except OSError:
                    pass

            # Process not found, stale lock file
            logger.info("Stale lock file 발견, 삭제")
            self.lock_file.unlink()
            return False

        except (ValueError, FileNotFoundError, PermissionError) as e:
            logger.warning(f"Lock file 확인 실패: {e}")
            return False

    def acquire(self) -> bool:
        """
        Try to acquire the lock (become the single instance).

        Returns:
            True if lock acquired, False if another instance exists
        """
        if self.is_running():
            return False

        try:
            # Write our PID to lock file
            self.lock_file.write_text(str(os.getpid()))
            self._lock_acquired = True

            # Register cleanup on exit
            atexit.register(self.release)

            logger.info(f"Single instance lock 획득: PID {os.getpid()}")
            return True

        except Exception as e:
            logger.error(f"Lock 획득 실패: {e}")
            return False

    def release(self) -> None:
        """Release the lock file."""
        if self._lock_acquired and self.lock_file.exists():
            try:
                self.lock_file.unlink()
                logger.info("Single instance lock 해제")
            except Exception as e:
                logger.warning(f"Lock 해제 실패: {e}")
            self._lock_acquired = False


# Global instance
_instance: Optional[SingleInstance] = None


def ensure_single_instance(app_name: str = "sword-macro") -> bool:
    """
    Ensure only one instance of the application is running.

    Args:
        app_name: Application identifier

    Returns:
        True if this is the only instance, False if another exists
    """
    global _instance
    _instance = SingleInstance(app_name)
    return _instance.acquire()


def release_single_instance() -> None:
    """Release the single instance lock."""
    global _instance
    if _instance:
        _instance.release()
        _instance = None
