"""Game state management"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class EnhanceResult(Enum):
    """Enhancement result types"""
    SUCCESS = "success"
    MAINTAIN = "maintain"
    DESTROY = "destroy"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Get Korean display name"""
        names = {
            EnhanceResult.SUCCESS: "성공",
            EnhanceResult.MAINTAIN: "유지",
            EnhanceResult.DESTROY: "파괴",
            EnhanceResult.UNKNOWN: "알 수 없음",
        }
        return names.get(self, "알 수 없음")

    @property
    def emoji(self) -> str:
        """Get emoji for the result"""
        emojis = {
            EnhanceResult.SUCCESS: "🟢",
            EnhanceResult.MAINTAIN: "🟡",
            EnhanceResult.DESTROY: "🔴",
            EnhanceResult.UNKNOWN: "⚪",
        }
        return emojis.get(self, "⚪")


class MacroState(Enum):
    """Macro execution state"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class GameState:
    """Current game state"""
    level: int = 0
    gold: int = 0
    fail_count: int = 0
    sword_name: str = ""  # 현재 칼 이름
    gold_spent: int = 0  # 마지막 액션에서 사용한 골드
    gold_earned: int = 0  # 마지막 액션에서 획득한 골드 (판매 시)
    last_result: Optional[EnhanceResult] = None
    last_update: datetime = field(default_factory=datetime.now)

    def update_from_result(
        self,
        result: EnhanceResult,
        new_level: int = None,
        new_gold: int = None,
        sword_name: str = None,
        gold_spent: int = 0,
        gold_earned: int = 0,
    ):
        """Update state based on enhancement result"""
        self.last_result = result
        self.last_update = datetime.now()
        self.gold_spent = gold_spent
        self.gold_earned = gold_earned

        if result == EnhanceResult.SUCCESS:
            self.level = new_level if new_level is not None else self.level + 1
            self.fail_count = 0
        elif result == EnhanceResult.MAINTAIN:
            self.fail_count += 1
        elif result == EnhanceResult.DESTROY:
            self.level = 0
            self.fail_count = 0

        if new_gold is not None:
            self.gold = new_gold

        if sword_name is not None:
            self.sword_name = sword_name

    def reset(self):
        """Reset state to initial values"""
        self.level = 0
        self.gold = 0
        self.fail_count = 0
        self.sword_name = ""
        self.gold_spent = 0
        self.gold_earned = 0
        self.last_result = None
        self.last_update = datetime.now()

    @property
    def level_display(self) -> str:
        """Get display string for current level"""
        return f"+{self.level}강"

    @property
    def gold_display(self) -> str:
        """Get display string for current gold"""
        return f"{self.gold:,}원"

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "level": self.level,
            "gold": self.gold,
            "fail_count": self.fail_count,
            "sword_name": self.sword_name,
            "gold_spent": self.gold_spent,
            "gold_earned": self.gold_earned,
            "last_result": self.last_result.value if self.last_result else None,
            "last_update": self.last_update.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        """Create from dictionary"""
        last_result = None
        if data.get("last_result"):
            try:
                last_result = EnhanceResult(data["last_result"])
            except ValueError:
                pass

        last_update = datetime.now()
        if data.get("last_update"):
            try:
                last_update = datetime.fromisoformat(data["last_update"])
            except ValueError:
                pass

        return cls(
            level=data.get("level", 0),
            gold=data.get("gold", 0),
            fail_count=data.get("fail_count", 0),
            sword_name=data.get("sword_name", ""),
            gold_spent=data.get("gold_spent", 0),
            gold_earned=data.get("gold_earned", 0),
            last_result=last_result,
            last_update=last_update,
        )
