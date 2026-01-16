"""CLI entry point for the macro"""
import argparse
import sys
import time
from .core.macro import MacroRunner
from .core.state import MacroState
from .config.settings import Settings
from .config.coordinates import Coordinates
from .automation.hotkeys import HotkeyListener


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════╗
║           검키우기 강화 매크로 v1.0                    ║
║                                                      ║
║  단축키:                                             ║
║    F1 - 수동 강화                                    ║
║    F2 - 수동 판매                                    ║
║    F3 - 자동 모드 시작                               ║
║    F4 - 일시정지/재개                                ║
║    F5 - 정지                                        ║
║    ESC - 긴급 정지                                   ║
╚══════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="검키우기 강화 매크로")
    parser.add_argument("--gui", action="store_true", help="GUI 모드로 실행")
    parser.add_argument("--auto", action="store_true", help="자동 모드로 바로 시작")
    parser.add_argument("--calibrate", action="store_true", help="좌표 캘리브레이션 모드")

    args = parser.parse_args()

    # GUI mode
    if args.gui:
        from .gui.app import main as gui_main
        gui_main()
        return

    # Load config
    settings = Settings.load()
    coords = Coordinates.load()

    # Calibration mode
    if args.calibrate:
        print("좌표 캘리브레이션 모드")
        print("마우스를 원하는 위치로 이동한 후 Enter를 누르세요.")

        import pyautogui

        print("\n[채팅 출력 영역] 마우스를 위치시키고 Enter...")
        input()
        x, y = pyautogui.position()
        coords.chat_output_x = x
        coords.chat_output_y = y
        print(f"  저장됨: ({x}, {y})")

        print("\n[채팅 입력 영역] 마우스를 위치시키고 Enter...")
        input()
        x, y = pyautogui.position()
        coords.chat_input_x = x
        coords.chat_input_y = y
        print(f"  저장됨: ({x}, {y})")

        coords.save()
        print("\n좌표가 저장되었습니다.")
        return

    # CLI mode
    print_banner()

    # Initialize macro
    macro = MacroRunner(coords=coords, settings=settings)

    # Setup hotkeys
    hotkey_listener = HotkeyListener()

    def on_enhance():
        if not macro.is_running():
            result = macro.manual_enhance()
            if result:
                print(f"강화 결과: {result.display_name}")

    def on_sell():
        if not macro.is_running():
            if macro.manual_sell():
                print("판매 완료")

    def on_start():
        if not macro.is_running():
            print("자동 모드 시작...")
            macro.start_auto()

    def on_pause():
        if macro.is_running():
            if macro.is_paused():
                macro.resume()
                print("재개됨")
            else:
                macro.pause()
                print("일시정지")

    def on_stop():
        if macro.is_running():
            macro.stop()
            print("정지됨")

    def on_emergency():
        macro.stop()
        print("긴급 정지!")

    hotkey_listener.register("f1", on_enhance)
    hotkey_listener.register("f2", on_sell)
    hotkey_listener.register("f3", on_start)
    hotkey_listener.register("f4", on_pause)
    hotkey_listener.register("f5", on_stop)
    hotkey_listener.register("escape", on_emergency)

    hotkey_listener.start()

    print("매크로가 준비되었습니다. 단축키를 사용하세요.")
    print("종료하려면 Ctrl+C를 누르세요.\n")

    # Auto mode
    if args.auto:
        print("자동 모드로 시작합니다...")
        macro.start_auto()

    # Main loop
    try:
        while True:
            time.sleep(1)

            # Print status periodically
            if macro.is_running():
                state = macro.game_state
                print(f"\r현재: {state.level_display} | 골드: {state.gold_display} | 연속실패: {state.fail_count}", end="")

    except KeyboardInterrupt:
        print("\n\n종료합니다...")
        macro.stop()
        hotkey_listener.stop()


if __name__ == "__main__":
    main()
