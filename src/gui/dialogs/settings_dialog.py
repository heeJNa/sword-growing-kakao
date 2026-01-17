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
        self.dialog.geometry("480x550")
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
        # Title
        ttk.Label(
            parent,
            text="목표 레벨까지 계속 강화합니다",
            font=("", 10, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # Target level
        ttk.Label(parent, text="목표 강화 레벨:").grid(row=1, column=0, sticky="w", pady=5)
        self.target_level = ttk.Spinbox(parent, from_=1, to=20, width=10)
        self.target_level.set(self.settings.target_level)
        self.target_level.grid(row=1, column=1, sticky="e", pady=5)

        # Min gold
        ttk.Label(parent, text="최소 필요 골드:").grid(row=2, column=0, sticky="w", pady=5)
        self.min_gold = ttk.Entry(parent, width=15)
        self.min_gold.insert(0, str(self.settings.min_gold))
        self.min_gold.grid(row=2, column=1, sticky="e", pady=5)

        # Options separator
        ttk.Separator(parent, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=15)

        ttk.Label(
            parent,
            text="목표 도달 시 동작",
            font=("", 9, "bold")
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 5))

        # Pause on target
        self.pause_on_target = tk.BooleanVar(value=self.settings.pause_on_target)
        ttk.Checkbutton(
            parent,
            text="목표 레벨 도달 시 일시정지",
            variable=self.pause_on_target
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=5)

        # Sell on target
        self.sell_on_target = tk.BooleanVar(value=self.settings.sell_on_target)
        ttk.Checkbutton(
            parent,
            text="목표 레벨 도달 시 판매 (골드 파밍용)",
            variable=self.sell_on_target
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=5)

        # Note
        ttk.Label(
            parent,
            text="💡 파괴되면 자동으로 0강부터 다시 강화합니다",
            foreground="gray"
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(15, 5))

        # Configure columns
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

    def _create_timing_tab(self, parent) -> None:
        """Create timing settings tab"""
        row = 0

        # === 기본 딜레이 섹션 ===
        ttk.Label(parent, text="기본 딜레이", font=("", 9, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 5))
        row += 1

        # Action delay
        ttk.Label(parent, text="행동 간 딜레이 (초):").grid(row=row, column=0, sticky="w", pady=3)
        self.action_delay = ttk.Entry(parent, width=10)
        self.action_delay.insert(0, str(self.settings.action_delay))
        self.action_delay.grid(row=row, column=1, sticky="e", pady=3)
        row += 1

        # Click delay
        ttk.Label(parent, text="클릭 딜레이 (초):").grid(row=row, column=0, sticky="w", pady=3)
        self.click_delay = ttk.Entry(parent, width=10)
        self.click_delay.insert(0, str(self.settings.click_delay))
        self.click_delay.grid(row=row, column=1, sticky="e", pady=3)
        row += 1

        # Type delay
        ttk.Label(parent, text="타이핑 딜레이 (초):").grid(row=row, column=0, sticky="w", pady=3)
        self.type_delay = ttk.Entry(parent, width=10)
        self.type_delay.insert(0, str(self.settings.type_delay))
        self.type_delay.grid(row=row, column=1, sticky="e", pady=3)
        row += 1

        # Response timeout
        ttk.Label(parent, text="응답 타임아웃 (초):").grid(row=row, column=0, sticky="w", pady=3)
        self.response_timeout = ttk.Entry(parent, width=10)
        self.response_timeout.insert(0, str(self.settings.response_timeout))
        self.response_timeout.grid(row=row, column=1, sticky="e", pady=3)
        row += 1

        # Separator
        ttk.Separator(parent, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1

        # === 매크로 딜레이 섹션 ===
        ttk.Label(parent, text="매크로 딜레이", font=("", 9, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 5))
        row += 1

        # Profile check delay
        ttk.Label(parent, text="프로필 확인 대기 (초):").grid(row=row, column=0, sticky="w", pady=3)
        self.profile_check_delay = ttk.Entry(parent, width=10)
        self.profile_check_delay.insert(0, str(self.settings.profile_check_delay))
        self.profile_check_delay.grid(row=row, column=1, sticky="e", pady=3)
        row += 1

        # Result check delay
        ttk.Label(parent, text="결과 확인 대기 (초):").grid(row=row, column=0, sticky="w", pady=3)
        self.result_check_delay = ttk.Entry(parent, width=10)
        self.result_check_delay.insert(0, str(self.settings.result_check_delay))
        self.result_check_delay.grid(row=row, column=1, sticky="e", pady=3)
        row += 1

        # Retry delay
        ttk.Label(parent, text="재시도 대기 (초):").grid(row=row, column=0, sticky="w", pady=3)
        self.retry_delay = ttk.Entry(parent, width=10)
        self.retry_delay.insert(0, str(self.settings.retry_delay))
        self.retry_delay.grid(row=row, column=1, sticky="e", pady=3)
        row += 1

        # Stale result delay
        ttk.Label(parent, text="오래된 결과 재확인 (초):").grid(row=row, column=0, sticky="w", pady=3)
        self.stale_result_delay = ttk.Entry(parent, width=10)
        self.stale_result_delay.insert(0, str(self.settings.stale_result_delay))
        self.stale_result_delay.grid(row=row, column=1, sticky="e", pady=3)
        row += 1

        # Note
        ttk.Separator(parent, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1
        ttk.Label(
            parent,
            text="⚠️ 딜레이를 너무 낮추면 오작동이 발생할 수 있습니다.",
            foreground="orange"
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=3)

        # Configure columns
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

    def _save(self) -> None:
        """Save settings"""
        try:
            # Update settings from inputs
            self.settings.target_level = int(self.target_level.get())
            self.settings.min_gold = int(self.min_gold.get())
            self.settings.pause_on_target = self.pause_on_target.get()
            self.settings.sell_on_target = self.sell_on_target.get()

            # Basic timing
            self.settings.action_delay = float(self.action_delay.get())
            self.settings.click_delay = float(self.click_delay.get())
            self.settings.type_delay = float(self.type_delay.get())
            self.settings.response_timeout = float(self.response_timeout.get())

            # Macro timing
            self.settings.profile_check_delay = float(self.profile_check_delay.get())
            self.settings.result_check_delay = float(self.result_check_delay.get())
            self.settings.retry_delay = float(self.retry_delay.get())
            self.settings.stale_result_delay = float(self.stale_result_delay.get())

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
        self.target_level.insert(0, str(defaults.target_level))

        self.min_gold.delete(0, tk.END)
        self.min_gold.insert(0, str(defaults.min_gold))

        # Basic timing
        self.action_delay.delete(0, tk.END)
        self.action_delay.insert(0, str(defaults.action_delay))

        self.click_delay.delete(0, tk.END)
        self.click_delay.insert(0, str(defaults.click_delay))

        self.type_delay.delete(0, tk.END)
        self.type_delay.insert(0, str(defaults.type_delay))

        self.response_timeout.delete(0, tk.END)
        self.response_timeout.insert(0, str(defaults.response_timeout))

        # Macro timing
        self.profile_check_delay.delete(0, tk.END)
        self.profile_check_delay.insert(0, str(defaults.profile_check_delay))

        self.result_check_delay.delete(0, tk.END)
        self.result_check_delay.insert(0, str(defaults.result_check_delay))

        self.retry_delay.delete(0, tk.END)
        self.retry_delay.insert(0, str(defaults.retry_delay))

        self.stale_result_delay.delete(0, tk.END)
        self.stale_result_delay.insert(0, str(defaults.stale_result_delay))

        self.pause_on_target.set(defaults.pause_on_target)
        self.sell_on_target.set(defaults.sell_on_target)
