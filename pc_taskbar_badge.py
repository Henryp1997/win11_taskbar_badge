"""
pc_taskbar_badge.py

Custom text display widget for windows taskbars
"""

import sys
import os
import yaml
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QFont, QColor, QGuiApplication
from PySide6.QtWidgets import QApplication, QWidget, QMenu


class PCBadge(QWidget):
    def __init__(self, text, bg="#20242B", fg="#FFFFFF", border_radius=4):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
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

        self.placeBottomLeft(available)
        self._drag_off = 0

        # Keep the badge from falling behind taskbar/other always-on-top windows
        self._top_timer = QTimer(self)
        self._top_timer.setInterval(200)
        self._top_timer.timeout.connect(self.ensureOnTop)
        self._top_timer.start()

        # Prevent the badge from stealing focus
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)

        # Create context menu to show Close option when right clicking
        self.close_context = QMenu(parent=self)
        close_action = self.close_context.addAction("Close")
        close_action.triggered.connect(QApplication.quit)


    def placeBottomLeft(self, available):
        """ Force place the badge on the bottom left of the screen over the taskbar """
        x, y = available.left() + 5, available.bottom() + 5
        self.move(x, y)
        self.badge_pos = (x, y)


    def paintEvent(self, _):
        from PySide6.QtGui import QPainterPath
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
            if (e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)) == (Qt.ControlModifier | Qt.ShiftModifier):
                # Close window if also holding CTRL and SHIFT
                self.close()
                sys.exit()
                return

        elif e.button() == Qt.RightButton:
            self.close_context.popup(QPoint(*self.badge_pos))
            QTimer.singleShot(0, lambda: self.setWidgetTopMost(self.close_context))

        super().mousePressEvent(e)

    
    def mouseMoveEvent(self, e):
        if self._drag_off:
            self.move(e.globalPosition().toPoint() - self._drag_off)


    def mouseReleaseEvent(self, e):
        self._drag_off = None


    def ensureOnTop(self):
        # Qt-level bump
        if self.isVisible():
            self.raise_()

        self.setWidgetTopMost(self)

        if self.close_context.isVisible():
            self.setWidgetTopMost(self.close_context)


    def setWidgetTopMost(self, widget):
        # Win32-level bump (more reliable vs taskbar)
        if sys.platform == "win32" and widget.isVisible():
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.WinDLL("user32", use_last_error=True)
            HWND_TOPMOST = -1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            SWP_SHOWWINDOW = 0x0040

            user32.SetWindowPos(
                wintypes.HWND(int(widget.winId())),
                wintypes.HWND(HWND_TOPMOST),
                0, 0, 0, 0, # x, y, x_width, y_width
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
            )


if __name__ == "__main__":
    with open(Path(__file__).parent / "config.yml", "r") as f:
        config = yaml.safe_load(f)

    host = config.get("host", None)
    if host is None:
        host = os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "PC"
    
    bg_colour = config.get("bg_colour", "#FF8A00")
    fg_colour = config.get("fg_colour", "#FFFFFF")
    border_radius = config.get("border_radius", 6)
    
    app = QApplication(sys.argv)
    w = PCBadge(
        text=host,
        bg=bg_colour,
        fg=fg_colour,
        border_radius=border_radius
    )
    w.show()
    sys.exit(app.exec())
