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

    # Try to use pynput - it will fail silently if no permissions
    try:
        from pynput.mouse import Controller as Mouse
        from pynput.keyboard import Controller as Keyboard

        mouse = Mouse()
        kb = Keyboard()

        # Test mouse position (this works without permissions)
        _ = mouse.position

        # Show info dialog about accessibility
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Mac 접근성 권한 안내",
            "이 앱은 마우스/키보드 제어를 위해 접근성 권한이 필요합니다.\n\n"
            "권한 설정 방법:\n"
            "1. 시스템 설정 → 개인정보 보호 및 보안 → 접근성\n"
            "2. Terminal (또는 사용 중인 터미널 앱) 체크\n\n"
            "권한이 없으면 마우스 클릭과 키보드 입력이 작동하지 않습니다."
        )
        root.destroy()
        return True

    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "접근성 권한 오류",
            f"pynput 초기화 실패: {e}\n\n"
            "시스템 설정 → 개인정보 보호 및 보안 → 접근성에서\n"
            "터미널 앱에 권한을 부여하세요."
        )
        root.destroy()
        return False


def main():
    """Main entry point for GUI application"""
    try:
        # Check macOS accessibility on first run
        if sys.platform == "darwin":
            check_mac_accessibility()

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
