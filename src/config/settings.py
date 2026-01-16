"""Global settings for the macro"""
from dataclasses import dataclass, field
from typing import Dict, Any
import json
from pathlib import Path


@dataclass
class Settings:
    """Application settings"""

    # Timing settings (in seconds)
    action_delay: float = 1.0
    click_delay: float = 0.1
    type_delay: float = 0.05
    response_timeout: float = 5.0

    # Strategy settings
    level_threshold: int = 11
    max_fails: int = 2
    min_gold: int = 10000
    max_level: int = 20

    # Auto mode settings
    auto_sell_on_threshold: bool = True
    auto_sell_on_max_fails: bool = True

    # UI settings
    gui_update_interval: int = 500  # milliseconds
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
            "level_threshold": self.level_threshold,
            "max_fails": self.max_fails,
            "min_gold": self.min_gold,
            "max_level": self.max_level,
            "auto_sell_on_threshold": self.auto_sell_on_threshold,
            "auto_sell_on_max_fails": self.auto_sell_on_max_fails,
            "gui_update_interval": self.gui_update_interval,
            "chart_update_interval": self.chart_update_interval,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Create settings from dictionary"""
        return cls(
            action_delay=data.get("action_delay", 1.0),
            click_delay=data.get("click_delay", 0.1),
            type_delay=data.get("type_delay", 0.05),
            response_timeout=data.get("response_timeout", 5.0),
            level_threshold=data.get("level_threshold", 11),
            max_fails=data.get("max_fails", 2),
            min_gold=data.get("min_gold", 10000),
            max_level=data.get("max_level", 20),
            auto_sell_on_threshold=data.get("auto_sell_on_threshold", True),
            auto_sell_on_max_fails=data.get("auto_sell_on_max_fails", True),
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
