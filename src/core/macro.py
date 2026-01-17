"""Main macro runner module"""
import copy
import re
import time
import threading
from typing import Optional, Callable, Tuple
from dataclasses import dataclass
from .state import GameState, MacroState, MacroMode, EnhanceResult
from .parser import parse_chat, parse_profile, RESULT_PATTERNS
from .actions import enhance, sell, check_status
from ..automation.clipboard import type_to_chat
from ..strategy.base import Strategy, Action
from ..strategy.heuristic import HeuristicStrategy
from ..stats.collector import StatsCollector
from ..config.settings import Settings, DEFAULT_SETTINGS
from ..config.coordinates import Coordinates, DEFAULT_COORDINATES
from ..utils.logger import get_logger

logger = get_logger(__name__)


def count_result_patterns(text: str) -> dict:
    """
    Count occurrences of result patterns in text.

    This is used for stale detection - if the count increases,
    we have new content even if the overall text looks similar.

    Args:
        text: Chat text to analyze

    Returns:
        Dictionary with counts for each result type
    """
    if not text:
        return {"success": 0, "maintain": 0, "destroy": 0, "total": 0}

    success_count = len(re.findall(RESULT_PATTERNS["success"], text))
    maintain_count = len(re.findall(RESULT_PATTERNS["maintain"], text))
    destroy_count = len(re.findall(RESULT_PATTERNS["destroy"], text))

    return {
        "success": success_count,
        "maintain": maintain_count,
        "destroy": destroy_count,
        "total": success_count + maintain_count + destroy_count
    }


# === Y Offset Constants ===
@dataclass(frozen=True)
class YOffsetConfig:
    """Y offset configuration for clipboard reading based on level."""
    HIGH_LEVEL_THRESHOLD: int = 9
    DEFAULT_OFFSET: int = 0
    # 9강 이상일 때 시도할 오프셋 리스트 (순서대로 시도)
    # - 0: 유지/파괴는 메시지가 짧아서 기본값으로 충분
    # - -65, -85, -105: 성공 시 축하 이미지/멘트로 인해 점점 더 위로
    OFFSETS_HIGH_LEVEL: tuple = (0, -65, -85, -105)
    # 9강 미만일 때 시도할 오프셋 리스트
    # - 0: 기본값
    # - -40: 메시지가 조금 길어질 경우
    OFFSETS_LOW_LEVEL: tuple = (0, -40)


Y_OFFSET_CONFIG = YOffsetConfig()


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
        self._state_lock = threading.Lock()  # Thread safety for game_state access

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
        """Notify callback of game state change (thread-safe)"""
        if self._on_state_change:
            try:
                # Create a copy of game_state to avoid race conditions
                with self._state_lock:
                    state_copy = copy.copy(self.game_state)
                self._on_state_change(state_copy)
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

            # Read result (wait for response)
            logger.debug(f"결과 대기 ({self.settings.result_check_delay}초)")
            time.sleep(self.settings.result_check_delay)
            logger.debug("채팅 상태 확인 중...")
            chat_text = check_status(self.coords, self.settings) or ""
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
            chat_text = check_status(self.coords, self.settings) or ""
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

    # === Helper methods for _auto_loop (extracted for readability) ===

    def _get_offsets_for_level(self, level: int) -> tuple:
        """Get list of y_offsets to try based on current level."""
        if level >= Y_OFFSET_CONFIG.HIGH_LEVEL_THRESHOLD:
            return Y_OFFSET_CONFIG.OFFSETS_HIGH_LEVEL  # (0, -65, -85, -105)
        else:
            return Y_OFFSET_CONFIG.OFFSETS_LOW_LEVEL  # (0, -40)

    def _read_chat_with_retry(self, y_offset: int, clipboard_before: str = None) -> str:
        """
        Read chat content with retry logic for empty or stale clipboard.

        Args:
            y_offset: Y coordinate offset for reading
            clipboard_before: Previous clipboard content to compare (for stale detection)

        Returns:
            Chat text content
        """
        max_retries = 3
        chat_text = ""

        # Count result patterns in previous content for smarter stale detection
        patterns_before = count_result_patterns(clipboard_before) if clipboard_before else None

        for retry in range(max_retries):
            logger.debug(f"채팅 상태 확인 중... (시도 {retry + 1}/{max_retries}, y_offset={y_offset})")
            chat_text = check_status(self.coords, self.settings, y_offset=y_offset) or ""

            # Check if clipboard is empty
            if not chat_text or len(chat_text.strip()) == 0:
                logger.warning(f"클립보드 내용 없음 - 재시도 대기 ({self.settings.retry_delay}초)")
                time.sleep(self.settings.retry_delay)
                continue

            # Check if clipboard content is same as before action (stale)
            # Use smarter detection: compare result pattern counts, not just text
            if clipboard_before and patterns_before and retry < max_retries - 1:
                patterns_now = count_result_patterns(chat_text)

                # If total result pattern count increased, we have new content
                if patterns_now["total"] > patterns_before["total"]:
                    logger.debug(f"새로운 결과 패턴 감지 (이전: {patterns_before['total']}, 현재: {patterns_now['total']})")
                    break

                # If text is exactly same and pattern count didn't increase, it's stale
                if chat_text == clipboard_before:
                    logger.warning(f"클립보드 내용이 액션 전과 동일 - 새 결과 대기 ({self.settings.retry_delay}초)")
                    time.sleep(self.settings.retry_delay)
                    continue

            # Valid new content
            logger.debug(f"새로운 클립보드 내용 확인됨 (길이: {len(chat_text) if chat_text else 0})")
            break

        return chat_text

    def _parse_with_offset_retry(
        self, chat_text: str, offsets: tuple
    ) -> Tuple[EnhanceResult, GameState, int]:
        """
        Parse chat text with stepped y-offset retry strategy.

        9강 이상: [0, -65, -85, -105] 순서로 시도
        - 0: 유지/파괴 결과는 메시지가 짧아서 기본값으로 충분
        - -65, -85, -105: 성공 시 축하 이미지/멘트로 점점 더 위로

        Args:
            chat_text: Initial chat text to parse (already read with offsets[0])
            offsets: Tuple of y_offsets to try in order

        Returns:
            Tuple of (result, state, failure_count)
        """
        # 첫 번째 시도: 이미 읽어온 chat_text로 파싱 (offsets[0]에서 읽음)
        result, state = parse_chat(chat_text)

        if result != EnhanceResult.UNKNOWN:
            return result, state, 0

        parse_failure_count = 1
        logger.warning(f"파싱 실패 #{parse_failure_count} (y_offset={offsets[0]})")

        # 나머지 오프셋 순회 (첫 번째는 이미 시도했으므로 건너뜀)
        for offset in offsets[1:]:
            time.sleep(self.settings.retry_delay)
            logger.debug(f"y_offset={offset}으로 재시도 중...")
            chat_text = check_status(self.coords, self.settings, y_offset=offset) or ""
            result, state = parse_chat(chat_text)

            if result != EnhanceResult.UNKNOWN:
                logger.info(f"파싱 성공 (y_offset={offset})")
                return result, state, parse_failure_count

            parse_failure_count += 1
            logger.warning(f"파싱 실패 #{parse_failure_count} (y_offset={offset})")

            # 최대 5회 실패 시 중단 (프로필 체크로 fallback)
            if parse_failure_count >= 5:
                logger.warning("5회 연속 파싱 실패 - 프로필 체크로 전환")
                break

        return result, state, parse_failure_count

    def _initialize_session(self) -> None:
        """Initialize session by checking profile and starting stats."""
        logger.info("=== 프로필 확인 중... ===")
        try:
            logger.info("프로필 명령 전송: /프로필")
            type_to_chat("/프로필", self.coords)
            time.sleep(self.settings.profile_check_delay)

            chat_text = check_status(self.coords, self.settings) or ""
            profile = parse_profile(chat_text)

            if profile:
                with self._state_lock:
                    if profile.level is not None:
                        self.game_state.level = profile.level
                    if profile.gold is not None:
                        self.game_state.gold = profile.gold
                    if profile.sword_name:
                        self.game_state.sword_name = profile.sword_name

                logger.info(f"=== 초기 상태 확인 완료 ===")
                logger.info(f"    현재 레벨: +{self.game_state.level}강")
                logger.info(f"    보유 골드: {self.game_state.gold:,} G")
                if profile.sword_name:
                    logger.info(f"    보유 검: {profile.sword_name}")
                self._notify_state_change()
            else:
                logger.warning("프로필 파싱 실패 - 기본값으로 시작")
        except Exception as e:
            logger.error(f"프로필 확인 에러: {e}")

        time.sleep(self.settings.action_delay)
        self.stats.start_session(self.game_state.gold)
        logger.info(f"세션 시작: starting_gold={self.game_state.gold:,}")

    def _auto_loop(self) -> None:
        """Main auto-mode loop"""
        logger.info("=== 자동 모드 루프 시작 ===")
        logger.info(f"현재 좌표: output=({self.coords.chat_output_x}, {self.coords.chat_output_y}), input=({self.coords.chat_input_x}, {self.coords.chat_input_y})")
        logger.info(f"설정: target_level={self.settings.target_level}, action_delay={self.settings.action_delay}")

        self._set_macro_state(MacroState.RUNNING)

        # Initialize session (profile check + stats start)
        self._initialize_session()

        consecutive_errors = 0
        max_errors = 5
        loop_count = 0

        while not self._stop_event.is_set():
            loop_count += 1
            logger.info(f"{'='*50}")
            logger.info(f"[ Cycle #{loop_count} ] 현재 {self.game_state.level}강 | 골드: {self.game_state.gold:,}")
            logger.info(f"{'='*50}")

            # Check for pause
            if not self._pause_event.is_set():
                logger.info("일시정지 대기 중...")
            self._pause_event.wait()

            if self._stop_event.is_set():
                logger.info("정지 이벤트 감지, 루프 종료")
                break

            try:
                # Check gold before action - stop if insufficient
                if self.game_state.gold < self.settings.min_gold:
                    logger.warning(f"골드 부족! 현재: {self.game_state.gold:,} < 최소: {self.settings.min_gold:,}")
                    logger.info("골드 부족으로 작업 중지")
                    break

                # Get action from strategy
                logger.debug(f"전략 결정 요청: level={self.game_state.level}, gold={self.game_state.gold}, fail_count={self.game_state.fail_count}")
                action = self.strategy.decide(self.game_state)
                logger.info(f"전략 결정: {action.value}")

                if action == Action.STOP:
                    logger.info("전략이 STOP 반환, 루프 종료")
                    break

                gold_before = self.game_state.gold
                current_level = self.game_state.level

                # Get list of y_offsets to try based on level
                offsets = self._get_offsets_for_level(current_level)
                initial_offset = offsets[0]  # 첫 번째 오프셋으로 초기 읽기

                # Store clipboard content before action for stale detection
                clipboard_before_action = check_status(self.coords, self.settings, y_offset=initial_offset) or ""

                if action == Action.ENHANCE:
                    logger.info(f"강화 실행 (현재 {current_level}강)")
                    enhance(self.coords, self.settings)
                elif action == Action.SELL:
                    # Double-check gold before selling
                    if self.game_state.gold < self.settings.min_gold:
                        logger.warning("골드 부족 - 판매 취소, 작업 중지")
                        break
                    logger.info(f"판매 실행 (현재 {current_level}강)")
                    sell(self.coords, self.settings)
                elif action == Action.WAIT:
                    logger.info(f"대기 중... (목표 도달 또는 조건 미충족)")
                    time.sleep(self.settings.action_delay)
                    continue
                else:
                    logger.warning(f"알 수 없는 액션: {action}")
                    time.sleep(self.settings.action_delay)
                    continue

                # Read result with retry logic
                logger.debug(f"결과 읽기 대기 ({self.settings.result_check_delay}초)")
                time.sleep(self.settings.result_check_delay)

                # Read chat with retry (handles empty/stale clipboard)
                chat_text = self._read_chat_with_retry(initial_offset, clipboard_before_action)
                logger.debug(f"채팅 텍스트 (마지막 200자): ...{chat_text[-200:] if chat_text and len(chat_text) > 200 else (chat_text or '')}")

                # Parse with y-offset retry strategy (tries offsets in order)
                result, state, parse_failure_count = self._parse_with_offset_retry(
                    chat_text, offsets
                )
                logger.info(f"파싱 결과: result={result.value}, parsed_level={state.level}, parsed_gold={state.gold}")

                # Stop after 5 consecutive parse failures (프로필 체크로 fallback)
                if result == EnhanceResult.UNKNOWN and parse_failure_count >= 5:
                    logger.warning(f"파싱 5회 연속 실패 - 프로필 체크로 전환")
                    # 프로필 체크는 아래 UNKNOWN 핸들링에서 수행됨

                if result != EnhanceResult.UNKNOWN and parse_failure_count > 0:
                    logger.info(f"재시도 파싱 결과: result={result.value}, parsed_level={state.level}, parsed_gold={state.gold}")

                # === UNKNOWN result handling: check profile to get actual state ===
                if result == EnhanceResult.UNKNOWN:
                    logger.warning("결과 여전히 UNKNOWN - 프로필 확인으로 상태 동기화")
                    time.sleep(self.settings.retry_delay)

                    # Check profile to get current level and gold
                    type_to_chat("/프로필", self.coords)
                    time.sleep(self.settings.profile_check_delay)
                    profile_text = check_status(self.coords, self.settings) or ""
                    profile = parse_profile(profile_text)

                    if profile:
                        old_level = self.game_state.level
                        if profile.level is not None:
                            state.level = profile.level
                        if profile.gold is not None:
                            state.gold = profile.gold
                            self.game_state.gold = profile.gold

                        logger.info(f"프로필 확인: +{profile.level}강, {profile.gold:,} G")

                        # Determine what happened based on level change
                        if profile.level is not None:
                            if profile.level == old_level + 1:
                                result = EnhanceResult.SUCCESS
                                logger.info(f"레벨 증가 감지 ({old_level} → {profile.level}) - SUCCESS로 판단")
                            elif profile.level == old_level:
                                result = EnhanceResult.MAINTAIN
                                logger.info(f"레벨 유지 감지 ({old_level}) - MAINTAIN으로 판단")
                            elif profile.level == 0 or profile.level < old_level:
                                result = EnhanceResult.DESTROY
                                logger.info(f"레벨 감소/리셋 감지 ({old_level} → {profile.level}) - DESTROY로 판단")

                        # Check gold after profile update
                        if self.game_state.gold < self.settings.min_gold:
                            logger.warning(f"프로필 확인 후 골드 부족! 현재: {self.game_state.gold:,} < 최소: {self.settings.min_gold:,}")
                            logger.info("골드 부족으로 작업 중지")
                            break
                    else:
                        logger.error("프로필 파싱도 실패 - 상태 불명, 계속 진행")

                # Check if result is stale (previous result instead of new result)
                # SUCCESS: new level should be current_level + 1
                # MAINTAIN: new level should be current_level
                # DESTROY: new level should be 0
                if action == Action.ENHANCE:
                    is_stale = False

                    # Special case: MAINTAIN with level = current_level + 1
                    # This means a SUCCESS was missed in between (timing/offset issue)
                    # The clipboard captured an old MAINTAIN message but sword info shows new level
                    if result == EnhanceResult.MAINTAIN and state.level == current_level + 1:
                        logger.warning(f"중간 성공 누락 감지! 현재: {current_level}강 → 파싱: {state.level}강 (MAINTAIN)")
                        logger.info(f"SUCCESS로 재분류: 실제 레벨이 {current_level}→{state.level}로 증가함")
                        # Change result to SUCCESS since level actually increased
                        result = EnhanceResult.SUCCESS
                        # state.level already contains the correct new level (current_level + 1)

                    # Special case: MAINTAIN/SUCCESS with level = 0
                    # This means a DESTROY was missed (timing/offset issue)
                    if result in (EnhanceResult.MAINTAIN, EnhanceResult.SUCCESS) and state.level == 0 and current_level > 0:
                        logger.warning(f"중간 파괴 누락 감지! 현재: {current_level}강 → 파싱: 0강 ({result.value})")
                        logger.info(f"DESTROY로 재분류: 실제 레벨이 0으로 리셋됨")
                        # Change result to DESTROY since level reset to 0
                        result = EnhanceResult.DESTROY

                    if result == EnhanceResult.SUCCESS and state.level != current_level + 1:
                        logger.warning(f"결과가 오래됨 (SUCCESS) - 예상: {current_level + 1}강, 파싱: {state.level}강")
                        is_stale = True
                    elif result == EnhanceResult.MAINTAIN and state.level != current_level:
                        logger.warning(f"결과가 오래됨 (MAINTAIN) - 예상: {current_level}강, 파싱: {state.level}강")
                        is_stale = True

                    if is_stale:
                        logger.info(f"추가 대기 ({self.settings.stale_result_delay}초) 후 재확인...")
                        time.sleep(self.settings.stale_result_delay)
                        # stale 재확인 시 오프셋 리스트 순회
                        for offset in offsets:
                            chat_text = check_status(self.coords, self.settings, y_offset=offset) or ""
                            result, state = parse_chat(chat_text)
                            if result != EnhanceResult.UNKNOWN:
                                break
                        logger.info(f"재확인 결과: result={result.value}, parsed_level={state.level}, parsed_gold={state.gold}")

                        # Still stale? Wait more and retry once more
                        still_stale = False
                        if result == EnhanceResult.SUCCESS and state.level != current_level + 1:
                            still_stale = True
                        elif result == EnhanceResult.MAINTAIN and state.level != current_level:
                            still_stale = True

                        if still_stale:
                            logger.warning(f"여전히 오래된 결과 - 추가 대기 ({self.settings.stale_result_delay * 2}초) 후 마지막 시도")
                            time.sleep(self.settings.stale_result_delay * 2)
                            for offset in offsets:
                                chat_text = check_status(self.coords, self.settings, y_offset=offset) or ""
                                result, state = parse_chat(chat_text)
                                if result != EnhanceResult.UNKNOWN:
                                    break
                            logger.info(f"최종 결과: result={result.value}, parsed_level={state.level}, parsed_gold={state.gold}")

                # Update state based on action
                if action == Action.ENHANCE:
                    old_level = self.game_state.level
                    self.game_state.update_from_result(result, state.level, state.gold)
                    logger.info(f"상태 업데이트: {old_level}강 -> {self.game_state.level}강 (결과: {result.value})")
                    # Always record at old_level (level before enhancement)
                    # - SUCCESS: old_level is the level that was enhanced
                    # - MAINTAIN: old_level is the current level (unchanged)
                    # - DESTROY: old_level is the level that was destroyed (not 0)
                    self.stats.record_enhance(
                        old_level,
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

    def _turbo_loop(self) -> None:
        """
        Turbo mode loop - fast enhancement without checking each result.

        - 1초 간격으로 강화 명령 입력
        - 100회마다 프로필 확인하여 현재 레벨 체크
        - 목표 레벨 도달 시 정지
        """
        logger.info("=== 터보 모드 루프 시작 ===")
        logger.info(f"설정: target_level={self.settings.target_level}, 확인 간격=100회")

        self._set_macro_state(MacroState.RUNNING)

        # Initialize session (프로필 확인 + 통계 시작)
        self._initialize_session()

        loop_count = 0
        check_interval = 100  # 100회마다 확인
        log_interval = 20  # 20회마다 진행 로그
        turbo_delay = 1.0  # 1초 간격
        consecutive_errors = 0
        max_errors = 5

        while not self._stop_event.is_set():
            loop_count += 1

            # Check for pause
            if not self._pause_event.is_set():
                logger.info("일시정지 대기 중...")
            self._pause_event.wait()

            if self._stop_event.is_set():
                break

            try:
                # 강화 명령만 입력 (결과 확인 안 함)
                enhance(self.coords, self.settings)

                # 진행 상황 로그 (20회마다)
                if loop_count % log_interval == 0 and loop_count % check_interval != 0:
                    logger.info(f"터보 모드 진행 중... ({loop_count}회)")

                # 100회마다 프로필 확인
                if loop_count % check_interval == 0:
                    logger.info(f"=== {loop_count}회 도달, 프로필 확인 중... ===")
                    time.sleep(self.settings.result_check_delay)  # 마지막 강화 결과 대기

                    # 프로필 확인
                    type_to_chat("/프로필", self.coords)
                    time.sleep(self.settings.profile_check_delay)

                    chat_text = check_status(self.coords, self.settings) or ""
                    profile = parse_profile(chat_text)

                    if profile:
                        # Thread-safe 상태 업데이트 및 조건 체크
                        with self._state_lock:
                            if profile.level is not None:
                                self.game_state.level = profile.level
                            if profile.gold is not None:
                                self.game_state.gold = profile.gold
                            if profile.sword_name:
                                self.game_state.sword_name = profile.sword_name

                            # Lock 내에서 현재 값 복사
                            current_level = self.game_state.level
                            current_gold = self.game_state.gold

                        logger.info(f"현재 상태: +{current_level}강, {current_gold:,} G")
                        self._notify_state_change()

                        # 목표 레벨 도달 확인
                        if current_level >= self.settings.target_level:
                            logger.info(f"🎉 목표 레벨 {self.settings.target_level}강 도달! 정지합니다.")
                            break

                        # 골드 부족 확인
                        if current_gold < self.settings.min_gold:
                            logger.warning(f"골드 부족! 현재: {current_gold:,} < 최소: {self.settings.min_gold:,}")
                            break
                    else:
                        logger.warning("프로필 파싱 실패, 계속 진행")

                # 1초 대기
                time.sleep(turbo_delay)

                # Reset error counter on success
                consecutive_errors = 0

            except Exception as e:
                consecutive_errors += 1
                logger.error(f"터보 모드 에러 #{consecutive_errors}: {type(e).__name__}: {e}", exc_info=True)
                self._notify_error(e)

                if consecutive_errors >= max_errors:
                    logger.error(f"연속 에러 {max_errors}회 도달, 터보 모드 종료")
                    self._set_macro_state(MacroState.ERROR)
                    break

                time.sleep(turbo_delay * 2)

        # End session
        logger.info(f"=== 터보 모드 루프 종료 (총 {loop_count}회 반복) ===")
        self.stats.end_session()
        if self.macro_state != MacroState.ERROR:
            self._set_macro_state(MacroState.STOPPED)

    def start_auto(self, mode: MacroMode = MacroMode.NORMAL) -> bool:
        """
        Start auto-mode loop in background thread.

        Args:
            mode: MacroMode.NORMAL (기본) or MacroMode.TURBO (터보)

        Returns:
            True if started successfully
        """
        logger.info(f"start_auto() 호출됨 (mode={mode.value})")
        logger.debug(f"현재 상태: macro_state={self.macro_state}, thread={self._thread}, stop_event={self._stop_event.is_set()}")

        # Check if thread exists and is still alive
        if self._thread is not None:
            if self._thread.is_alive():
                logger.warning("이미 실행 중인 스레드 존재, 시작 취소")
                return False
            else:
                # Thread finished but reference wasn't cleared, clean it up
                logger.debug("이전 스레드 참조 정리")
                self._thread = None

        # Reset events for new run - CRITICAL: must clear stop event before starting
        self._stop_event.clear()
        self._pause_event.set()
        logger.debug(f"이벤트 초기화 완료: stop_event={self._stop_event.is_set()}, pause_event={self._pause_event.is_set()}")

        # Reset macro state
        self.macro_state = MacroState.IDLE
        logger.debug("매크로 상태 IDLE로 초기화")

        # Select loop based on mode
        if mode == MacroMode.TURBO:
            logger.info("터보 모드 스레드 생성 중...")
            self._thread = threading.Thread(target=self._turbo_loop, daemon=True)
        else:
            logger.info("기본 모드 스레드 생성 중...")
            self._thread = threading.Thread(target=self._auto_loop, daemon=True)

        self._thread.start()
        logger.info(f"{mode.display_name} 스레드 시작됨")

        return True

    def stop(self) -> None:
        """Stop auto-mode loop"""
        logger.info("stop() 호출됨")

        self._stop_event.set()
        self._pause_event.set()  # Unpause to allow thread to exit

        if self._thread is not None:
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                logger.warning("스레드가 5초 내에 종료되지 않음")
            self._thread = None

        self._set_macro_state(MacroState.STOPPED)
        logger.info("stop() 완료")

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
