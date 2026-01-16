"""GUI entry point for the macro - used for EXE build"""
import sys
import os

# Add src to path for imports
if getattr(sys, 'frozen', False):
    # Running as compiled EXE
    application_path = os.path.dirname(sys.executable)
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.dirname(application_path))

from src.gui.app import MacroApp


def main():
    """Main entry point for GUI application"""
    try:
        app = MacroApp()
        app.run()
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("오류", f"프로그램 실행 중 오류가 발생했습니다:\n\n{e}")
        root.destroy()
        sys.exit(1)


if __name__ == "__main__":
    main()
