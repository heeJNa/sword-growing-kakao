"""Global settings for the macro"""
from dataclasses import dataclass, field
from typing import Dict, Any
import json
from pathlib import Path


@dataclass
class Settings:
    """Application settings"""

    # Timing settings (in seconds)
    action_delay: float = 0.7  # 행동 간 딜레이
    click_delay: float = 0.1  # 클릭 딜레이
    type_delay: float = 0.05  # 타이핑 딜레이
    response_timeout: float = 5.0  # 응답 타임아웃

    # Macro timing settings (in seconds)
    profile_check_delay: float = 1.2  # 프로필 확인 대기
    result_check_delay: float = 1.2  # 결과 확인 대기
    retry_delay: float = 0.2  # 재시도 대기
    stale_result_delay: float = 0.7  # 오래된 결과 재확인 대기

    # Strategy settings
    target_level: int = 15  # Target enhancement level to reach
    sell_on_target: bool = False  # Sell when target reached (usually False)
    pause_on_target: bool = True  # Pause when target reached
    min_gold: int = 1000  # Minimum gold before selling

    # UI settings
    gui_update_interval: int = 1000  # milliseconds (reduced from 500 to lower CPU usage)
    chart_update_interval: int = 1000  # milliseconds

    # File paths
    config_dir: str = field(default_factory=lambda: str(Path.home() / ".sword-macro"))
    stats_dir: str = field(default_factory=lambda: str(Path.home() / ".sword-macro" / "stats"))

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return {
            "action_delay": self.action_delay,
            "click_delay": self.click_delay,
            "type_delay": self.type_delay,
            "response_timeout": self.response_timeout,
            "profile_check_delay": self.profile_check_delay,
            "result_check_delay": self.result_check_delay,
            "retry_delay": self.retry_delay,
            "stale_result_delay": self.stale_result_delay,
            "target_level": self.target_level,
            "sell_on_target": self.sell_on_target,
            "pause_on_target": self.pause_on_target,
            "min_gold": self.min_gold,
            "gui_update_interval": self.gui_update_interval,
            "chart_update_interval": self.chart_update_interval,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Create settings from dictionary"""
        return cls(
            action_delay=data.get("action_delay", 0.7),
            click_delay=data.get("click_delay", 0.1),
            type_delay=data.get("type_delay", 0.05),
            response_timeout=data.get("response_timeout", 5.0),
            profile_check_delay=data.get("profile_check_delay", 1.2),
            result_check_delay=data.get("result_check_delay", 1.2),
            retry_delay=data.get("retry_delay", 0.2),
            stale_result_delay=data.get("stale_result_delay", 0.7),
            target_level=data.get("target_level", 15),
            sell_on_target=data.get("sell_on_target", False),
            pause_on_target=data.get("pause_on_target", True),
            min_gold=data.get("min_gold", 1000),
            gui_update_interval=data.get("gui_update_interval", 500),
            chart_update_interval=data.get("chart_update_interval", 1000),
        )

    def save(self, path: str = None) -> None:
        """Save settings to file"""
        if path is None:
            config_path = Path(self.config_dir)
            config_path.mkdir(parents=True, exist_ok=True)
            path = str(config_path / "settings.json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str = None) -> "Settings":
        """Load settings from file"""
        if path is None:
            path = str(Path.home() / ".sword-macro" / "settings.json")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except FileNotFoundError:
            return cls()


# Global default settings instance
DEFAULT_SETTINGS = Settings()
