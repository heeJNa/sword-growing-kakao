"""Info log panel widget showing INFO level logs in real-time"""
import tkinter as tk
from tkinter import ttk
import logging
import queue
from typing import Optional


class InfoTextHandler(logging.Handler):
    """
    Logging handler that writes INFO+ logs to a Tkinter Text widget.
    Thread-safe via queue.
    """

    def __init__(self, text_widget: tk.Text):
        super().__init__()
        self.text_widget = text_widget
        self._shutdown = False
        self._log_queue = queue.Queue()

        # Simple formatter
        self.setFormatter(logging.Formatter(
            "%(asctime)s | %(message)s",
            datefmt="%H:%M:%S"
        ))
        # Only show INFO and above
        self.setLevel(logging.INFO)

    def shutdown(self):
        """Signal that the handler should stop accepting logs"""
        self._shutdown = True

    def emit(self, record):
        """Put log record in queue (thread-safe)"""
        if self._shutdown:
            return

        try:
            msg = self.format(record)
            self._log_queue.put_nowait((msg, record.levelno))
        except queue.Full:
            pass
        except Exception:
            pass

    def process_queue(self):
        """Process pending logs. MAIN THREAD ONLY."""
        if self._shutdown:
            return

        try:
            messages_processed = 0
            max_batch = 30

            while messages_processed < max_batch:
                try:
                    msg, levelno = self._log_queue.get_nowait()
                    self._append_log(msg, levelno)
                    messages_processed += 1
                except queue.Empty:
                    break
        except tk.TclError:
            pass

    def _append_log(self, msg: str, levelno: int):
        """Append log message to text widget. MAIN THREAD ONLY."""
        if self._shutdown:
            return

        try:
            if not self.text_widget.winfo_exists():
                return

            self.text_widget.configure(state="normal")
            self.text_widget.insert(tk.END, msg + "\n")
            self.text_widget.see(tk.END)

            # Apply tag based on level
            line_start = self.text_widget.index("end-2l linestart")
            line_end = self.text_widget.index("end-1l lineend")

            if levelno >= logging.ERROR:
                self.text_widget.tag_add("error", line_start, line_end)
            elif levelno >= logging.WARNING:
                self.text_widget.tag_add("warning", line_start, line_end)
            else:
                self.text_widget.tag_add("info", line_start, line_end)

            # Limit to 500 lines
            line_count = int(self.text_widget.index("end-1c").split(".")[0])
            if line_count > 500:
                self.text_widget.delete("1.0", f"{line_count - 500}.0")

            self.text_widget.configure(state="disabled")
        except tk.TclError:
            pass


class InfoLogPanel(ttk.Frame):
    """Compact panel showing INFO level logs for dashboard"""

    def __init__(self, parent):
        super().__init__(parent)

        # Log text widget
        self.log_text = tk.Text(
            self,
            wrap="none",
            font=("Consolas", 9),
            state="disabled",
            bg="#1e1e1e",
            fg="#d4d4d4",
            height=12
        )

        # Scrollbar
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=v_scroll.set)

        # Layout
        self.log_text.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")

        # Configure tags for coloring
        self.log_text.tag_configure("error", foreground="#f44747")
        self.log_text.tag_configure("warning", foreground="#cca700")
        self.log_text.tag_configure("info", foreground="#4fc1ff")

        # Setup logging handler
        self._handler: Optional[InfoTextHandler] = None
        self._setup_logging()

        # Start log queue processing
        self._start_log_processing()

    def _setup_logging(self) -> None:
        """Setup logging handler to capture INFO+ logs"""
        self._handler = InfoTextHandler(self.log_text)

        # Add handler to root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Ensure root logger allows all levels
        root_logger.addHandler(self._handler)

        # Add to specific app loggers (propagate=False로 인해 직접 추가 필요)
        logger_names = [
            "src", "__main__",
            "src.core", "src.core.macro", "src.core.parser", "src.core.actions",
            "src.automation", "src.automation.clipboard", "src.automation.hotkeys",
            "src.gui", "src.gui.app",
            "src.strategy", "src.strategy.heuristic",
            "src.stats", "src.stats.collector",
        ]
        for logger_name in logger_names:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)  # Ensure logger allows all levels
            if self._handler not in logger.handlers:
                logger.addHandler(self._handler)

    def _start_log_processing(self) -> None:
        """Start periodic log queue processing"""
        self._process_log_queue()

    def _process_log_queue(self) -> None:
        """Process log queue and reschedule. MAIN THREAD ONLY."""
        if self._handler:
            self._handler.process_queue()

        try:
            if self.winfo_exists():
                self.after(100, self._process_log_queue)
        except tk.TclError:
            pass

    def destroy(self) -> None:
        """Clean up when widget is destroyed"""
        if self._handler:
            self._handler.shutdown()

            # Remove handler from loggers
            root_logger = logging.getLogger()
            try:
                root_logger.removeHandler(self._handler)
            except ValueError:
                pass

            logger_names = [
                "src", "__main__",
                "src.core", "src.core.macro", "src.core.parser", "src.core.actions",
                "src.automation", "src.automation.clipboard", "src.automation.hotkeys",
                "src.gui", "src.gui.app",
                "src.strategy", "src.strategy.heuristic",
                "src.stats", "src.stats.collector",
            ]
            for logger_name in logger_names:
                logger = logging.getLogger(logger_name)
                try:
                    logger.removeHandler(self._handler)
                except ValueError:
                    pass

            self._handler = None
        super().destroy()
