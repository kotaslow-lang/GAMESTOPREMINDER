"""
ui/tray_icon.py - System tray icon with menu.
"""
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PySide6.QtCore import Signal


def create_default_icon() -> QIcon:
    """Create a simple colored icon programmatically (no file needed)."""
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Draw a game controller-like shape
    painter.setBrush(QColor("#1a1a2e"))
    painter.setPen(QColor("#00f5d4"))
    painter.drawRoundedRect(4, 16, 56, 36, 12, 12)

    # Neon accent
    painter.setBrush(QColor("#00f5d4"))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(16, 26, 10, 10)
    painter.drawEllipse(38, 26, 10, 10)

    painter.end()
    return QIcon(pixmap)


# Need to import Qt for the pen
from PySide6.QtCore import Qt
import os
import sys

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class TrayIcon(QSystemTrayIcon):
    """System tray icon with context menu."""
    show_requested = Signal()
    quit_requested = Signal()
    toggle_detection = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        icon_path = get_resource_path(os.path.join("resources", "icons", "app_icon.ico"))
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            self.setIcon(create_default_icon())
            
        self.setToolTip("Game Stop Reminder - 待機中")

        self._setup_menu()
        self.activated.connect(self._on_activated)

    def _setup_menu(self):
        menu = QMenu()

        self.show_action = QAction("🖥️  ウィンドウ表示", menu)
        self.show_action.triggered.connect(self.show_requested.emit)
        menu.addAction(self.show_action)

        menu.addSeparator()

        self.detection_action = QAction("🔍  検知 開始/停止", menu)
        self.detection_action.triggered.connect(self.toggle_detection.emit)
        menu.addAction(self.detection_action)

        menu.addSeparator()

        quit_action = QAction("❌  終了", menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_requested.emit()

    def update_status(self, status: str):
        """Update tooltip with current status."""
        self.setToolTip(f"Game Stop Reminder - {status}")

    def show_reminder(self, title: str, message: str):
        """Show a balloon/toast notification."""
        self.showMessage(
            title,
            message,
            QSystemTrayIcon.Warning,
            10000  # Show for 10 seconds
        )
