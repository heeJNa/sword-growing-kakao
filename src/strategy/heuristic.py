"""Strategy for enhancement decisions"""
from dataclasses import dataclass
from typing import Optional
from .base import Strategy, Action
from ..core.state import GameState
from ..config.settings import Settings, DEFAULT_SETTINGS
from ..config.game_data import LEVEL_DATA, get_enhance_cost


@dataclass
class StrategyConfig:
    """Configuration for enhancement strategy"""
    target_level: int = 15  # Target level to reach
    sell_on_target: bool = False  # Sell when reaching target (usually False)
    min_gold: int = 1000  # Minimum gold to continue (sell if below)
    max_level: int = 20  # Maximum possible level in game
    pause_on_target: bool = True  # Pause when target reached


class EnhanceUntilTargetStrategy(Strategy):
    """
    Main strategy: Keep enhancing until target level is reached.

    Logic:
    1. If level >= target_level -> WAIT (target reached, pause)
       - Or SELL if sell_on_target is True
    2. If gold < min_gold and level > 0 -> SELL (need gold to continue)
    3. Otherwise -> ENHANCE (keep trying)

    On destroy (level goes to 0), automatically continues from 0.
    """

    def __init__(self, config: StrategyConfig = None, settings: Settings = None):
        self.config = config or StrategyConfig()
        self.settings = settings or DEFAULT_SETTINGS
        self._target_reached = False

    def decide(self, state: GameState) -> Action:
        """
        Decide next action based on current state.

        Args:
            state: Current game state

        Returns:
            Action to take (ENHANCE, SELL, or WAIT)
        """
        # Check if target reached
        if state.level >= self.config.target_level:
            self._target_reached = True
            if self.config.sell_on_target:
                return Action.SELL
            if self.config.pause_on_target:
                return Action.WAIT
            # If not selling or pausing, continue enhancing
            return Action.ENHANCE

        # Check if at absolute max level
        if state.level >= self.config.max_level:
            return Action.WAIT

        # Check gold - only sell if really necessary
        enhance_cost = get_enhance_cost(state.level)
        if state.gold < enhance_cost and state.gold < self.config.min_gold:
            if state.level > 0:
                return Action.SELL
            else:
                return Action.WAIT  # Can't do anything at 0 with no gold

        # Default: keep enhancing toward target
        return Action.ENHANCE

    def get_name(self) -> str:
        return "목표 강화"

    def get_description(self) -> str:
        return f"{self.config.target_level}강 목표까지 계속 강화"

    def update_config(self, **kwargs) -> None:
        """Update configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        # Reset target reached flag if target changed
        if "target_level" in kwargs:
            self._target_reached = False

    def reset(self) -> None:
        """Reset strategy state"""
        self._target_reached = False

    def is_target_reached(self) -> bool:
        """Check if target has been reached"""
        return self._target_reached


class SafeEnhanceStrategy(EnhanceUntilTargetStrategy):
    """
    Safe strategy - lower target, pause frequently for user check.
    """

    def __init__(self, settings: Settings = None):
        config = StrategyConfig(
            target_level=10,
            sell_on_target=False,
            pause_on_target=True,
            min_gold=1000,
        )
        super().__init__(config, settings)

    def get_name(self) -> str:
        return "안전 강화"

    def get_description(self) -> str:
        return "10강 목표, 도달 시 일시정지"


class AggressiveEnhanceStrategy(EnhanceUntilTargetStrategy):
    """
    Aggressive strategy - aim for high levels.
    """

    def __init__(self, settings: Settings = None):
        config = StrategyConfig(
            target_level=20,
            sell_on_target=False,
            pause_on_target=True,
            min_gold=500,
        )
        super().__init__(config, settings)

    def get_name(self) -> str:
        return "최고 강화"

    def get_description(self) -> str:
        return "20강 목표까지 무한 도전"


class ContinuousEnhanceStrategy(EnhanceUntilTargetStrategy):
    """
    Continuous strategy - never stop, sell on target and restart.
    For farming gold automatically.
    """

    def __init__(self, settings: Settings = None):
        config = StrategyConfig(
            target_level=12,
            sell_on_target=True,  # Sell and restart
            pause_on_target=False,
            min_gold=500,
        )
        super().__init__(config, settings)

    def get_name(self) -> str:
        return "무한 반복"

    def get_description(self) -> str:
        return "12강 도달 시 판매 후 재시작 (골드 파밍용)"


# Backward compatibility aliases
HeuristicStrategy = EnhanceUntilTargetStrategy
HeuristicConfig = StrategyConfig
