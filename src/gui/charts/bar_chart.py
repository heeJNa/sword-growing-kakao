"""Bar chart showing level probability distribution"""
import sys
import tkinter as tk
from typing import Dict, List, Optional
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

        # Store bars for hover detection
        self._all_bars: List = []
        self._bar_info: Dict = {}  # bar -> (level, type, value)

        # Tooltip annotation
        self._tooltip = None

        # Connect hover event
        self.canvas.mpl_connect('motion_notify_event', self._on_hover)

        # Initial empty chart
        self._draw_empty()

    def _draw_empty(self) -> None:
        """Draw empty chart without placeholder text"""
        if self.canvas is None:
            return

        self.ax.clear()
        self.ax.set_title('레벨별 강화 결과 분포', fontsize=10)
        self.ax.set_xlabel('강화 레벨', fontsize=9)
        self.ax.set_ylabel('확률 (%)', fontsize=9)
        self.ax.set_ylim(0, 110)
        self.ax.set_xlim(-1, 20)
        self.canvas.draw()

    def update(self, level_stats: Dict[int, LevelStats]) -> None:
        """Update chart with level statistics"""
        if self.canvas is None:
            return

        self.ax.clear()
        self._all_bars = []
        self._bar_info = {}

        if not level_stats:
            self._draw_empty()
            return

        # Fixed X-axis: levels 1-20
        all_levels = list(range(1, 21))
        x = np.arange(len(all_levels))
        width = 0.25

        # Get rates for all levels (0 if no data)
        success_rates = []
        maintain_rates = []
        destroy_rates = []

        for level in all_levels:
            if level in level_stats:
                stats = level_stats[level]
                success_rates.append(stats.success_rate * 100)
                maintain_rates.append(stats.maintain_rate * 100)
                destroy_rates.append(stats.destroy_rate * 100)
            else:
                success_rates.append(0)
                maintain_rates.append(0)
                destroy_rates.append(0)

        # Draw bars
        bars_success = self.ax.bar(
            x - width, success_rates, width,
            label='성공', color=self.colors['success']
        )
        bars_maintain = self.ax.bar(
            x, maintain_rates, width,
            label='유지', color=self.colors['maintain']
        )
        bars_destroy = self.ax.bar(
            x + width, destroy_rates, width,
            label='파괴', color=self.colors['destroy']
        )

        # Store bar info for hover tooltip
        for i, level in enumerate(all_levels):
            if success_rates[i] > 0:
                self._bar_info[bars_success[i]] = (level, '성공', success_rates[i])
                self._all_bars.append(bars_success[i])
            if maintain_rates[i] > 0:
                self._bar_info[bars_maintain[i]] = (level, '유지', maintain_rates[i])
                self._all_bars.append(bars_maintain[i])
            if destroy_rates[i] > 0:
                self._bar_info[bars_destroy[i]] = (level, '파괴', destroy_rates[i])
                self._all_bars.append(bars_destroy[i])

        # Configure axes
        self.ax.set_xlabel('강화 레벨', fontsize=9)
        self.ax.set_ylabel('확률 (%)', fontsize=9)
        self.ax.set_title('레벨별 강화 결과 분포', fontsize=10)

        # X-axis: set ticks at bar group centers, align labels properly
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(
            [f'+{l}' for l in all_levels],
            fontsize=7,
            rotation=45,
            ha='right'  # Align rotated labels to the right for proper positioning
        )

        self.ax.legend(fontsize=8, loc='upper right')
        self.ax.set_ylim(0, 105)  # Slightly less headroom without labels
        self.ax.set_xlim(-1, 20)  # More left/right margin

        # Tight layout with padding
        self.figure.tight_layout(pad=1.5)
        self.canvas.draw()

    def _on_hover(self, event) -> None:
        """Handle mouse hover to show tooltip"""
        if self.canvas is None or event.inaxes != self.ax:
            # Remove tooltip when outside axes
            if self._tooltip is not None:
                self._tooltip.remove()
                self._tooltip = None
                self.canvas.draw_idle()
            return

        # Check if mouse is over any bar
        for bar in self._all_bars:
            if bar.contains(event)[0]:
                level, bar_type, value = self._bar_info[bar]

                # Remove old tooltip
                if self._tooltip is not None:
                    self._tooltip.remove()

                # Create new tooltip
                self._tooltip = self.ax.annotate(
                    f'+{level}강 {bar_type}: {value:.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 10),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=9,
                    color='white',
                    bbox=dict(
                        boxstyle='round,pad=0.3',
                        facecolor='#333333',
                        edgecolor='#555555',
                        alpha=1.0
                    )
                )
                self.canvas.draw_idle()
                return

        # No bar under mouse - remove tooltip
        if self._tooltip is not None:
            self._tooltip.remove()
            self._tooltip = None
            self.canvas.draw_idle()
