"""Line chart showing gold history over time"""
import sys
import tkinter as tk
from typing import List
from datetime import datetime

try:
    import matplotlib
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.dates as mdates

    # Set Korean font for macOS
    if sys.platform == "darwin":
        matplotlib.rcParams['font.family'] = 'AppleGothic'
    else:
        # Windows Korean font
        matplotlib.rcParams['font.family'] = 'Malgun Gothic'
    matplotlib.rcParams['axes.unicode_minus'] = False

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from ...stats.models import EnhanceRecord


class GoldHistoryChart:
    """Line chart showing gold balance over time"""

    def __init__(self, parent: tk.Frame):
        self.parent = parent

        if not MATPLOTLIB_AVAILABLE:
            self.label = tk.Label(parent, text="차트 표시 불가 (matplotlib 필요)")
            self.label.pack(fill="both", expand=True)
            self.canvas = None
            return

        # Create matplotlib figure
        self.figure = Figure(figsize=(6, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Initial empty chart
        self._draw_empty()

    def _draw_empty(self) -> None:
        """Draw empty chart with placeholder text"""
        if self.canvas is None:
            return

        self.ax.clear()
        self.ax.text(
            0.5, 0.5, '데이터 수집 중...',
            ha='center', va='center',
            fontsize=12, color='gray',
            transform=self.ax.transAxes
        )
        self.ax.set_title('골드 변화 추이', fontsize=10)
        self.canvas.draw()

    def update(self, history: List[EnhanceRecord], starting_gold: int = 0) -> None:
        """Update chart with enhancement history"""
        if self.canvas is None:
            return

        self.ax.clear()

        if not history:
            self._draw_empty()
            return

        # Prepare data
        times = [record.timestamp for record in history]
        golds = [record.gold_after for record in history]

        # Add starting point
        if history:
            times.insert(0, history[0].timestamp)
            golds.insert(0, starting_gold or history[0].gold_before)

        # Plot line
        self.ax.plot(times, golds, 'b-', linewidth=1.5)
        self.ax.fill_between(times, golds, alpha=0.3)

        # Format x-axis
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())

        # Format y-axis
        self.ax.yaxis.set_major_formatter(
            lambda x, p: f'{x/1000:.0f}K' if x >= 1000 else f'{x:.0f}'
        )

        # Configure axes
        self.ax.set_xlabel('시간', fontsize=9)
        self.ax.set_ylabel('골드', fontsize=9)
        self.ax.set_title('골드 변화 추이', fontsize=10)
        self.ax.grid(True, alpha=0.3)

        # Rotate x labels
        for label in self.ax.get_xticklabels():
            label.set_rotation(45)
            label.set_fontsize(8)

        # Tight layout
        self.figure.tight_layout()
        self.canvas.draw()
