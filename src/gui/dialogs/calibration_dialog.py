"""Calibration dialog for setting screen coordinates"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import threading
import time

from pynput import mouse

from ...automation.mouse import get_position, click_at
from ...config.coordinates import Coordinates
from ...utils.logger import get_logger, LOG_DIR

# Logger for this module
logger = get_logger(__name__)


class CalibrationDialog:
    """Dialog for calibrating screen coordinates"""

    def __init__(self, parent, coords: Coordinates, on_save: Callable[[Coordinates], None] = None):
        self.parent = parent
        self.coords = coords
        self.on_save = on_save
        self._capturing = False
        self._capture_target = None
        self._mouse_listener = None

        logger.info("CalibrationDialog 열림")
        logger.debug(f"현재 좌표: output=({coords.chat_output_x}, {coords.chat_output_y}), input=({coords.chat_input_x}, {coords.chat_input_y})")

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("좌표 설정")
        self.dialog.geometry("500x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Instructions
        instruction_frame = ttk.LabelFrame(self.dialog, text="설정 방법", padding=10)
        instruction_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(
            instruction_frame,
            text="각 좌표는 클릭할 위치 한 점입니다.\n\n"
                 "• 채팅 출력 영역: 채팅 메시지가 보이는 곳 아무 데나\n"
                 "  (Ctrl+A로 전체 선택 후 복사하므로 정확한 위치 불필요)\n\n"
                 "• 채팅 입력 영역: 메시지 입력하는 텍스트 박스\n"
                 "  (여기에 '강화' 등의 명령어를 입력합니다)",
            justify="left",
            wraplength=450
        ).pack(anchor="w")

        # Coordinates frame
        coords_frame = ttk.LabelFrame(self.dialog, text="좌표 설정", padding=10)
        coords_frame.pack(fill="x", padx=10, pady=10)

        # Chat output coordinates
        ttk.Label(coords_frame, text="채팅 출력 영역 (클릭 위치):").grid(row=0, column=0, sticky="w", pady=5)

        self.output_x = ttk.Entry(coords_frame, width=8)
        self.output_x.insert(0, str(coords.chat_output_x))
        self.output_x.grid(row=0, column=1, padx=2)

        ttk.Label(coords_frame, text="X").grid(row=0, column=2)

        self.output_y = ttk.Entry(coords_frame, width=8)
        self.output_y.insert(0, str(coords.chat_output_y))
        self.output_y.grid(row=0, column=3, padx=2)

        ttk.Label(coords_frame, text="Y").grid(row=0, column=4)

        ttk.Button(
            coords_frame,
            text="클릭으로 캡처",
            command=lambda: self._start_capture("output"),
            width=12
        ).grid(row=0, column=5, padx=10)

        # Chat input coordinates
        ttk.Label(coords_frame, text="채팅 입력 영역 (클릭 위치):").grid(row=1, column=0, sticky="w", pady=5)

        self.input_x = ttk.Entry(coords_frame, width=8)
        self.input_x.insert(0, str(coords.chat_input_x))
        self.input_x.grid(row=1, column=1, padx=2)

        ttk.Label(coords_frame, text="X").grid(row=1, column=2)

        self.input_y = ttk.Entry(coords_frame, width=8)
        self.input_y.insert(0, str(coords.chat_input_y))
        self.input_y.grid(row=1, column=3, padx=2)

        ttk.Label(coords_frame, text="Y").grid(row=1, column=4)

        ttk.Button(
            coords_frame,
            text="클릭으로 캡처",
            command=lambda: self._start_capture("input"),
            width=12
        ).grid(row=1, column=5, padx=10)

        # Current position display
        pos_frame = ttk.LabelFrame(self.dialog, text="현재 마우스 위치 (실시간)", padding=10)
        pos_frame.pack(fill="x", padx=10, pady=10)

        self.pos_label = ttk.Label(pos_frame, text="X: 0, Y: 0", font=("", 14, "bold"))
        self.pos_label.pack()

        # Capture status
        self.status_label = ttk.Label(pos_frame, text="", foreground="blue")
        self.status_label.pack(pady=5)

        # Start position tracking
        self._update_position()

        # Log file info
        log_frame = ttk.LabelFrame(self.dialog, text="디버그 로그", padding=10)
        log_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(
            log_frame,
            text=f"로그 파일: {LOG_DIR}",
            foreground="gray"
        ).pack(anchor="w")

        ttk.Button(
            log_frame,
            text="로그 폴더 열기",
            command=self._open_log_folder
        ).pack(anchor="w", pady=5)

        # Button frame
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="저장", command=self._save).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="취소", command=self._on_close).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="테스트 클릭", command=self._test_click).pack(side="left", padx=5)

        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)

    def _update_position(self) -> None:
        """Update current mouse position display"""
        try:
            x, y = get_position()
            self.pos_label.config(text=f"X: {x}, Y: {y}")
            self.dialog.after(50, self._update_position)
        except Exception as e:
            logger.error(f"마우스 위치 업데이트 실패: {e}")

    def _start_capture(self, target: str) -> None:
        """Start capturing coordinates from mouse click"""
        if self._capturing:
            logger.warning("이미 캡처 중입니다")
            return

        self._capturing = True
        self._capture_target = target
        target_name = "채팅 출력 영역" if target == "output" else "채팅 입력 영역"

        logger.info(f"좌표 캡처 시작: {target_name}")
        self.status_label.config(text=f"⏳ {target_name}을 클릭하세요... (10초 대기)")

        # Start mouse listener
        def on_click(x, y, button, pressed):
            if pressed and self._capturing:
                logger.info(f"클릭 감지: x={x}, y={y}, button={button}")
                self._capturing = False

                # Update in main thread
                self.dialog.after(0, lambda: self._set_coords(target, x, y))
                self.dialog.after(0, lambda: self.status_label.config(
                    text=f"✅ {target_name} 좌표 설정: ({x}, {y})"
                ))

                # Stop listener
                return False

        logger.debug("pynput 마우스 리스너 시작")
        self._mouse_listener = mouse.Listener(on_click=on_click)
        self._mouse_listener.start()

        # Timeout after 10 seconds
        def timeout():
            if self._capturing:
                logger.warning("캡처 타임아웃 (10초)")
                self._capturing = False
                if self._mouse_listener:
                    self._mouse_listener.stop()
                self.status_label.config(text="⚠️ 타임아웃 - 다시 시도해주세요")

        threading.Timer(10.0, timeout).start()

    def _set_coords(self, target: str, x: int, y: int) -> None:
        """Set coordinates in entry fields"""
        logger.debug(f"좌표 설정: target={target}, x={x}, y={y}")

        if target == "output":
            self.output_x.delete(0, tk.END)
            self.output_x.insert(0, str(x))
            self.output_y.delete(0, tk.END)
            self.output_y.insert(0, str(y))
        elif target == "input":
            self.input_x.delete(0, tk.END)
            self.input_x.insert(0, str(x))
            self.input_y.delete(0, tk.END)
            self.input_y.insert(0, str(y))

    def _test_click(self) -> None:
        """Test click at configured coordinates"""
        try:
            x = int(self.input_x.get())
            y = int(self.input_y.get())

            logger.info(f"테스트 클릭 시작: ({x}, {y})")

            result = messagebox.askyesno(
                "테스트",
                f"3초 후 ({x}, {y})에 클릭합니다.\n계속하시겠습니까?",
                parent=self.dialog
            )

            if not result:
                logger.info("테스트 클릭 취소됨")
                return

            self.dialog.withdraw()

            time.sleep(3)
            logger.debug(f"click_at({x}, {y}) 실행")
            click_at(x, y)
            logger.info("테스트 클릭 완료")

            self.dialog.deiconify()

        except ValueError as e:
            logger.error(f"좌표 값 오류: {e}")
            messagebox.showerror("오류", "좌표가 올바르지 않습니다.", parent=self.dialog)

    def _open_log_folder(self) -> None:
        """Open log folder in file explorer"""
        import subprocess
        import sys

        logger.info(f"로그 폴더 열기: {LOG_DIR}")

        if sys.platform == "darwin":  # macOS
            subprocess.run(["open", str(LOG_DIR)])
        elif sys.platform == "win32":  # Windows
            subprocess.run(["explorer", str(LOG_DIR)])
        else:  # Linux
            subprocess.run(["xdg-open", str(LOG_DIR)])

    def _save(self) -> None:
        """Save coordinates"""
        try:
            old_coords = (
                self.coords.chat_output_x, self.coords.chat_output_y,
                self.coords.chat_input_x, self.coords.chat_input_y
            )

            self.coords.chat_output_x = int(self.output_x.get())
            self.coords.chat_output_y = int(self.output_y.get())
            self.coords.chat_input_x = int(self.input_x.get())
            self.coords.chat_input_y = int(self.input_y.get())

            new_coords = (
                self.coords.chat_output_x, self.coords.chat_output_y,
                self.coords.chat_input_x, self.coords.chat_input_y
            )

            logger.info(f"좌표 저장: {old_coords} -> {new_coords}")

            # Save to file
            self.coords.save()
            logger.info(f"좌표 파일 저장 완료")

            # Call callback
            if self.on_save:
                self.on_save(self.coords)

            self.dialog.destroy()
            messagebox.showinfo("좌표 설정", "좌표가 저장되었습니다.")

        except ValueError as e:
            logger.error(f"좌표 저장 실패: {e}")
            messagebox.showerror("오류", f"잘못된 값이 있습니다: {e}", parent=self.dialog)

    def _on_close(self) -> None:
        """Handle dialog close"""
        logger.info("CalibrationDialog 닫힘")

        # Stop mouse listener if running
        if self._mouse_listener:
            self._mouse_listener.stop()

        self._capturing = False
        self.dialog.destroy()
