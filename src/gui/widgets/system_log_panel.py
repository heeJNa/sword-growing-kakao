"""System log panel widget showing application logs in real-time"""
import tkinter as tk
from tkinter import ttk, filedialog
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from ...utils.logger import LOG_DIR, get_log_file


class TextHandler(logging.Handler):
    """Logging handler that writes to a Tkinter Text widget"""

    def __init__(self, text_widget: tk.Text):
        super().__init__()
        self.text_widget = text_widget

        # Formatter
        self.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%H:%M:%S"
        ))

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text_widget.configure(state="normal")
            self.text_widget.insert(tk.END, msg + "\n")

            # Auto-scroll to bottom
            self.text_widget.see(tk.END)

            # Apply tag based on level
            line_start = self.text_widget.index(f"end-2l linestart")
            line_end = self.text_widget.index(f"end-1l lineend")

            if record.levelno >= logging.ERROR:
                self.text_widget.tag_add("error", line_start, line_end)
            elif record.levelno >= logging.WARNING:
                self.text_widget.tag_add("warning", line_start, line_end)
            elif record.levelno >= logging.INFO:
                self.text_widget.tag_add("info", line_start, line_end)
            else:
                self.text_widget.tag_add("debug", line_start, line_end)

            # Limit to 1000 lines
            line_count = int(self.text_widget.index("end-1c").split(".")[0])
            if line_count > 1000:
                self.text_widget.delete("1.0", f"{line_count - 1000}.0")

            self.text_widget.configure(state="disabled")

        # Schedule in main thread
        self.text_widget.after(0, append)


class SystemLogPanel(ttk.Frame):
    """Panel showing system logs"""

    def __init__(self, parent):
        super().__init__(parent, padding=5)

        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 5))

        ttk.Label(toolbar, text="시스템 로그", font=("", 10, "bold")).pack(side="left")

        # Log level filter
        ttk.Label(toolbar, text="레벨:").pack(side="left", padx=(20, 5))
        self.level_var = tk.StringVar(value="DEBUG")
        level_combo = ttk.Combobox(
            toolbar,
            textvariable=self.level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            width=10,
            state="readonly"
        )
        level_combo.pack(side="left")
        level_combo.bind("<<ComboboxSelected>>", self._on_level_change)

        # Buttons
        ttk.Button(
            toolbar,
            text="지우기",
            command=self._clear_log,
            width=8
        ).pack(side="right", padx=2)

        ttk.Button(
            toolbar,
            text="저장",
            command=self._save_log,
            width=8
        ).pack(side="right", padx=2)

        ttk.Button(
            toolbar,
            text="로그 폴더 열기",
            command=self._open_log_folder,
            width=12
        ).pack(side="right", padx=2)

        # Log text widget
        log_frame = ttk.Frame(self)
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_frame,
            wrap="none",
            font=("Consolas", 9),
            state="disabled",
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white"
        )

        # Scrollbars
        v_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        h_scroll = ttk.Scrollbar(log_frame, orient="horizontal", command=self.log_text.xview)
        self.log_text.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # Grid layout
        self.log_text.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        # Configure tags for coloring
        self.log_text.tag_configure("error", foreground="#f44747")
        self.log_text.tag_configure("warning", foreground="#cca700")
        self.log_text.tag_configure("info", foreground="#4fc1ff")
        self.log_text.tag_configure("debug", foreground="#808080")

        # Setup logging handler
        self._handler: Optional[TextHandler] = None
        self._setup_logging()

        # Status bar
        status_frame = ttk.Frame(self)
        status_frame.pack(fill="x", pady=(5, 0))

        self.status_label = ttk.Label(
            status_frame,
            text=f"로그 파일: {get_log_file()}",
            foreground="gray"
        )
        self.status_label.pack(side="left")

    def _setup_logging(self) -> None:
        """Setup logging handler to capture logs"""
        self._handler = TextHandler(self.log_text)
        self._handler.setLevel(logging.DEBUG)

        # Add handler to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(self._handler)

        # Also add to our app loggers
        for logger_name in ["src", "__main__"]:
            logger = logging.getLogger(logger_name)
            if self._handler not in logger.handlers:
                logger.addHandler(self._handler)

    def _on_level_change(self, event=None) -> None:
        """Handle log level filter change"""
        level_name = self.level_var.get()
        level = getattr(logging, level_name, logging.DEBUG)
        if self._handler:
            self._handler.setLevel(level)

    def _clear_log(self) -> None:
        """Clear log display"""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

    def _save_log(self) -> None:
        """Save current log to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"log_export_{timestamp}.txt"

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")],
            initialfile=default_name
        )

        if path:
            content = self.log_text.get("1.0", tk.END)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

    def _open_log_folder(self) -> None:
        """Open log folder in file explorer"""
        import subprocess
        import sys

        if sys.platform == "darwin":
            subprocess.run(["open", str(LOG_DIR)])
        elif sys.platform == "win32":
            subprocess.run(["explorer", str(LOG_DIR)])
        else:
            subprocess.run(["xdg-open", str(LOG_DIR)])

    def add_log(self, message: str, level: str = "INFO") -> None:
        """Manually add a log message"""
        logger = logging.getLogger("gui")
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)

    def destroy(self) -> None:
        """Clean up when widget is destroyed"""
        if self._handler:
            root_logger = logging.getLogger()
            root_logger.removeHandler(self._handler)
        super().destroy()
