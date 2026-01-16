"""Main macro runner module"""
import time
import threading
from typing import Optional, Callable
from datetime import datetime
from .state import GameState, MacroState, EnhanceResult
from .parser import parse_chat
from .actions import enhance, sell, check_status
from ..strategy.base import Strategy, Action
from ..strategy.heuristic import HeuristicStrategy
from ..stats.collector import StatsCollector
from ..config.settings import Settings, DEFAULT_SETTINGS
from ..config.coordinates import Coordinates, DEFAULT_COORDINATES


class MacroRunner:
    """
    Main macro runner that orchestrates the automation loop.

    Supports:
    - Manual mode (hotkey-triggered actions)
    - Auto mode (continuous loop with strategy)
    - Statistics collection
    - GUI integration via callbacks
    """

    def __init__(
        self,
        coords: Coordinates = None,
        settings: Settings = None,
        strategy: Strategy = None,
        stats_collector: StatsCollector = None,
    ):
        self.coords = coords or DEFAULT_COORDINATES
        self.settings = settings or DEFAULT_SETTINGS
        self.strategy = strategy or HeuristicStrategy(settings=self.settings)
        self.stats = stats_collector or StatsCollector()

        # State
        self.game_state = GameState()
        self.macro_state = MacroState.IDLE

        # Threading
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused by default

        # Callbacks for GUI updates
        self._on_state_change: Optional[Callable[[GameState], None]] = None
        self._on_result: Optional[Callable[[EnhanceResult], None]] = None
        self._on_status_change: Optional[Callable[[MacroState], None]] = None
        self._on_error: Optional[Callable[[Exception], None]] = None

    def set_callbacks(
        self,
        on_state_change: Callable[[GameState], None] = None,
        on_result: Callable[[EnhanceResult], None] = None,
        on_status_change: Callable[[MacroState], None] = None,
        on_error: Callable[[Exception], None] = None,
    ) -> None:
        """Set callback functions for GUI updates"""
        self._on_state_change = on_state_change
        self._on_result = on_result
        self._on_status_change = on_status_change
        self._on_error = on_error

    def _set_macro_state(self, state: MacroState) -> None:
        """Update macro state and notify callback"""
        self.macro_state = state
        if self._on_status_change:
            try:
                self._on_status_change(state)
            except Exception:
                pass

    def _notify_state_change(self) -> None:
        """Notify callback of game state change"""
        if self._on_state_change:
            try:
                self._on_state_change(self.game_state)
            except Exception:
                pass

    def _notify_result(self, result: EnhanceResult) -> None:
        """Notify callback of enhancement result"""
        if self._on_result:
            try:
                self._on_result(result)
            except Exception:
                pass

    def _notify_error(self, error: Exception) -> None:
        """Notify callback of error"""
        if self._on_error:
            try:
                self._on_error(error)
            except Exception:
                pass

    def manual_enhance(self) -> Optional[EnhanceResult]:
        """
        Execute a single enhancement (for manual mode).

        Returns:
            EnhanceResult or None on error
        """
        try:
            gold_before = self.game_state.gold

            # Execute enhance
            enhance(self.coords, self.settings)

            # Read result
            time.sleep(0.5)
            chat_text = check_status(self.coords, self.settings)
            result, state = parse_chat(chat_text)

            # Update state
            self.game_state.update_from_result(result, state.level, state.gold)
            self._notify_state_change()
            self._notify_result(result)

            # Record stats
            if self.stats.session:
                self.stats.record_enhance(
                    self.game_state.level,
                    result,
                    gold_before,
                    self.game_state.gold
                )

            return result

        except Exception as e:
            self._notify_error(e)
            return None

    def manual_sell(self) -> bool:
        """
        Execute a sell action (for manual mode).

        Returns:
            True if successful
        """
        try:
            # Execute sell
            sell(self.coords, self.settings)

            # Read result
            time.sleep(0.5)
            chat_text = check_status(self.coords, self.settings)
            _, state = parse_chat(chat_text)

            # Update state
            self.game_state.level = 0
            self.game_state.gold = state.gold
            self.game_state.fail_count = 0
            self._notify_state_change()

            # Record stats
            if self.stats.session:
                self.stats.record_sell(state.gold)

            return True

        except Exception as e:
            self._notify_error(e)
            return False

    def _auto_loop(self) -> None:
        """Main auto-mode loop"""
        self._set_macro_state(MacroState.RUNNING)

        # Start stats session
        self.stats.start_session(self.game_state.gold)

        consecutive_errors = 0
        max_errors = 5

        while not self._stop_event.is_set():
            # Check for pause
            self._pause_event.wait()

            if self._stop_event.is_set():
                break

            try:
                # Get action from strategy
                action = self.strategy.decide(self.game_state)

                if action == Action.STOP:
                    break

                gold_before = self.game_state.gold

                if action == Action.ENHANCE:
                    enhance(self.coords, self.settings)
                elif action == Action.SELL:
                    sell(self.coords, self.settings)
                elif action == Action.WAIT:
                    time.sleep(self.settings.action_delay)
                    continue
                else:
                    time.sleep(self.settings.action_delay)
                    continue

                # Read result
                time.sleep(0.5)
                chat_text = check_status(self.coords, self.settings)
                result, state = parse_chat(chat_text)

                # Update state based on action
                if action == Action.ENHANCE:
                    self.game_state.update_from_result(result, state.level, state.gold)
                    self.stats.record_enhance(
                        self.game_state.level if result != EnhanceResult.SUCCESS else self.game_state.level - 1,
                        result,
                        gold_before,
                        self.game_state.gold
                    )
                    self._notify_result(result)
                elif action == Action.SELL:
                    self.game_state.level = 0
                    self.game_state.gold = state.gold
                    self.game_state.fail_count = 0
                    self.stats.record_sell(state.gold)

                self._notify_state_change()

                # Reset error counter on success
                consecutive_errors = 0

                # Delay before next action
                time.sleep(self.settings.action_delay)

            except Exception as e:
                consecutive_errors += 1
                self._notify_error(e)

                if consecutive_errors >= max_errors:
                    self._set_macro_state(MacroState.ERROR)
                    break

                time.sleep(self.settings.action_delay * 2)

        # End session
        self.stats.end_session()
        self._set_macro_state(MacroState.STOPPED)

    def start_auto(self) -> bool:
        """
        Start auto-mode loop in background thread.

        Returns:
            True if started successfully
        """
        if self._thread and self._thread.is_alive():
            return False

        self._stop_event.clear()
        self._pause_event.set()

        self._thread = threading.Thread(target=self._auto_loop, daemon=True)
        self._thread.start()

        return True

    def stop(self) -> None:
        """Stop auto-mode loop"""
        self._stop_event.set()
        self._pause_event.set()  # Unpause to allow thread to exit

        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

        self._set_macro_state(MacroState.STOPPED)

    def pause(self) -> None:
        """Pause auto-mode loop"""
        self._pause_event.clear()
        self._set_macro_state(MacroState.PAUSED)

    def resume(self) -> None:
        """Resume paused auto-mode loop"""
        self._pause_event.set()
        self._set_macro_state(MacroState.RUNNING)

    def is_running(self) -> bool:
        """Check if auto-mode is running"""
        return self._thread is not None and self._thread.is_alive()

    def is_paused(self) -> bool:
        """Check if auto-mode is paused"""
        return not self._pause_event.is_set()

    def update_settings(self, settings: Settings) -> None:
        """Update settings"""
        self.settings = settings
        if hasattr(self.strategy, 'settings'):
            self.strategy.settings = settings

    def update_coordinates(self, coords: Coordinates) -> None:
        """Update screen coordinates"""
        self.coords = coords

    def update_strategy(self, strategy: Strategy) -> None:
        """Update decision strategy"""
        self.strategy = strategy

    def reset_state(self) -> None:
        """Reset game state"""
        self.game_state.reset()
        self._notify_state_change()
