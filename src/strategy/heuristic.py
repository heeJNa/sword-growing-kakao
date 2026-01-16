"""Heuristic (rule-based) strategy for decision making"""
from dataclasses import dataclass
from typing import Optional
from .base import Strategy, Action
from ..core.state import GameState
from ..config.settings import Settings, DEFAULT_SETTINGS
from ..config.game_data import LEVEL_DATA, get_enhance_cost


@dataclass
class HeuristicConfig:
    """Configuration for heuristic strategy"""
    level_threshold: int = 11  # Start checking fails at this level
    max_fails: int = 2  # Sell after this many consecutive fails
    min_gold: int = 10000  # Minimum gold to continue
    max_level: int = 20  # Maximum level (always sell at max)
    target_level: int = 12  # Target level to sell at
    use_target_sell: bool = True  # Sell when reaching target level
    conservative_mode: bool = False  # More conservative decisions


class HeuristicStrategy(Strategy):
    """
    Rule-based decision strategy.

    Decision logic:
    1. If gold < min_gold -> SELL (need money)
    2. If level >= max_level -> SELL (max reached)
    3. If use_target_sell and level >= target_level -> SELL
    4. If level >= threshold and fails >= max_fails -> SELL
    5. Otherwise -> ENHANCE
    """

    def __init__(self, config: HeuristicConfig = None, settings: Settings = None):
        self.config = config or HeuristicConfig()
        self.settings = settings or DEFAULT_SETTINGS

        # Sync config with settings
        if settings:
            self.config.level_threshold = settings.level_threshold
            self.config.max_fails = settings.max_fails
            self.config.min_gold = settings.min_gold
            self.config.max_level = settings.max_level

    def decide(self, state: GameState) -> Action:
        """
        Decide next action based on current state.

        Args:
            state: Current game state

        Returns:
            Action to take
        """
        # Check if we have enough gold
        enhance_cost = get_enhance_cost(state.level)
        if state.gold < self.config.min_gold or state.gold < enhance_cost:
            # Not enough gold - need to sell or wait
            if state.level > 0:
                return Action.SELL
            else:
                return Action.WAIT

        # Check if at max level
        if state.level >= self.config.max_level:
            return Action.SELL

        # Check if at target level (optional)
        if self.config.use_target_sell and state.level >= self.config.target_level:
            return Action.SELL

        # Check fail count at high levels
        if state.level >= self.config.level_threshold:
            if state.fail_count >= self.config.max_fails:
                return Action.SELL

        # Conservative mode: sell earlier at high destroy rate levels
        if self.config.conservative_mode and state.level >= 10:
            destroy_rate = LEVEL_DATA.get(state.level, {}).get("destroy", 0)
            if destroy_rate >= 0.3:  # 30%+ destroy chance
                if state.fail_count >= 1:
                    return Action.SELL

        # Default: enhance
        return Action.ENHANCE

    def get_name(self) -> str:
        return "휴리스틱"

    def get_description(self) -> str:
        return f"규칙 기반 전략: {self.config.target_level}강 판매, 실패 {self.config.max_fails}회 시 판매"

    def update_config(self, **kwargs) -> None:
        """Update configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def reset(self) -> None:
        """Reset strategy state"""
        pass  # Heuristic strategy is stateless


class AggressiveStrategy(HeuristicStrategy):
    """
    More aggressive strategy - aims for higher levels.
    """

    def __init__(self, settings: Settings = None):
        config = HeuristicConfig(
            level_threshold=13,
            max_fails=3,
            target_level=15,
            use_target_sell=True,
            conservative_mode=False,
        )
        super().__init__(config, settings)

    def get_name(self) -> str:
        return "공격적"

    def get_description(self) -> str:
        return "고위험 고수익: 15강 목표, 실패 3회까지 허용"


class ConservativeStrategy(HeuristicStrategy):
    """
    Conservative strategy - safe and steady profits.
    """

    def __init__(self, settings: Settings = None):
        config = HeuristicConfig(
            level_threshold=9,
            max_fails=1,
            target_level=10,
            use_target_sell=True,
            conservative_mode=True,
        )
        super().__init__(config, settings)

    def get_name(self) -> str:
        return "보수적"

    def get_description(self) -> str:
        return "안전 위주: 10강 판매, 파괴 위험 최소화"
