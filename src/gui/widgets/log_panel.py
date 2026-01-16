"""Log panel widget showing recent enhancement history"""
import tkinter as tk
from tkinter import ttk
from typing import List
from ...stats.models import EnhanceRecord
from ...core.state import EnhanceResult


class LogPanel(ttk.LabelFrame):
    """Panel showing recent enhancement log"""

    def __init__(self, parent):
        super().__init__(parent, text="최근 기록", padding=5)

        # Create treeview for log
        columns = ("time", "level", "result", "gold")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=8)

        # Configure columns
        self.tree.heading("time", text="시간")
        self.tree.heading("level", text="레벨")
        self.tree.heading("result", text="결과")
        self.tree.heading("gold", text="골드 변화")

        self.tree.column("time", width=80, anchor="center")
        self.tree.column("level", width=80, anchor="center")
        self.tree.column("result", width=80, anchor="center")
        self.tree.column("gold", width=100, anchor="e")

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Layout
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Tags for coloring
        self.tree.tag_configure("success", foreground="green")
        self.tree.tag_configure("maintain", foreground="orange")
        self.tree.tag_configure("destroy", foreground="red")

    def add_record(self, record: EnhanceRecord) -> None:
        """Add a single record to the log"""
        time_str = record.timestamp.strftime("%H:%M:%S")
        level_str = f"+{record.level}강"

        result_str = record.result.display_name
        result_emoji = record.result.emoji

        gold_change = record.gold_change
        gold_str = f"{gold_change:+,}원"

        # Determine tag
        tag = record.result.value

        # Insert at top
        self.tree.insert("", 0, values=(
            time_str,
            level_str,
            f"{result_emoji} {result_str}",
            gold_str
        ), tags=(tag,))

        # Limit to 100 entries
        children = self.tree.get_children()
        if len(children) > 100:
            for child in children[100:]:
                self.tree.delete(child)

    def update_records(self, records: List[EnhanceRecord]) -> None:
        """Update log with list of records"""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add records (most recent first)
        for record in reversed(records):
            self.add_record(record)

    def clear(self) -> None:
        """Clear all log entries"""
        for item in self.tree.get_children():
            self.tree.delete(item)
