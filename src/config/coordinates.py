"""Screen coordinates configuration for KakaoTalk chat window"""
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class Coordinates:
    """Screen coordinates for automation"""

    # Chat output area - where messages are displayed
    chat_output_x: int = 500
    chat_output_y: int = 400

    # Chat input area - where commands are typed
    chat_input_x: int = 500
    chat_input_y: int = 700

    # Window position (optional, for reference)
    window_x: int = 0
    window_y: int = 0
    window_width: int = 800
    window_height: int = 600

    @property
    def chat_output(self) -> tuple:
        """Get chat output coordinates as tuple"""
        return (self.chat_output_x, self.chat_output_y)

    @property
    def chat_input(self) -> tuple:
        """Get chat input coordinates as tuple"""
        return (self.chat_input_x, self.chat_input_y)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "chat_output_x": self.chat_output_x,
            "chat_output_y": self.chat_output_y,
            "chat_input_x": self.chat_input_x,
            "chat_input_y": self.chat_input_y,
            "window_x": self.window_x,
            "window_y": self.window_y,
            "window_width": self.window_width,
            "window_height": self.window_height,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Coordinates":
        """Create from dictionary"""
        return cls(
            chat_output_x=data.get("chat_output_x", 500),
            chat_output_y=data.get("chat_output_y", 400),
            chat_input_x=data.get("chat_input_x", 500),
            chat_input_y=data.get("chat_input_y", 700),
            window_x=data.get("window_x", 0),
            window_y=data.get("window_y", 0),
            window_width=data.get("window_width", 800),
            window_height=data.get("window_height", 600),
        )

    def save(self, path: str = None) -> None:
        """Save coordinates to file"""
        if path is None:
            config_dir = Path.home() / ".sword-macro"
            config_dir.mkdir(parents=True, exist_ok=True)
            path = str(config_dir / "coordinates.json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str = None) -> "Coordinates":
        """Load coordinates from file"""
        if path is None:
            path = str(Path.home() / ".sword-macro" / "coordinates.json")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except FileNotFoundError:
            return cls()


# Default coordinates instance - load from file if exists
DEFAULT_COORDINATES = Coordinates.load()
