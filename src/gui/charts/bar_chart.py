"""Bar chart showing level probability distribution"""
import sys
import tkinter as tk
from typing import Dict
import numpy as np

try:
    import matplotlib
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

from ...stats.models import LevelStats


class LevelProbabilityChart:
    """Bar chart showing success/maintain/destroy rates by level"""

    def __init__(self, parent: tk.Frame):
        self.parent = parent

        if not MATPLOTLIB_AVAILABLE:
            # Fallback label if matplotlib not available
            self.label = tk.Label(parent, text="차트 표시 불가 (matplotlib 필요)")
            self.label.pack(fill="both", expand=True)
            self.canvas = None
            return

        # Create matplotlib figure
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Colors
        self.colors = {
            'success': '#4CAF50',
            'maintain': '#FFC107',
            'destroy': '#F44336',
        }

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
        self.ax.set_title('레벨별 강화 확률', fontsize=10)
        self.canvas.draw()

    def update(self, level_stats: Dict[int, LevelStats]) -> None:
        """Update chart with level statistics"""
        if self.canvas is None:
            return

        self.ax.clear()

        if not level_stats:
            self._draw_empty()
            return

        # Prepare data
        levels = sorted(level_stats.keys())
        x = np.arange(len(levels))
        width = 0.25

        success_rates = [level_stats[l].success_rate * 100 for l in levels]
        maintain_rates = [level_stats[l].maintain_rate * 100 for l in levels]
        destroy_rates = [level_stats[l].destroy_rate * 100 for l in levels]

        # Draw bars
        self.ax.bar(
            x - width, success_rates, width,
            label='성공', color=self.colors['success']
        )
        self.ax.bar(
            x, maintain_rates, width,
            label='유지', color=self.colors['maintain']
        )
        self.ax.bar(
            x + width, destroy_rates, width,
            label='파괴', color=self.colors['destroy']
        )

        # Configure axes
        self.ax.set_xlabel('강화 레벨', fontsize=9)
        self.ax.set_ylabel('확률 (%)', fontsize=9)
        self.ax.set_title('레벨별 강화 결과 분포', fontsize=10)
        self.ax.set_xticks(x)
        self.ax.set_xticklabels([f'+{l}' for l in levels], fontsize=8)
        self.ax.legend(fontsize=8)
        self.ax.set_ylim(0, 100)

        # Tight layout
        self.figure.tight_layout()
        self.canvas.draw()
