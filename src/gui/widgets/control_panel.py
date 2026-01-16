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

        # Start button
        self.start_btn = ttk.Button(
            self,
            text="▶ 시작",
            command=self._handle_start,
            width=10
        )
        self.start_btn.pack(side="left", padx=5)

        # Pause button
        self.pause_btn = ttk.Button(
            self,
            text="⏸ 일시정지",
            command=self._handle_pause,
            width=10,
            state="disabled"
        )
        self.pause_btn.pack(side="left", padx=5)

        # Stop button
        self.stop_btn = ttk.Button(
            self,
            text="■ 정지",
            command=self._handle_stop,
            width=10,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)

        # Separator
        ttk.Separator(self, orient="vertical").pack(side="left", fill="y", padx=10)

        # Settings button
        self.settings_btn = ttk.Button(
            self,
            text="⚙ 설정",
            command=self._handle_settings,
            width=10
        )
        self.settings_btn.pack(side="left", padx=5)

        # Export button
        self.export_btn = ttk.Button(
            self,
            text="📊 내보내기",
            command=self._handle_export,
            width=10
        )
        self.export_btn.pack(side="left", padx=5)

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
    ) -> None:
        """Set callback functions for buttons"""
        self._on_start = on_start
        self._on_pause = on_pause
        self._on_stop = on_stop
        self._on_settings = on_settings
        self._on_export = on_export

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

    def set_running(self, running: bool) -> None:
        """Update button states for running mode"""
        self._is_running = running

        if running:
            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="normal", text="⏸ 일시정지")
            self.stop_btn.config(state="normal")
            self.settings_btn.config(state="disabled")
        else:
            self.start_btn.config(state="normal")
            self.pause_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")
            self.settings_btn.config(state="normal")

    def set_paused(self, paused: bool) -> None:
        """Update button states for paused mode"""
        self._is_paused = paused

        if paused:
            self.pause_btn.config(text="▶ 재개")
        else:
            self.pause_btn.config(text="⏸ 일시정지")
