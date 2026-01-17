"""Status panel widget showing current game state"""
from tkinter import ttk
from ...core.state import GameState, MacroState


class StatusPanel(ttk.LabelFrame):
    """Panel showing current game status"""

    def __init__(self, parent):
        super().__init__(parent, text="현재 상태", padding=10)

        # Level display
        self.level_label = ttk.Label(self, text="레벨:", font=("", 10))
        self.level_label.grid(row=0, column=0, sticky="w", pady=2)

        self.level_value = ttk.Label(self, text="+0강", font=("", 14, "bold"))
        self.level_value.grid(row=0, column=1, sticky="e", pady=2)

        # Target level display
        self.target_label = ttk.Label(self, text="목표 레벨:", font=("", 10))
        self.target_label.grid(row=1, column=0, sticky="w", pady=2)

        self.target_value = ttk.Label(self, text="+10강", font=("", 12), foreground="blue")
        self.target_value.grid(row=1, column=1, sticky="e", pady=2)

        # Gold display
        self.gold_label = ttk.Label(self, text="골드:", font=("", 10))
        self.gold_label.grid(row=2, column=0, sticky="w", pady=2)

        self.gold_value = ttk.Label(self, text="0원", font=("", 12))
        self.gold_value.grid(row=2, column=1, sticky="e", pady=2)

        # Fail count display
        self.fail_label = ttk.Label(self, text="연속 실패:", font=("", 10))
        self.fail_label.grid(row=3, column=0, sticky="w", pady=2)

        self.fail_value = ttk.Label(self, text="0회", font=("", 12))
        self.fail_value.grid(row=3, column=1, sticky="e", pady=2)

        # Last result display
        self.result_label = ttk.Label(self, text="마지막 결과:", font=("", 10))
        self.result_label.grid(row=4, column=0, sticky="w", pady=2)

        self.result_value = ttk.Label(self, text="-", font=("", 12))
        self.result_value.grid(row=4, column=1, sticky="e", pady=2)

        # Macro status display
        ttk.Separator(self, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)

        self.status_label = ttk.Label(self, text="매크로 상태:", font=("", 10))
        self.status_label.grid(row=6, column=0, sticky="w", pady=2)

        self.status_value = ttk.Label(self, text="대기 중", font=("", 12))
        self.status_value.grid(row=6, column=1, sticky="e", pady=2)

        # Configure column weights
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

    def update_state(self, state: GameState) -> None:
        """Update display with game state"""
        self.level_value.config(text=state.level_display)
        self.gold_value.config(text=state.gold_display)
        self.fail_value.config(text=f"{state.fail_count}회")

        if state.last_result:
            result_text = f"{state.last_result.emoji} {state.last_result.display_name}"
            self.result_value.config(text=result_text)
        else:
            self.result_value.config(text="-")

    def update_target_level(self, target_level: int) -> None:
        """Update target level display"""
        self.target_value.config(text=f"+{target_level}강")

    def update_macro_state(self, macro_state: MacroState) -> None:
        """Update macro status display"""
        status_map = {
            MacroState.IDLE: ("대기 중", "gray"),
            MacroState.RUNNING: ("실행 중", "green"),
            MacroState.PAUSED: ("일시정지", "orange"),
            MacroState.STOPPED: ("정지됨", "red"),
            MacroState.ERROR: ("오류!", "red"),
        }

        text, color = status_map.get(macro_state, ("알 수 없음", "gray"))
        self.status_value.config(text=text, foreground=color)
