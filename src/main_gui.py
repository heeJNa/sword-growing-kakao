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


def check_mac_accessibility():
    """Check and warn about macOS accessibility permissions"""
    if sys.platform != "darwin":
        return True

    import tkinter as tk
    from tkinter import messagebox
    import subprocess

    # Create root window and bring to front on macOS
    root = tk.Tk()
    root.title("검키우기 매크로")

    # Set window size and center on screen
    window_width = 400
    window_height = 100
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Bring window to front on macOS
    root.lift()
    root.attributes('-topmost', True)
    root.update()
    root.attributes('-topmost', False)

    # Use AppleScript to activate the Python process (bring to front)
    try:
        subprocess.run([
            'osascript', '-e',
            'tell application "System Events" to set frontmost of first process whose unix id is (do shell script "echo $PPID") to true'
        ], capture_output=True, timeout=2)
    except Exception:
        pass

    # Show info dialog
    messagebox.showinfo(
        "Mac 손쉬운 사용 권한 안내",
        "이 앱은 마우스/키보드 제어를 위해 손쉬운 사용 권한이 필요합니다.\n\n"
        "권한 설정 방법:\n"
        "1. 시스템 설정 → 개인정보 보호 및 보안 → 손쉬운 사용\n"
        "2. 터미널 앱 (Terminal, iTerm, VS Code 등) 토글 ON\n"
        "3. 권한 부여 후 앱 재시작 필요\n\n"
        "권한이 없으면 마우스 클릭과 키보드 입력이 작동하지 않습니다.\n\n"
        "참고: macOS에서는 F1-F5 단축키가 지원되지 않습니다. GUI 버튼을 사용해주세요.",
        parent=root
    )
    root.destroy()
    return True


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
