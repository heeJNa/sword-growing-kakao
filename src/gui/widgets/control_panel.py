"""Control panel widget with action buttons"""
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class ControlPanel(ttk.Frame):
    """Panel with control buttons for the macro"""

    def __init__(self, parent):
        super().__init__(parent, padding=5)

        # Callbacks
        self._on_start: Optional[Callable] = None
        self._on_pause: Optional[Callable] = None
        self._on_stop: Optional[Callable] = None
        self._on_settings: Optional[Callable] = None
        self._on_export: Optional[Callable] = None
        self._on_enhance: Optional[Callable] = None
        self._on_sell: Optional[Callable] = None
        self._on_calibrate: Optional[Callable] = None

        # === 자동 모드 버튼 ===
        auto_frame = ttk.LabelFrame(self, text="자동 모드", padding=5)
        auto_frame.pack(side="left", padx=5)

        # Start button
        self.start_btn = ttk.Button(
            auto_frame,
            text="▶ 시작",
            command=self._handle_start,
            width=10
        )
        self.start_btn.pack(side="left", padx=2)

        # Pause button
        self.pause_btn = ttk.Button(
            auto_frame,
            text="⏸ 일시정지",
            command=self._handle_pause,
            width=10,
            state="disabled"
        )
        self.pause_btn.pack(side="left", padx=2)

        # Stop button
        self.stop_btn = ttk.Button(
            auto_frame,
            text="■ 정지",
            command=self._handle_stop,
            width=10,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=2)

        # === 수동 모드 버튼 ===
        manual_frame = ttk.LabelFrame(self, text="수동 모드", padding=5)
        manual_frame.pack(side="left", padx=5)

        # Enhance button
        self.enhance_btn = ttk.Button(
            manual_frame,
            text="⚔ 강화",
            command=self._handle_enhance,
            width=8
        )
        self.enhance_btn.pack(side="left", padx=2)

        # Sell button
        self.sell_btn = ttk.Button(
            manual_frame,
            text="💰 판매",
            command=self._handle_sell,
            width=8
        )
        self.sell_btn.pack(side="left", padx=2)

        # === 설정 버튼 ===
        settings_frame = ttk.LabelFrame(self, text="설정", padding=5)
        settings_frame.pack(side="left", padx=5)

        # Settings button
        self.settings_btn = ttk.Button(
            settings_frame,
            text="⚙ 전략",
            command=self._handle_settings,
            width=8
        )
        self.settings_btn.pack(side="left", padx=2)

        # Calibrate button
        self.calibrate_btn = ttk.Button(
            settings_frame,
            text="🎯 좌표",
            command=self._handle_calibrate,
            width=8
        )
        self.calibrate_btn.pack(side="left", padx=2)

        # Export button
        self.export_btn = ttk.Button(
            settings_frame,
            text="📊 내보내기",
            command=self._handle_export,
            width=10
        )
        self.export_btn.pack(side="left", padx=2)

        # State tracking
        self._is_running = False
        self._is_paused = False

    def set_callbacks(
        self,
        on_start: Callable = None,
        on_pause: Callable = None,
        on_stop: Callable = None,
        on_settings: Callable = None,
        on_export: Callable = None,
        on_enhance: Callable = None,
        on_sell: Callable = None,
        on_calibrate: Callable = None,
    ) -> None:
        """Set callback functions for buttons"""
        self._on_start = on_start
        self._on_pause = on_pause
        self._on_stop = on_stop
        self._on_settings = on_settings
        self._on_export = on_export
        self._on_enhance = on_enhance
        self._on_sell = on_sell
        self._on_calibrate = on_calibrate

    def _handle_start(self) -> None:
        if self._on_start:
            self._on_start()

    def _handle_pause(self) -> None:
        if self._on_pause:
            self._on_pause()

    def _handle_stop(self) -> None:
        if self._on_stop:
            self._on_stop()

    def _handle_settings(self) -> None:
        if self._on_settings:
            self._on_settings()

    def _handle_export(self) -> None:
        if self._on_export:
            self._on_export()

    def _handle_enhance(self) -> None:
        if self._on_enhance:
            self._on_enhance()

    def _handle_sell(self) -> None:
        if self._on_sell:
            self._on_sell()

    def _handle_calibrate(self) -> None:
        if self._on_calibrate:
            self._on_calibrate()

    def set_running(self, running: bool) -> None:
        """Update button states for running mode"""
        self._is_running = running

        if running:
            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="normal", text="⏸ 일시정지")
            self.stop_btn.config(state="normal")
            self.settings_btn.config(state="disabled")
            self.calibrate_btn.config(state="disabled")
            self.enhance_btn.config(state="disabled")
            self.sell_btn.config(state="disabled")
        else:
            self.start_btn.config(state="normal")
            self.pause_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")
            self.settings_btn.config(state="normal")
            self.calibrate_btn.config(state="normal")
            self.enhance_btn.config(state="normal")
            self.sell_btn.config(state="normal")

    def set_paused(self, paused: bool) -> None:
        """Update button states for paused mode"""
        self._is_paused = paused

        if paused:
            self.pause_btn.config(text="▶ 재개")
        else:
            self.pause_btn.config(text="⏸ 일시정지")
