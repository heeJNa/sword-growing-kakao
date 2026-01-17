"""System Tray functionality for background operation"""
import threading
from typing import Callable, Optional
from PIL import Image, ImageDraw
import pystray


class SystemTray:
    """System tray icon handler"""

    def __init__(
        self,
        on_show: Callable[[], None],
        on_quit: Callable[[], None],
        on_start: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
    ):
        self.on_show = on_show
        self.on_quit = on_quit
        self.on_start = on_start
        self.on_stop = on_stop

        self._icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None
        self._icon_image: Optional[Image.Image] = None  # Store for cleanup
        self._running = False

    def _create_icon_image(self, size: int = 64) -> Image.Image:
        """Create a simple sword icon"""
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw sword blade (rectangle)
        blade_width = size // 6
        blade_height = size * 2 // 3
        blade_x = (size - blade_width) // 2
        blade_y = size // 8

        draw.rectangle(
            [blade_x, blade_y, blade_x + blade_width, blade_y + blade_height],
            fill=(192, 192, 192),
            outline=(128, 128, 128),
        )

        # Draw sword guard (horizontal rectangle)
        guard_width = size // 2
        guard_height = size // 10
        guard_x = (size - guard_width) // 2
        guard_y = blade_y + blade_height

        draw.rectangle(
            [guard_x, guard_y, guard_x + guard_width, guard_y + guard_height],
            fill=(139, 69, 19),
            outline=(101, 67, 33),
        )

        # Draw sword handle
        handle_width = size // 8
        handle_height = size // 5
        handle_x = (size - handle_width) // 2
        handle_y = guard_y + guard_height

        draw.rectangle(
            [handle_x, handle_y, handle_x + handle_width, handle_y + handle_height],
            fill=(139, 69, 19),
            outline=(101, 67, 33),
        )

        return image

    def _create_menu(self) -> pystray.Menu:
        """Create tray menu"""
        menu_items = [
            pystray.MenuItem("열기", self._on_show_click, default=True),
        ]

        if self.on_start:
            menu_items.append(pystray.MenuItem("시작", self._on_start_click))

        if self.on_stop:
            menu_items.append(pystray.MenuItem("정지", self._on_stop_click))

        menu_items.append(pystray.Menu.SEPARATOR)
        menu_items.append(pystray.MenuItem("종료", self._on_quit_click))

        return pystray.Menu(*menu_items)

    def _on_show_click(self, icon, item) -> None:
        """Handle show click"""
        self.on_show()

    def _on_start_click(self, icon, item) -> None:
        """Handle start click"""
        if self.on_start:
            self.on_start()

    def _on_stop_click(self, icon, item) -> None:
        """Handle stop click"""
        if self.on_stop:
            self.on_stop()

    def _on_quit_click(self, icon, item) -> None:
        """Handle quit click"""
        self.stop()
        self.on_quit()

    def start(self) -> None:
        """Start the system tray icon"""
        if self._running:
            return

        self._running = True
        self._icon_image = self._create_icon_image()
        menu = self._create_menu()

        self._icon = pystray.Icon(
            name="sword_macro",
            icon=self._icon_image,
            title="검키우기 매크로",
            menu=menu,
        )

        # Run in background thread
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the system tray icon"""
        if not self._running:
            return

        self._running = False
        if self._icon:
            self._icon.stop()
            self._icon = None

        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            try:
                self._thread.join(timeout=1.0)
            except Exception:
                pass
            self._thread = None

        # Clean up PIL image
        if self._icon_image:
            try:
                self._icon_image.close()
            except Exception:
                pass
            self._icon_image = None

    def update_title(self, title: str) -> None:
        """Update tray icon title/tooltip"""
        if self._icon:
            self._icon.title = title

    def notify(self, title: str, message: str) -> None:
        """Show notification"""
        if self._icon:
            self._icon.notify(message, title)
