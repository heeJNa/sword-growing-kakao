"""Calibration dialog for setting screen coordinates"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import pyautogui
from ...config.coordinates import Coordinates


class CalibrationDialog:
    """Dialog for calibrating screen coordinates"""

    def __init__(self, parent, coords: Coordinates, on_save: Callable[[Coordinates], None] = None):
        self.parent = parent
        self.coords = coords
        self.on_save = on_save

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("좌표 설정")
        self.dialog.geometry("450x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Instructions
        instruction_frame = ttk.LabelFrame(self.dialog, text="사용 방법", padding=10)
        instruction_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(
            instruction_frame,
            text="1. '클릭 위치 캡처' 버튼을 누릅니다.\n"
                 "2. 3초 내에 원하는 위치를 클릭합니다.\n"
                 "3. 좌표가 자동으로 입력됩니다.",
            justify="left"
        ).pack(anchor="w")

        # Coordinates frame
        coords_frame = ttk.LabelFrame(self.dialog, text="좌표 설정", padding=10)
        coords_frame.pack(fill="x", padx=10, pady=10)

        # Chat output coordinates
        ttk.Label(coords_frame, text="채팅 출력 영역:").grid(row=0, column=0, sticky="w", pady=5)

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
            text="캡처",
            command=lambda: self._capture_coords("output"),
            width=6
        ).grid(row=0, column=5, padx=10)

        # Chat input coordinates
        ttk.Label(coords_frame, text="채팅 입력 영역:").grid(row=1, column=0, sticky="w", pady=5)

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
            text="캡처",
            command=lambda: self._capture_coords("input"),
            width=6
        ).grid(row=1, column=5, padx=10)

        # Current position display
        pos_frame = ttk.LabelFrame(self.dialog, text="현재 마우스 위치", padding=10)
        pos_frame.pack(fill="x", padx=10, pady=10)

        self.pos_label = ttk.Label(pos_frame, text="X: 0, Y: 0", font=("", 12))
        self.pos_label.pack()

        # Start position tracking
        self._update_position()

        # Button frame
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="저장", command=self._save).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="취소", command=self.dialog.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="테스트 클릭", command=self._test_click).pack(side="left", padx=5)

    def _update_position(self) -> None:
        """Update current mouse position display"""
        try:
            x, y = pyautogui.position()
            self.pos_label.config(text=f"X: {x}, Y: {y}")
            self.dialog.after(100, self._update_position)
        except Exception:
            pass

    def _capture_coords(self, target: str) -> None:
        """Capture coordinates from next click"""
        self.dialog.withdraw()  # Hide dialog

        # Wait for click
        messagebox.showinfo(
            "좌표 캡처",
            "3초 내에 원하는 위치를 클릭하세요.\n창이 자동으로 복원됩니다.",
            parent=self.parent
        )

        import time
        import threading

        def capture():
            time.sleep(0.5)  # Wait for messagebox to close
            initial_pos = pyautogui.position()

            # Wait for click (position change)
            for _ in range(30):  # 3 seconds
                time.sleep(0.1)
                current_pos = pyautogui.position()
                # Simple click detection
                pass

            # Get final position
            x, y = pyautogui.position()

            # Update in main thread
            self.dialog.after(0, lambda: self._set_coords(target, x, y))
            self.dialog.after(0, self.dialog.deiconify)

        threading.Thread(target=capture, daemon=True).start()

    def _set_coords(self, target: str, x: int, y: int) -> None:
        """Set coordinates in entry fields"""
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

            self.dialog.withdraw()
            messagebox.showinfo(
                "테스트",
                f"3초 후 ({x}, {y})에 클릭합니다.",
                parent=self.parent
            )

            import time
            time.sleep(3)
            pyautogui.click(x, y)

            self.dialog.deiconify()

        except ValueError:
            messagebox.showerror("오류", "좌표가 올바르지 않습니다.")

    def _save(self) -> None:
        """Save coordinates"""
        try:
            self.coords.chat_output_x = int(self.output_x.get())
            self.coords.chat_output_y = int(self.output_y.get())
            self.coords.chat_input_x = int(self.input_x.get())
            self.coords.chat_input_y = int(self.input_y.get())

            # Save to file
            self.coords.save()

            # Call callback
            if self.on_save:
                self.on_save(self.coords)

            self.dialog.destroy()
            messagebox.showinfo("좌표 설정", "좌표가 저장되었습니다.")

        except ValueError as e:
            messagebox.showerror("오류", f"잘못된 값이 있습니다: {e}")
