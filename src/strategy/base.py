"""Base strategy interface"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..config.settings import Settings

from ..core.state import GameState


class Action(Enum):
    """Available actions"""
    ENHANCE = "enhance"
    SELL = "sell"
    WAIT = "wait"
    BUY_PROTECTION = "buy_protection"
    USE_PROTECTION = "use_protection"
    STOP = "stop"

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Get Korean display name"""
        names = {
            Action.ENHANCE: "강화",
            Action.SELL: "판매",
            Action.WAIT: "대기",
            Action.BUY_PROTECTION: "방지권 구매",
            Action.USE_PROTECTION: "방지권 사용",
            Action.STOP: "정지",
        }
        return names.get(self, "알 수 없음")


class Strategy(ABC):
    """Abstract base class for decision strategies"""

    # Optional attributes that subclasses may implement
    settings: Optional["Settings"] = None

    @abstractmethod
    def decide(self, state: GameState) -> Action:
        """
        Decide the next action based on current game state.

        Args:
            state: Current game state

        Returns:
            Action to take
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get strategy description"""
        pass

    def reset(self) -> None:
        """Reset strategy state (if any)"""
        pass

    def update_config(self, **kwargs) -> None:
        """Update strategy configuration (optional override)"""
        pass


class ManualStrategy(Strategy):
    """
    Manual strategy - always waits for user input.
    Used in manual mode where user presses hotkeys.
    """

    def decide(self, state: GameState) -> Action:
        return Action.WAIT

    def get_name(self) -> str:
        return "수동"

    def get_description(self) -> str:
        return "사용자가 직접 단축키로 조작합니다."
