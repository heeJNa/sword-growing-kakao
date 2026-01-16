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
from ..utils.logger import get_logger

logger = get_logger(__name__)


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
        logger.info("=== 수동 강화 시작 ===")
        try:
            gold_before = self.game_state.gold
            logger.debug(f"강화 전 상태: level={self.game_state.level}, gold={gold_before}")

            # Execute enhance
            logger.info("강화 명령 실행 중...")
            enhance(self.coords, self.settings)

            # Read result
            logger.debug("결과 대기 (0.5초)")
            time.sleep(0.5)
            logger.debug("채팅 상태 확인 중...")
            chat_text = check_status(self.coords, self.settings)
            logger.debug(f"채팅 텍스트 길이: {len(chat_text)}")

            result, state = parse_chat(chat_text)
            logger.info(f"파싱 결과: {result.value}, level={state.level}, gold={state.gold}")

            # Update state
            old_level = self.game_state.level
            self.game_state.update_from_result(result, state.level, state.gold)
            logger.info(f"상태 업데이트: {old_level}강 -> {self.game_state.level}강")

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

            logger.info(f"=== 수동 강화 완료: {result.value} ===")
            return result

        except Exception as e:
            logger.error(f"수동 강화 에러: {type(e).__name__}: {e}", exc_info=True)
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
        logger.info("=== 자동 모드 루프 시작 ===")
        logger.info(f"현재 좌표: output=({self.coords.chat_output_x}, {self.coords.chat_output_y}), input=({self.coords.chat_input_x}, {self.coords.chat_input_y})")
        logger.info(f"설정: target_level={self.settings.target_level}, action_delay={self.settings.action_delay}")

        self._set_macro_state(MacroState.RUNNING)

        # Start stats session
        self.stats.start_session(self.game_state.gold)
        logger.info(f"세션 시작: starting_gold={self.game_state.gold}")

        consecutive_errors = 0
        max_errors = 5
        loop_count = 0

        while not self._stop_event.is_set():
            loop_count += 1
            logger.debug(f"--- 루프 #{loop_count} ---")

            # Check for pause
            if not self._pause_event.is_set():
                logger.info("일시정지 대기 중...")
            self._pause_event.wait()

            if self._stop_event.is_set():
                logger.info("정지 이벤트 감지, 루프 종료")
                break

            try:
                # Get action from strategy
                logger.debug(f"전략 결정 요청: level={self.game_state.level}, gold={self.game_state.gold}, fail_count={self.game_state.fail_count}")
                action = self.strategy.decide(self.game_state)
                logger.info(f"전략 결정: {action.value}")

                if action == Action.STOP:
                    logger.info("전략이 STOP 반환, 루프 종료")
                    break

                gold_before = self.game_state.gold

                if action == Action.ENHANCE:
                    logger.info(f"강화 실행 (현재 {self.game_state.level}강)")
                    enhance(self.coords, self.settings)
                elif action == Action.SELL:
                    logger.info(f"판매 실행 (현재 {self.game_state.level}강)")
                    sell(self.coords, self.settings)
                elif action == Action.WAIT:
                    logger.info(f"대기 중... (목표 도달 또는 조건 미충족)")
                    time.sleep(self.settings.action_delay)
                    continue
                else:
                    logger.warning(f"알 수 없는 액션: {action}")
                    time.sleep(self.settings.action_delay)
                    continue

                # Read result
                logger.debug("결과 읽기 대기 (0.5초)")
                time.sleep(0.5)
                logger.debug("채팅 상태 확인 중...")
                chat_text = check_status(self.coords, self.settings)
                logger.debug(f"채팅 텍스트 (마지막 200자): ...{chat_text[-200:] if len(chat_text) > 200 else chat_text}")

                result, state = parse_chat(chat_text)
                logger.info(f"파싱 결과: result={result.value}, parsed_level={state.level}, parsed_gold={state.gold}")

                # Update state based on action
                if action == Action.ENHANCE:
                    old_level = self.game_state.level
                    self.game_state.update_from_result(result, state.level, state.gold)
                    logger.info(f"상태 업데이트: {old_level}강 -> {self.game_state.level}강 (결과: {result.value})")
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
                    logger.info(f"판매 완료: gold={state.gold}")

                self._notify_state_change()

                # Reset error counter on success
                consecutive_errors = 0

                # Delay before next action
                logger.debug(f"다음 액션 대기: {self.settings.action_delay}초")
                time.sleep(self.settings.action_delay)

            except Exception as e:
                consecutive_errors += 1
                logger.error(f"루프 에러 #{consecutive_errors}: {type(e).__name__}: {e}", exc_info=True)
                self._notify_error(e)

                if consecutive_errors >= max_errors:
                    logger.error(f"연속 에러 {max_errors}회 도달, 루프 종료")
                    self._set_macro_state(MacroState.ERROR)
                    break

                time.sleep(self.settings.action_delay * 2)

        # End session
        logger.info(f"=== 자동 모드 루프 종료 (총 {loop_count}회 반복) ===")
        self.stats.end_session()
        self._set_macro_state(MacroState.STOPPED)

    def start_auto(self) -> bool:
        """
        Start auto-mode loop in background thread.

        Returns:
            True if started successfully
        """
        logger.info("start_auto() 호출됨")

        if self._thread and self._thread.is_alive():
            logger.warning("이미 실행 중인 스레드 존재, 시작 취소")
            return False

        self._stop_event.clear()
        self._pause_event.set()

        logger.info("자동 모드 스레드 생성 중...")
        self._thread = threading.Thread(target=self._auto_loop, daemon=True)
        self._thread.start()
        logger.info("자동 모드 스레드 시작됨")

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
        logger.info(f"설정 업데이트: target_level={settings.target_level}, action_delay={settings.action_delay}")
        self.settings = settings
        if hasattr(self.strategy, 'settings'):
            self.strategy.settings = settings
        # Also update strategy config if applicable
        if hasattr(self.strategy, 'update_config'):
            self.strategy.update_config(
                target_level=settings.target_level,
                sell_on_target=settings.sell_on_target,
                pause_on_target=settings.pause_on_target,
                min_gold=settings.min_gold,
            )
            logger.debug("전략 config도 업데이트됨")

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
