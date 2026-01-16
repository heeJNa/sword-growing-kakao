"""Statistics panel widget showing session stats"""
import tkinter as tk
from tkinter import ttk
from ...stats.models import SessionStats


class StatsPanel(ttk.LabelFrame):
    """Panel showing session statistics"""

    def __init__(self, parent):
        super().__init__(parent, text="세션 통계", padding=10)

        # Total enhances
        self.enhance_label = ttk.Label(self, text="총 강화:", font=("", 10))
        self.enhance_label.grid(row=0, column=0, sticky="w", pady=2)

        self.enhance_value = ttk.Label(self, text="0회", font=("", 12))
        self.enhance_value.grid(row=0, column=1, sticky="e", pady=2)

        # Total sells
        self.sell_label = ttk.Label(self, text="총 판매:", font=("", 10))
        self.sell_label.grid(row=1, column=0, sticky="w", pady=2)

        self.sell_value = ttk.Label(self, text="0회", font=("", 12))
        self.sell_value.grid(row=1, column=1, sticky="e", pady=2)

        # Success rate
        self.success_label = ttk.Label(self, text="성공률:", font=("", 10))
        self.success_label.grid(row=2, column=0, sticky="w", pady=2)

        self.success_value = ttk.Label(self, text="0%", font=("", 12))
        self.success_value.grid(row=2, column=1, sticky="e", pady=2)

        # Profit
        self.profit_label = ttk.Label(self, text="수익:", font=("", 10))
        self.profit_label.grid(row=3, column=0, sticky="w", pady=2)

        self.profit_value = ttk.Label(self, text="0원", font=("", 12, "bold"))
        self.profit_value.grid(row=3, column=1, sticky="e", pady=2)

        # ROI
        self.roi_label = ttk.Label(self, text="ROI:", font=("", 10))
        self.roi_label.grid(row=4, column=0, sticky="w", pady=2)

        self.roi_value = ttk.Label(self, text="0%", font=("", 12))
        self.roi_value.grid(row=4, column=1, sticky="e", pady=2)

        # Max level
        ttk.Separator(self, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)

        self.max_label = ttk.Label(self, text="최고 레벨:", font=("", 10))
        self.max_label.grid(row=6, column=0, sticky="w", pady=2)

        self.max_value = ttk.Label(self, text="+0강", font=("", 12))
        self.max_value.grid(row=6, column=1, sticky="e", pady=2)

        # Duration
        self.duration_label = ttk.Label(self, text="실행 시간:", font=("", 10))
        self.duration_label.grid(row=7, column=0, sticky="w", pady=2)

        self.duration_value = ttk.Label(self, text="0분", font=("", 12))
        self.duration_value.grid(row=7, column=1, sticky="e", pady=2)

        # Configure column weights
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

    def update_stats(self, stats: SessionStats) -> None:
        """Update display with session statistics"""
        self.enhance_value.config(text=f"{stats.total_enhances}회")
        self.sell_value.config(text=f"{stats.total_sells}회")
        self.success_value.config(text=f"{stats.total_success_rate * 100:.1f}%")

        # Profit with color
        profit = stats.profit
        profit_text = f"{profit:+,}원"
        profit_color = "green" if profit >= 0 else "red"
        self.profit_value.config(text=profit_text, foreground=profit_color)

        # ROI
        roi_text = f"{stats.roi_percent:+.1f}%"
        self.roi_value.config(text=roi_text)

        # Max level
        self.max_value.config(text=f"+{stats.max_level_reached}강")

        # Duration
        minutes = int(stats.duration_minutes)
        self.duration_value.config(text=f"{minutes}분")
