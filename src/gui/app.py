"""Main GUI Application"""
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import queue
from pathlib import Path
from typing import Optional

from .widgets.status_panel import StatusPanel
from .widgets.stats_panel import StatsPanel
from .widgets.system_log_panel import SystemLogPanel
from .charts.bar_chart import LevelProbabilityChart
from .widgets.info_log_panel import InfoLogPanel
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.calibration_dialog import CalibrationDialog

from ..core.macro import MacroRunner
from ..core.state import GameState, MacroState, EnhanceResult
from ..config.settings import Settings
from ..config.coordinates import Coordinates
from ..stats.collector import StatsCollector
from ..stats.models import SessionStats
from ..automation.hotkeys import HotkeyListener
from ..utils.logger import get_logger
from ..utils.single_instance import ensure_single_instance, release_single_instance

# Logger for this module
logger = get_logger(__name__)

# Try to import system tray (optional dependency)
# NOTE: System tray is disabled on macOS because pystray runs its own
# NSApplication run loop in a background thread, which conflicts with
# tkinter's mainloop and causes crashes in app bundles.
try:
    if sys.platform == "darwin":
        # Disable system tray on macOS to prevent NSUpdateCycleInitialize crash
        HAS_SYSTEM_TRAY = False
    else:
        from .system_tray import SystemTray
        HAS_SYSTEM_TRAY = True
except ImportError:
    HAS_SYSTEM_TRAY = False


class MacroApp:
    """Main GUI Application for the sword enhancement macro"""

    def __init__(self):
        logger.info("검키우기 매크로 시작")

        # Shutdown flag to prevent callbacks during shutdown
        self._shutting_down = False

        # Thread-safe queue for callbacks from background threads
        self._callback_queue = queue.Queue()

        # Dirty flag for chart updates - only redraw when data changes
        self._chart_dirty = False
        self._last_enhance_count = 0

        # Check single instance
        if not ensure_single_instance("sword-macro"):
            logger.error("이미 실행 중인 인스턴스가 있습니다!")
            import tkinter.messagebox as msgbox
            root = tk.Tk()
            root.withdraw()
            msgbox.showerror("실행 오류", "프로그램이 이미 실행 중입니다.\n기존 프로그램을 종료하고 다시 시도해주세요.")
            root.destroy()
            raise SystemExit(1)

        # Load configuration
        self.settings = Settings.load()
        self.coords = Coordinates.load()
        logger.debug(f"설정 로드 완료: target_level={self.settings.target_level}")

        # Initialize components
        self.stats_collector = StatsCollector()
        self.macro = MacroRunner(
            coords=self.coords,
            settings=self.settings,
            stats_collector=self.stats_collector,
        )

        # Hotkey listener
        self.hotkey_listener = HotkeyListener()
        self._setup_hotkeys()

        # Create main window
        self.root = tk.Tk()
        self.root.title("검키우기 매크로 v1.0")

        # Center window on screen
        window_width = 1100
        window_height = 820
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 3  # 1/3 from top for better visibility
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(950, 780)

        # Set icon if exists
        try:
            icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass

        # Setup UI
        self._setup_ui()

        # Setup callbacks
        self._setup_callbacks()

        # Start hotkey listener
        self.hotkey_listener.start()
        logger.info("단축키 리스너 시작됨")

        # Setup system tray (minimize to tray on close)
        self._setup_system_tray()

        # Handle window close (minimize to tray)
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # Note: _start_update_loop() and _bring_to_front() are called in run()
        # to ensure mainloop is ready (required for macOS app bundle)

    def _setup_ui(self) -> None:
        """Setup main UI layout with tabs"""
        # Main notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab 1: Dashboard
        dashboard_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(dashboard_frame, text="📊 대시보드")
        self._setup_dashboard(dashboard_frame)

        # Tab 2: System Log
        log_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(log_frame, text="📝 시스템 로그")
        self.system_log_panel = SystemLogPanel(log_frame)
        self.system_log_panel.pack(fill="both", expand=True)

        # Setup system log panel control callbacks
        self.system_log_panel.set_control_callbacks(
            on_start=self._on_start,
            on_pause=self._on_pause,
            on_stop=self._on_stop,
        )

        # Menu bar
        self._setup_menu()

    def _setup_dashboard(self, parent) -> None:
        """Setup dashboard tab content"""
        # Top section - status and charts
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill="both", expand=True)

        # Left panel - status, stats and controls
        left_frame = ttk.Frame(top_frame, width=320)
        left_frame.pack(side="left", fill="both", padx=(0, 10))
        left_frame.pack_propagate(False)

        self.status_panel = StatusPanel(left_frame)
        self.status_panel.pack(fill="x", pady=(0, 5))

        self.stats_panel = StatsPanel(left_frame)
        self.stats_panel.pack(fill="x", pady=(0, 5))

        # 자동 모드
        auto_control = ttk.LabelFrame(left_frame, text="자동 모드", padding=5)
        auto_control.pack(fill="x", pady=(0, 5))

        auto_row1 = ttk.Frame(auto_control)
        auto_row1.pack(fill="x", pady=2)

        self.dash_start_btn = ttk.Button(auto_row1, text="▶ 시작", command=self._on_start)
        self.dash_start_btn.pack(side="left", padx=2, expand=True, fill="x")

        self.dash_pause_btn = ttk.Button(auto_row1, text="⏸ 일시정지", command=self._on_pause, state="disabled")
        self.dash_pause_btn.pack(side="left", padx=2, expand=True, fill="x")

        self.dash_stop_btn = ttk.Button(auto_row1, text="■ 정지", command=self._on_stop, state="disabled")
        self.dash_stop_btn.pack(side="left", padx=2, expand=True, fill="x")

        # 수동 모드
        manual_control = ttk.LabelFrame(left_frame, text="수동 모드", padding=5)
        manual_control.pack(fill="x", pady=(0, 5))

        manual_row1 = ttk.Frame(manual_control)
        manual_row1.pack(fill="x", pady=2)

        self.dash_profile_btn = ttk.Button(manual_row1, text="📋 프로필", command=self._on_manual_profile)
        self.dash_profile_btn.pack(side="left", padx=2, expand=True, fill="x")

        self.dash_enhance_btn = ttk.Button(manual_row1, text="⚔ 강화", command=self._on_manual_enhance)
        self.dash_enhance_btn.pack(side="left", padx=2, expand=True, fill="x")

        self.dash_sell_btn = ttk.Button(manual_row1, text="💰 판매", command=self._on_manual_sell)
        self.dash_sell_btn.pack(side="left", padx=2, expand=True, fill="x")

        # 설정
        settings_control = ttk.LabelFrame(left_frame, text="설정", padding=5)
        settings_control.pack(fill="x", pady=(0, 5))

        settings_row1 = ttk.Frame(settings_control)
        settings_row1.pack(fill="x", pady=2)

        ttk.Button(settings_row1, text="⚙ 전략", command=self._on_settings).pack(side="left", padx=2, expand=True, fill="x")
        ttk.Button(settings_row1, text="🎯 좌표", command=self._on_calibration).pack(side="left", padx=2, expand=True, fill="x")
        ttk.Button(settings_row1, text="📤 내보내기", command=self._on_export).pack(side="left", padx=2, expand=True, fill="x")

        # Right panel - charts
        right_frame = ttk.Frame(top_frame)
        right_frame.pack(side="left", fill="both", expand=True)

        # Bar chart (fixed height)
        chart_frame1 = ttk.LabelFrame(right_frame, text="레벨별 확률", height=320)
        chart_frame1.pack(fill="x", pady=(0, 5))
        chart_frame1.pack_propagate(False)
        self.bar_chart = LevelProbabilityChart(chart_frame1)

        # Info log panel (expand to fill remaining space)
        log_frame2 = ttk.LabelFrame(right_frame, text="실행 로그")
        log_frame2.pack(fill="both", expand=True, pady=(5, 0))
        self.info_log_panel = InfoLogPanel(log_frame2)
        self.info_log_panel.pack(fill="both", expand=True)

        # Load cumulative stats and update chart on startup
        self._load_and_show_cumulative_stats()

        # Set initial target level display
        self.status_panel.update_target_level(self.settings.target_level)

    def _setup_system_tray(self) -> None:
        """Setup system tray for minimize to tray"""
        self.system_tray = None
        if HAS_SYSTEM_TRAY:
            try:
                # System tray callbacks run on a background thread,
                # so we wrap them to execute on the main thread via queue
                self.system_tray = SystemTray(
                    on_show=lambda: self._safe_after(self._show_window),
                    on_quit=lambda: self._safe_after(self._on_quit),
                    on_start=lambda: self._safe_after(self._on_start),
                    on_stop=lambda: self._safe_after(self._on_stop),
                )
                self.system_tray.start()
                logger.info("System Tray 초기화 완료")
            except Exception as e:
                logger.warning(f"System Tray 초기화 실패: {e}")
                self.system_tray = None

    def _setup_menu(self) -> None:
        """Setup menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="파일", menu=file_menu)
        file_menu.add_command(label="통계 내보내기", command=self._on_export)
        file_menu.add_separator()
        if HAS_SYSTEM_TRAY:
            file_menu.add_command(label="트레이로 최소화", command=self._minimize_to_tray)
            file_menu.add_separator()
        file_menu.add_command(label="종료", command=self._on_quit)

        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="설정", menu=settings_menu)
        settings_menu.add_command(label="전략 설정", command=self._on_settings)
        settings_menu.add_command(label="좌표 설정", command=self._on_calibration)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="도움말", menu=help_menu)
        help_menu.add_command(label="단축키 안내", command=self._show_hotkeys)
        if sys.platform == "darwin":
            help_menu.add_command(label="Mac 권한 안내", command=self._show_mac_permissions)
        help_menu.add_separator()
        help_menu.add_command(label="정보", command=self._show_about)

    def _setup_hotkeys(self) -> None:
        """Setup global hotkeys"""
        self.hotkey_listener.register("f1", self._hotkey_enhance)
        self.hotkey_listener.register("f2", self._hotkey_sell)
        self.hotkey_listener.register("f3", self._hotkey_start)
        self.hotkey_listener.register("f4", self._hotkey_pause)
        self.hotkey_listener.register("f5", self._hotkey_stop)
        self.hotkey_listener.register("escape", self._hotkey_emergency_stop)

    def _setup_callbacks(self) -> None:
        """Setup macro callbacks for GUI updates"""
        self.macro.set_callbacks(
            on_state_change=self._on_state_change,
            on_result=self._on_result,
            on_status_change=self._on_status_change,
            on_error=self._on_error,
        )

    def _start_update_loop(self) -> None:
        """Start periodic GUI update and queue processing"""
        self._process_queue()
        self._update_gui()

    def _process_queue(self) -> None:
        """Process callbacks from background threads (runs on main thread)"""
        if self._shutting_down:
            return

        try:
            # Process all pending callbacks
            while True:
                try:
                    callback = self._callback_queue.get_nowait()
                    if callback and not self._shutting_down:
                        try:
                            callback()
                        except tk.TclError:
                            pass
                except queue.Empty:
                    break

            # Schedule next queue check (every 50ms)
            if not self._shutting_down:
                self.root.after(50, self._process_queue)
        except tk.TclError:
            pass

    def _load_and_show_cumulative_stats(self) -> None:
        """Load cumulative stats from previous sessions and show in chart"""
        try:
            cumulative_stats = self.stats_collector.get_cumulative_level_stats_as_model()
            if cumulative_stats:
                logger.info(f"누적 통계 로드: {len(cumulative_stats)}개 레벨")
                self.bar_chart.update(cumulative_stats)
        except Exception as e:
            logger.warning(f"누적 통계 로드 실패: {e}")

    def _get_combined_level_stats(self) -> dict:
        """
        Get combined level stats: cumulative + current session.
        This merges previous session data with the current session.
        """
        from ..stats.models import LevelStats

        # Start with cumulative stats
        combined = self.stats_collector.get_cumulative_level_stats_as_model()

        # Add current session stats
        if self.stats_collector.session:
            current_stats = self.stats_collector.get_all_level_stats()
            for level, stats in current_stats.items():
                if level in combined:
                    # Merge with existing
                    combined[level].success_count += stats.success_count
                    combined[level].maintain_count += stats.maintain_count
                    combined[level].destroy_count += stats.destroy_count
                    combined[level].total_attempts += stats.total_attempts
                else:
                    # Create new entry
                    combined[level] = LevelStats(level=level)
                    combined[level].success_count = stats.success_count
                    combined[level].maintain_count = stats.maintain_count
                    combined[level].destroy_count = stats.destroy_count
                    combined[level].total_attempts = stats.total_attempts

        return combined

    def _update_gui(self) -> None:
        """Periodic GUI update"""
        # Don't update if shutting down
        if self._shutting_down:
            return

        try:
            # Update status panel
            self.status_panel.update_state(self.macro.game_state)

            # Update stats panel if session exists
            if self.stats_collector.session:
                self.stats_panel.update_stats(self.stats_collector.session)

                # Only update chart when data has changed (dirty flag pattern)
                # This reduces CPU usage significantly
                current_count = self.stats_collector.session.total_enhances
                if self._chart_dirty or current_count != self._last_enhance_count:
                    combined_stats = self._get_combined_level_stats()
                    self.bar_chart.update(combined_stats)
                    self._chart_dirty = False
                    self._last_enhance_count = current_count

            # Schedule next update
            if not self._shutting_down:
                self.root.after(self.settings.gui_update_interval, self._update_gui)
        except tk.TclError:
            # Widget destroyed, stop updating
            pass

    # === Callbacks ===

    def _safe_after(self, callback) -> None:
        """Queue a callback to be executed on the main thread (thread-safe)"""
        if self._shutting_down:
            return
        # Put callback in queue - will be processed by _process_queue on main thread
        try:
            self._callback_queue.put_nowait(callback)
        except queue.Full:
            pass

    def _on_state_change(self, state: GameState) -> None:
        """Handle game state change (called from background thread)"""
        if self._shutting_down:
            return
        logger.debug(f"상태 변경: level={state.level}, gold={state.gold}")
        # GUI 업데이트는 메인 스레드에서 실행
        self._safe_after(lambda: self.status_panel.update_state(state))

    def _on_result(self, result: EnhanceResult) -> None:
        """Handle enhancement result (called from background thread)"""
        if self._shutting_down:
            return
        logger.info(f"강화 결과: {result.value}")

        # Mark chart as dirty so it will be updated on next GUI cycle
        self._chart_dirty = True

        # Enhancement results are now shown in the info_log_panel via logger.info()

    def _on_status_change(self, status: MacroState) -> None:
        """Handle macro status change (called from background thread)"""
        if self._shutting_down:
            return
        logger.info(f"매크로 상태: {status.value}")

        # GUI 업데이트는 메인 스레드에서 실행
        def update_ui():
            if self._shutting_down:
                return
            try:
                self.status_panel.update_macro_state(status)
                self.system_log_panel.set_running(status == MacroState.RUNNING)
                self.system_log_panel.set_paused(status == MacroState.PAUSED)
                self._update_dashboard_buttons(status)
            except tk.TclError:
                pass

        self._safe_after(update_ui)

    def _update_dashboard_buttons(self, status: MacroState) -> None:
        """Update dashboard control buttons based on macro state"""
        if self._shutting_down:
            return
        try:
            if status == MacroState.RUNNING:
                self.dash_start_btn.config(state="disabled")
                self.dash_pause_btn.config(state="normal", text="⏸ 일시정지")
                self.dash_stop_btn.config(state="normal")
            elif status == MacroState.PAUSED:
                self.dash_start_btn.config(state="disabled")
                self.dash_pause_btn.config(state="normal", text="▶ 재개")
                self.dash_stop_btn.config(state="normal")
            else:  # STOPPED, IDLE, ERROR
                self.dash_start_btn.config(state="normal")
                self.dash_pause_btn.config(state="disabled", text="⏸ 일시정지")
                self.dash_stop_btn.config(state="disabled")
        except tk.TclError:
            # Widget destroyed, ignore
            pass

    def _on_error(self, error: Exception) -> None:
        """Handle error"""
        if self._shutting_down:
            return
        logger.error(f"오류 발생: {error}")
        self._safe_after(lambda: messagebox.showerror("오류", str(error)))

    # === Control Actions ===

    def _on_start(self) -> None:
        """Start auto mode"""
        if not self.macro.is_running():
            logger.info("자동 모드 시작")
            self.macro.start_auto()

    def _on_pause(self) -> None:
        """Pause/Resume auto mode"""
        if self.macro.is_paused():
            logger.info("자동 모드 재개")
            self.macro.resume()
        else:
            logger.info("자동 모드 일시정지")
            self.macro.pause()

    def _on_stop(self) -> None:
        """Stop auto mode"""
        logger.info("자동 모드 정지")
        self.macro.stop()

    def _on_manual_profile(self) -> None:
        """Manual profile check"""
        if not self.macro.is_running():
            logger.info("수동 프로필 확인")
            # Run in background thread to avoid blocking GUI
            import threading
            def check_profile():
                from ..automation.clipboard import type_to_chat
                from ..core.actions import check_status
                from ..core.parser import parse_profile
                import time

                try:
                    type_to_chat("/프로필", self.coords)
                    time.sleep(1.5)
                    chat_text = check_status(self.coords, self.macro.settings)
                    profile = parse_profile(chat_text)

                    if profile:
                        if profile.level is not None:
                            self.macro.game_state.level = profile.level
                        if profile.gold is not None:
                            self.macro.game_state.gold = profile.gold
                        if profile.sword_name:
                            self.macro.game_state.sword_name = profile.sword_name

                        logger.info(f"프로필 확인: +{profile.level}강, {profile.gold:,} G")
                        self._safe_after(lambda: self.status_panel.update_state(self.macro.game_state))
                    else:
                        logger.warning("프로필 파싱 실패")
                except Exception as e:
                    logger.error(f"프로필 확인 에러: {e}")

            threading.Thread(target=check_profile, daemon=True).start()

    def _on_manual_enhance(self) -> None:
        """Manual enhance"""
        if not self.macro.is_running():
            logger.info("수동 강화 실행")
            self.macro.manual_enhance()

    def _on_manual_sell(self) -> None:
        """Manual sell"""
        if not self.macro.is_running():
            logger.info("수동 판매 실행")
            self.macro.manual_sell()

    def _on_settings(self) -> None:
        """Open settings dialog"""
        logger.debug("설정 다이얼로그 열기")
        SettingsDialog(
            self.root,
            self.settings,
            on_save=self._apply_settings
        )

    def _on_calibration(self) -> None:
        """Open calibration dialog"""
        logger.debug("좌표 설정 다이얼로그 열기")
        CalibrationDialog(
            self.root,
            self.coords,
            on_save=self._apply_coords
        )

    def _on_export(self) -> None:
        """Export statistics to file"""
        if not self.stats_collector.session:
            messagebox.showinfo("내보내기", "내보낼 통계가 없습니다.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON 파일", "*.json"), ("모든 파일", "*.*")],
            initialfile=f"stats_{self.stats_collector.session.session_id}.json"
        )

        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.stats_collector.session.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"통계 내보내기 완료: {path}")
            messagebox.showinfo("내보내기", f"통계가 저장되었습니다:\n{path}")

    def _apply_settings(self, settings: Settings) -> None:
        """Apply new settings"""
        self.settings = settings
        self.macro.update_settings(settings)
        # Update target level display in status panel
        self.status_panel.update_target_level(settings.target_level)
        logger.info(f"설정 적용: target_level={settings.target_level}")

    def _apply_coords(self, coords: Coordinates) -> None:
        """Apply new coordinates"""
        self.coords = coords
        self.macro.update_coordinates(coords)
        logger.info(f"좌표 적용: output=({coords.chat_output_x}, {coords.chat_output_y})")

    # === Hotkey Handlers ===

    def _hotkey_enhance(self) -> None:
        """F1: Manual enhance"""
        self._on_manual_enhance()

    def _hotkey_sell(self) -> None:
        """F2: Manual sell"""
        self._on_manual_sell()

    def _hotkey_start(self) -> None:
        """F3: Start auto mode"""
        self._on_start()

    def _hotkey_pause(self) -> None:
        """F4: Pause/Resume"""
        self._on_pause()

    def _hotkey_stop(self) -> None:
        """F5: Stop"""
        self._on_stop()

    def _hotkey_emergency_stop(self) -> None:
        """ESC: Emergency stop (called from hotkey listener background thread)"""
        logger.warning("긴급 정지!")
        self.macro.stop()
        # Use thread-safe queue instead of after() from background thread
        self._safe_after(lambda: messagebox.showwarning("긴급 정지", "매크로가 긴급 정지되었습니다."))

    # === Help Dialogs ===

    def _show_hotkeys(self) -> None:
        """Show hotkey help"""
        help_text = """
단축키 안내:

F1 - 수동 강화
F2 - 수동 판매
F3 - 자동 모드 시작
F4 - 일시정지/재개
F5 - 정지
ESC - 긴급 정지

※ macOS에서는 단축키가 지원되지 않습니다.
   GUI 버튼을 사용해주세요.
"""
        messagebox.showinfo("단축키 안내", help_text)

    def _show_mac_permissions(self) -> None:
        """Show macOS accessibility permissions help"""
        help_text = """
Mac 손쉬운 사용 권한 안내

이 앱은 마우스/키보드 제어를 위해
손쉬운 사용 권한이 필요합니다.

권한 설정 방법:
1. 시스템 설정 → 개인정보 보호 및 보안
2. 손쉬운 사용 선택
3. 터미널 앱 (Terminal, iTerm, VS Code 등) 토글 ON
4. 권한 부여 후 앱 재시작 필요

⚠️ 권한이 없으면 마우스 클릭과
   키보드 입력이 작동하지 않습니다.

※ macOS에서는 F1-F5 단축키가 지원되지 않습니다.
   GUI 버튼을 사용해주세요.
"""
        messagebox.showinfo("Mac 권한 안내", help_text)

    def _show_about(self) -> None:
        """Show about dialog"""
        about_text = """
검키우기 매크로 v1.0

카카오톡 검키우기 챗봇 게임의
강화를 자동화하는 프로그램입니다.

⚠️ 주의사항:
- 매크로 실행 중에는 마우스/키보드 사용 불가
- 디스플레이 배율 100% 설정 필요
- 카카오톡 창 위치 고정 필요
"""
        messagebox.showinfo("정보", about_text)

    def _on_window_close(self) -> None:
        """Handle window close button - minimize to tray if available"""
        if self.system_tray:
            self._minimize_to_tray()
        else:
            self._on_quit()

    def _minimize_to_tray(self) -> None:
        """Minimize window to system tray"""
        if self.system_tray:
            logger.info("트레이로 최소화")
            self.root.withdraw()
            self.system_tray.notify(
                "검키우기 매크로",
                "백그라운드에서 실행 중입니다. 트레이 아이콘을 클릭하여 열 수 있습니다."
            )

    def _bring_to_front(self) -> None:
        """Bring window to front (above other windows)"""
        logger.debug("창을 앞으로 가져오기")
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        self.root.focus_force()

    def _show_window(self) -> None:
        """Show window from system tray"""
        logger.info("창 복원")
        self.root.deiconify()
        self._bring_to_front()

    def _on_quit(self) -> None:
        """Handle actual quit"""
        if self.macro.is_running():
            if not messagebox.askyesno("종료", "매크로가 실행 중입니다. 종료하시겠습니까?"):
                return

        # CRITICAL: Set shutdown flag FIRST to prevent callbacks from accessing GUI
        self._shutting_down = True
        logger.info("프로그램 종료 시작...")

        # Clear macro callbacks to prevent any more GUI updates
        self.macro.set_callbacks(
            on_state_change=None,
            on_result=None,
            on_status_change=None,
            on_error=None,
        )

        # Stop macro if running
        if self.macro.is_running():
            self.macro.stop()

            # Wait for macro thread to actually stop (max 2 seconds)
            import time
            for _ in range(20):  # 20 * 0.1s = 2s max
                if not self.macro.is_running():
                    break
                time.sleep(0.1)

        logger.info("프로그램 종료")

        # Release single instance lock
        release_single_instance()

        # End session
        self.stats_collector.end_session()

        # Stop hotkey listener
        self.hotkey_listener.stop()

        # Stop system tray
        if self.system_tray:
            self.system_tray.stop()

        # Destroy log panels first to stop logging handlers
        # This prevents background threads from trying to log during shutdown
        try:
            self.system_log_panel.destroy()
        except Exception:
            pass
        try:
            self.info_log_panel.destroy()
        except Exception:
            pass

        # Destroy chart widgets to release matplotlib resources
        try:
            self.bar_chart.destroy()
        except Exception:
            pass

        # Small delay to let any pending after() callbacks complete
        try:
            self.root.update()
        except tk.TclError:
            pass

        # Close window
        self.root.destroy()

    def run(self) -> None:
        """Run the application"""
        logger.info("GUI 메인 루프 시작")

        # Start GUI update loop (must be called when mainloop is ready)
        # This is critical for macOS app bundles - calling after() before
        # mainloop causes NSUpdateCycleInitialize crash
        self._start_update_loop()

        # Bring window to front on startup
        self._bring_to_front()

        self.root.mainloop()


def main():
    """Entry point for GUI application"""
    app = MacroApp()
    app.run()


if __name__ == "__main__":
    main()
