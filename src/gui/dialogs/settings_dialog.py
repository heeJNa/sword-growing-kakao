"""Settings dialog for configuring macro parameters"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from ...config.settings import Settings


class SettingsDialog:
    """Dialog for configuring macro settings"""

    def __init__(self, parent, settings: Settings, on_save: Callable[[Settings], None] = None):
        self.parent = parent
        self.settings = settings
        self.on_save = on_save

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("설정")
        self.dialog.geometry("400x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Create notebook for tabs
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Strategy tab
        strategy_frame = ttk.Frame(notebook, padding=10)
        notebook.add(strategy_frame, text="전략")
        self._create_strategy_tab(strategy_frame)

        # Timing tab
        timing_frame = ttk.Frame(notebook, padding=10)
        notebook.add(timing_frame, text="타이밍")
        self._create_timing_tab(timing_frame)

        # Button frame
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="저장", command=self._save).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="취소", command=self.dialog.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="기본값", command=self._reset_defaults).pack(side="left", padx=5)

    def _create_strategy_tab(self, parent) -> None:
        """Create strategy settings tab"""
        # Target level
        ttk.Label(parent, text="목표 판매 레벨:").grid(row=0, column=0, sticky="w", pady=5)
        self.target_level = ttk.Spinbox(parent, from_=1, to=20, width=10)
        self.target_level.set(self.settings.level_threshold)
        self.target_level.grid(row=0, column=1, sticky="e", pady=5)

        # Max fails
        ttk.Label(parent, text="최대 연속 실패 횟수:").grid(row=1, column=0, sticky="w", pady=5)
        self.max_fails = ttk.Spinbox(parent, from_=1, to=10, width=10)
        self.max_fails.set(self.settings.max_fails)
        self.max_fails.grid(row=1, column=1, sticky="e", pady=5)

        # Min gold
        ttk.Label(parent, text="최소 필요 골드:").grid(row=2, column=0, sticky="w", pady=5)
        self.min_gold = ttk.Entry(parent, width=15)
        self.min_gold.insert(0, str(self.settings.min_gold))
        self.min_gold.grid(row=2, column=1, sticky="e", pady=5)

        # Max level
        ttk.Label(parent, text="최대 강화 레벨:").grid(row=3, column=0, sticky="w", pady=5)
        self.max_level = ttk.Spinbox(parent, from_=10, to=20, width=10)
        self.max_level.set(self.settings.max_level)
        self.max_level.grid(row=3, column=1, sticky="e", pady=5)

        # Auto sell options
        ttk.Separator(parent, orient="horizontal").grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)

        self.auto_threshold = tk.BooleanVar(value=self.settings.auto_sell_on_threshold)
        ttk.Checkbutton(
            parent,
            text="목표 레벨 도달 시 자동 판매",
            variable=self.auto_threshold
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=5)

        self.auto_fails = tk.BooleanVar(value=self.settings.auto_sell_on_max_fails)
        ttk.Checkbutton(
            parent,
            text="최대 실패 횟수 도달 시 자동 판매",
            variable=self.auto_fails
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=5)

        # Configure columns
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

    def _create_timing_tab(self, parent) -> None:
        """Create timing settings tab"""
        # Action delay
        ttk.Label(parent, text="행동 간 딜레이 (초):").grid(row=0, column=0, sticky="w", pady=5)
        self.action_delay = ttk.Entry(parent, width=10)
        self.action_delay.insert(0, str(self.settings.action_delay))
        self.action_delay.grid(row=0, column=1, sticky="e", pady=5)

        # Click delay
        ttk.Label(parent, text="클릭 딜레이 (초):").grid(row=1, column=0, sticky="w", pady=5)
        self.click_delay = ttk.Entry(parent, width=10)
        self.click_delay.insert(0, str(self.settings.click_delay))
        self.click_delay.grid(row=1, column=1, sticky="e", pady=5)

        # Type delay
        ttk.Label(parent, text="타이핑 딜레이 (초):").grid(row=2, column=0, sticky="w", pady=5)
        self.type_delay = ttk.Entry(parent, width=10)
        self.type_delay.insert(0, str(self.settings.type_delay))
        self.type_delay.grid(row=2, column=1, sticky="e", pady=5)

        # Response timeout
        ttk.Label(parent, text="응답 타임아웃 (초):").grid(row=3, column=0, sticky="w", pady=5)
        self.response_timeout = ttk.Entry(parent, width=10)
        self.response_timeout.insert(0, str(self.settings.response_timeout))
        self.response_timeout.grid(row=3, column=1, sticky="e", pady=5)

        # Note
        ttk.Separator(parent, orient="horizontal").grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Label(
            parent,
            text="⚠️ 딜레이를 너무 낮추면 오작동이 발생할 수 있습니다.",
            foreground="orange"
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=5)

        # Configure columns
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

    def _save(self) -> None:
        """Save settings"""
        try:
            # Update settings from inputs
            self.settings.level_threshold = int(self.target_level.get())
            self.settings.max_fails = int(self.max_fails.get())
            self.settings.min_gold = int(self.min_gold.get())
            self.settings.max_level = int(self.max_level.get())
            self.settings.auto_sell_on_threshold = self.auto_threshold.get()
            self.settings.auto_sell_on_max_fails = self.auto_fails.get()

            self.settings.action_delay = float(self.action_delay.get())
            self.settings.click_delay = float(self.click_delay.get())
            self.settings.type_delay = float(self.type_delay.get())
            self.settings.response_timeout = float(self.response_timeout.get())

            # Save to file
            self.settings.save()

            # Call callback
            if self.on_save:
                self.on_save(self.settings)

            self.dialog.destroy()
            messagebox.showinfo("설정", "설정이 저장되었습니다.")

        except ValueError as e:
            messagebox.showerror("오류", f"잘못된 값이 있습니다: {e}")

    def _reset_defaults(self) -> None:
        """Reset to default values"""
        defaults = Settings()

        self.target_level.delete(0, tk.END)
        self.target_level.insert(0, str(defaults.level_threshold))

        self.max_fails.delete(0, tk.END)
        self.max_fails.insert(0, str(defaults.max_fails))

        self.min_gold.delete(0, tk.END)
        self.min_gold.insert(0, str(defaults.min_gold))

        self.max_level.delete(0, tk.END)
        self.max_level.insert(0, str(defaults.max_level))

        self.action_delay.delete(0, tk.END)
        self.action_delay.insert(0, str(defaults.action_delay))

        self.click_delay.delete(0, tk.END)
        self.click_delay.insert(0, str(defaults.click_delay))

        self.type_delay.delete(0, tk.END)
        self.type_delay.insert(0, str(defaults.type_delay))

        self.response_timeout.delete(0, tk.END)
        self.response_timeout.insert(0, str(defaults.response_timeout))

        self.auto_threshold.set(defaults.auto_sell_on_threshold)
        self.auto_fails.set(defaults.auto_sell_on_max_fails)
