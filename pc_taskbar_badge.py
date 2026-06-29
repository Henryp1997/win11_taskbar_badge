"""
pc_taskbar_badge.py

Custom text display widget for windows taskbars
"""

import sys
import os
import yaml
from pathlib import Path
import ctypes
from ctypes import wintypes
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QFont, QColor, QGuiApplication, QPainterPath
from PySide6.QtWidgets import QApplication, QWidget, QMenu
from get_taskbar_pos import get_taskbar_position

class PCBadge(QWidget):
    def __init__(
        self,
        text: str,
        bg: str = "#20242B",
        fg: str = "#FFFFFF",
        border_radius: int = 4,
        debug: bool = False
    ):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.debug = debug
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.text = text
        self.bg = QColor(bg); self.fg = QColor(fg)
        self.padding = (8, 6)
        self.font = QFont("Segoe UI", 14, QFont.Bold)
        self.border_radius = border_radius
        
        screen = QGuiApplication.primaryScreen()
        available = screen.availableGeometry()
        window = screen.geometry()
        taskbar_height = window.height() - available.height()
        self.resize(150, 40 * (taskbar_height / 48))

        self.place_widget_in_available_area(available)
        self._drag_off = 0

        # Keep the badge from falling behind taskbar/other always-on-top windows
        self._top_timer = QTimer(self)
        self._top_timer.setInterval(200)
        self._top_timer.timeout.connect(self.ensure_on_top)
        self._top_timer.start()

        # Prevent the badge from stealing focus
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)

        # Create context menu to show Close option when right clicking
        self.close_context = QMenu(parent=self)
        close_action = self.close_context.addAction("Close")
        close_action.triggered.connect(QApplication.quit)


    def place_widget_in_available_area(self, available):
        """ 
        Force place the badge on the taskbar
        Place the widget on the bottom left if user has taskbar centered
        Otherwise, attempt to locate optimal position for widget so it
        doesn't clash with existing icons on the taskbar
        """
        pos, alignment = get_taskbar_position()
        if not self.debug:
            if pos == "bottom" and alignment != "centre":
                raise NotImplementedError(
                    "This app does not currently work for taskbar " \
                    "positions other than 'bottom', with 'left' icon/start alignment"
                )
        x, y = available.left() + 5, available.bottom() + 5
        self.move(x, y)
        self.badge_pos = (x, y)


    def ensure_on_top(self):
        """
        Method to be called on a timer to bump the application
        to the top, so that it is painted above the taskbar
        """
        # Qt-level bump
        if self.isVisible():
            self.raise_()

        self.set_widget_top_most(self)

        if self.close_context.isVisible():
            self.set_widget_top_most(self.close_context)


    def set_widget_top_most(self, widget):
        """
        Leverage the Windows API's SetWindowPos method to force
        this application to be placed on top of the taskbar
        --> BOOL SetWindowPos(
                HWND hWnd,
                HWND hWndInsertAfter,
                int X,
                int Y,
                int cx,
                int cy,
                UINT uFlags
            );
        """
        # Win32-level bump (more reliable vs taskbar)
        if sys.platform == "win32" and widget.isVisible(): # Only Windows supported for now
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            HWND_TOPMOST = -1       # -1 forces windows to place this window in the topmost Z-order
            SWP_NOMOVE = 0x0002     # Keep x-y position fixed when painting
            SWP_NOSIZE = 0x0001     # Keep size fixed when painting
            SWP_NOACTIVATE = 0x0010 # Don't steal focus
            SWP_SHOWWINDOW = 0x0040 # Ensure the window is visible after SetWindowPos

            user32.SetWindowPos(
                wintypes.HWND(int(widget.winId())), # This window's window handle
                wintypes.HWND(HWND_TOPMOST), # Make this window permanently TOPMOST
                0, 0, 0, 0, # x, y, x_width, y_width (all ignored because of below flags)

                # Combine all flags together into 'uFlags'
                SWP_NOMOVE |
                SWP_NOSIZE |
                SWP_NOACTIVATE |
                SWP_SHOWWINDOW
            )


    ### Qt event handling ###
    def paintEvent(self, _):
        """ Draw the rect and text of the widget """
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), self.border_radius, self.border_radius)
        p.fillPath(path, self.bg)
        p.setFont(self.font)
        p.setPen(self.fg)
        metrics = p.fontMetrics()
        tw = metrics.horizontalAdvance(self.text)
        th = metrics.ascent()
        x = (self.width() - tw) // 2
        y = (self.height() + th) // 2 - 2
        p.drawText(x, y, self.text)


    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            if (
                e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)
                ) == (Qt.ControlModifier | Qt.ShiftModifier):
                # Close window if also holding CTRL and SHIFT
                self.close()
                sys.exit()
                return

        elif e.button() == Qt.RightButton:
            self.close_context.popup(QPoint(*self.badge_pos))
            QTimer.singleShot(0, lambda: self.set_widget_top_most(self.close_context))

        super().mousePressEvent(e)

    
    def mouseMoveEvent(self, e):
        if self._drag_off:
            self.move(e.globalPosition().toPoint() - self._drag_off)


    def mouseReleaseEvent(self, e):
        self._drag_off = None


if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        config_path = Path(sys.executable).parent
    else:
        config_path = Path(__file__).parent

    with open(config_path / "config.yml", "r") as f:
        config = yaml.safe_load(f)

    text = config.get("text", None)
    if text is None or not text:
        text = os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "PC"
    
    bg_colour = config.get("bg_colour", "#FF8A00")
    fg_colour = config.get("fg_colour", "#FFFFFF")
    border_radius = config.get("border_radius", 6)
    
    app = QApplication(sys.argv)
    w = PCBadge(
        text=text,
        bg=bg_colour,
        fg=fg_colour,
        border_radius=border_radius,
        debug=config.get("debug", False)
    )
    w.show()
    sys.exit(app.exec())
