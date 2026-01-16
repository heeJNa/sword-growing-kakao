"""Main GUI Application"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from pathlib import Path
from typing import Optional

from .widgets.status_panel import StatusPanel
from .widgets.stats_panel import StatsPanel
from .widgets.log_panel import LogPanel
from .widgets.control_panel import ControlPanel
from .widgets.system_log_panel import SystemLogPanel
from .charts.bar_chart import LevelProbabilityChart
from .charts.line_chart import GoldHistoryChart
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

# Logger for this module
logger = get_logger(__name__)

# Try to import system tray (optional dependency)
try:
    from .system_tray import SystemTray
    HAS_SYSTEM_TRAY = True
except ImportError:
    HAS_SYSTEM_TRAY = False


class MacroApp:
    """Main GUI Application for the sword enhancement macro"""

    def __init__(self):
        logger.info("검키우기 매크로 시작")

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
        self.root.geometry("950x750")
        self.root.minsize(900, 700)

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

        # Start GUI update loop
        self._start_update_loop()

        # Handle window close (minimize to tray)
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

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

        # Control panel (always visible at bottom)
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.control_panel = ControlPanel(control_frame)
        self.control_panel.pack()

        # Setup control callbacks
        self.control_panel.set_callbacks(
            on_start=self._on_start,
            on_pause=self._on_pause,
            on_stop=self._on_stop,
            on_settings=self._on_settings,
            on_export=self._on_export,
            on_enhance=self._on_manual_enhance,
            on_sell=self._on_manual_sell,
            on_calibrate=self._on_calibration,
        )

        # Menu bar
        self._setup_menu()

    def _setup_dashboard(self, parent) -> None:
        """Setup dashboard tab content"""
        # Top section - status and charts
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill="both", expand=True)

        # Left panel - status and stats
        left_frame = ttk.Frame(top_frame, width=250)
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        left_frame.pack_propagate(False)

        self.status_panel = StatusPanel(left_frame)
        self.status_panel.pack(fill="x", pady=(0, 10))

        self.stats_panel = StatsPanel(left_frame)
        self.stats_panel.pack(fill="x")

        # Right panel - charts
        right_frame = ttk.Frame(top_frame)
        right_frame.pack(side="left", fill="both", expand=True)

        # Bar chart
        chart_frame1 = ttk.LabelFrame(right_frame, text="레벨별 확률")
        chart_frame1.pack(fill="both", expand=True, pady=(0, 5))
        self.bar_chart = LevelProbabilityChart(chart_frame1)

        # Line chart
        chart_frame2 = ttk.LabelFrame(right_frame, text="골드 변화")
        chart_frame2.pack(fill="both", expand=True, pady=(5, 0))
        self.line_chart = GoldHistoryChart(chart_frame2)

        # Bottom section - enhancement log
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(fill="x", pady=(10, 0))

        self.log_panel = LogPanel(bottom_frame)
        self.log_panel.pack(fill="x")

    def _setup_system_tray(self) -> None:
        """Setup system tray for minimize to tray"""
        self.system_tray = None
        if HAS_SYSTEM_TRAY:
            try:
                self.system_tray = SystemTray(
                    on_show=self._show_window,
                    on_quit=self._on_quit,
                    on_start=self._on_start,
                    on_stop=self._on_stop,
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
        """Start periodic GUI update"""
        self._update_gui()

    def _update_gui(self) -> None:
        """Periodic GUI update"""
        # Update status panel
        self.status_panel.update_state(self.macro.game_state)

        # Update stats panel if session exists
        if self.stats_collector.session:
            self.stats_panel.update_stats(self.stats_collector.session)

            # Update charts (less frequently)
            level_stats = self.stats_collector.get_all_level_stats()
            self.bar_chart.update(level_stats)

            history = self.stats_collector.get_recent_history(50)
            starting = self.stats_collector.session.starting_gold
            self.line_chart.update(history, starting)

        # Schedule next update
        self.root.after(self.settings.gui_update_interval, self._update_gui)

    # === Callbacks ===

    def _on_state_change(self, state: GameState) -> None:
        """Handle game state change"""
        logger.debug(f"상태 변경: level={state.level}, gold={state.gold}")

    def _on_result(self, result: EnhanceResult) -> None:
        """Handle enhancement result"""
        logger.info(f"강화 결과: {result.value}")
        if self.stats_collector.session:
            history = self.stats_collector.get_recent_history(1)
            if history:
                self.log_panel.add_record(history[0])

    def _on_status_change(self, status: MacroState) -> None:
        """Handle macro status change"""
        logger.info(f"매크로 상태: {status.value}")
        self.status_panel.update_macro_state(status)
        self.control_panel.set_running(status == MacroState.RUNNING)
        self.control_panel.set_paused(status == MacroState.PAUSED)

    def _on_error(self, error: Exception) -> None:
        """Handle error"""
        logger.error(f"오류 발생: {error}")
        self.root.after(0, lambda: messagebox.showerror("오류", str(error)))

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
        """ESC: Emergency stop"""
        logger.warning("긴급 정지!")
        self.macro.stop()
        self.root.after(0, lambda: messagebox.showwarning("긴급 정지", "매크로가 긴급 정지되었습니다."))

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
"""
        messagebox.showinfo("단축키 안내", help_text)

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

    def _show_window(self) -> None:
        """Show window from system tray"""
        logger.info("창 복원")
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _on_quit(self) -> None:
        """Handle actual quit"""
        if self.macro.is_running():
            if not messagebox.askyesno("종료", "매크로가 실행 중입니다. 종료하시겠습니까?"):
                return
            self.macro.stop()

        logger.info("프로그램 종료")

        # End session
        self.stats_collector.end_session()

        # Stop hotkey listener
        self.hotkey_listener.stop()

        # Stop system tray
        if self.system_tray:
            self.system_tray.stop()

        # Close window
        self.root.destroy()

    def run(self) -> None:
        """Run the application"""
        logger.info("GUI 메인 루프 시작")
        self.root.mainloop()


def main():
    """Entry point for GUI application"""
    app = MacroApp()
    app.run()


if __name__ == "__main__":
    main()
