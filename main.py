"""
main.py - Entry point for Game Stop Reminder application.

Initializes all modules, wires signals, and starts the app.
"""
import sys
import os
import winsound
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QColor, QIcon

from ui.main_window import MainWindow
from ui.tray_icon import TrayIcon
from ui.settings_dialog import SettingsDialog
from game_detector import GameDetector
from reminder_manager import ReminderManager
from reminder_manager import ReminderManager
from data.storage import load_settings, save_settings, load_history, add_history_entry


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class ReminderPopup(QDialog):
    """Full-screen-like reminder popup that overlays on top of everything."""
    def __init__(self, game_name: str, elapsed_str: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⏰ リマインダー")
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Dialog
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(460, 280)

        # Main container
        container = QFrame(self)
        container.setObjectName("reminderPopup")
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(16)
        container_layout.setContentsMargins(32, 28, 32, 28)

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(255, 107, 107, 120))
        shadow.setOffset(0, 0)
        container.setGraphicsEffect(shadow)

        # Title
        title = QLabel("⏰ 時間です！")
        title.setObjectName("reminderTitle")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title)

        # Message
        msg = QLabel(f"🎮 {game_name}\nプレイ時間: {elapsed_str}")
        msg.setObjectName("reminderMessage")
        msg_font = QFont()
        msg_font.setPointSize(13)
        msg.setFont(msg_font)
        msg.setAlignment(Qt.AlignCenter)
        msg.setWordWrap(True)
        container_layout.addWidget(msg)

        advice = QLabel("そろそろ休憩しませんか？ 🌟")
        advice.setObjectName("reminderMessage")
        advice_font = QFont()
        advice_font.setPointSize(11)
        advice.setFont(advice_font)
        advice.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(advice)

        container_layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        dismiss_btn = QPushButton("👍 わかった")
        dismiss_btn.setObjectName("reminderDismissBtn")
        dismiss_btn.clicked.connect(self.accept)
        btn_layout.addWidget(dismiss_btn)

        snooze_btn = QPushButton("⏰ あと少し...")
        snooze_btn.setObjectName("reminderSnoozeBtn")
        snooze_btn.clicked.connect(self.reject)  # reject = snooze
        btn_layout.addWidget(snooze_btn)

        container_layout.addLayout(btn_layout)

        # Layout for this dialog
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

    def showEvent(self, event):
        super().showEvent(event)
        # Center on screen
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2
            )


class GameStopReminderApp:
    """Main application controller."""
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in tray

        # Load styles and icons
        self._load_styles()
        
        icon_path = get_resource_path(os.path.join("resources", "icons", "app_icon.ico"))
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))

        # Load settings
        self.settings = load_settings()

        # Initialize components
        self.detector = GameDetector()
        self.reminder = ReminderManager()
        self.window = MainWindow()
        self.tray = TrayIcon()

        # Apply settings
        self._apply_settings()

        # Wire signals
        self._connect_signals()

        # Load history
        self._refresh_history()

        # Detection state
        self._detecting = False

    def _load_styles(self):
        """Load QSS stylesheet."""
        style_path = get_resource_path("style.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.app.setStyleSheet(f.read())

    def _apply_settings(self):
        """Apply current settings to all components."""
        # Set game list
        games = self.settings.get("games", [])
        self.detector.set_monitored_games(games)
        self.window.game_list.set_games(games)

        # Set reminder config
        self.reminder.set_default_time_limit(
            self.settings.get("default_time_limit_minutes", 60)
        )
        self.reminder.set_reminder_interval(
            self.settings.get("reminder_interval_minutes", 10)
        )

        # Per-game time limits
        custom_limits = {}
        for g in games:
            if g.get("custom_time_limit") is not None:
                custom_limits[g["exe_name"].lower()] = g["custom_time_limit"]
        self.reminder.set_game_time_limits(custom_limits)

    def _connect_signals(self):
        """Connect all signals between components."""
        # Game detector signals
        self.detector.game_started.connect(self._on_game_started)
        self.detector.game_stopped.connect(self._on_game_stopped)

        # Reminder signals
        self.reminder.time_updated.connect(self._on_time_updated)
        self.reminder.reminder_triggered.connect(self._on_reminder_triggered)
        self.reminder.session_ended.connect(self._on_session_ended)

        # UI signals
        self.window.status_card.detection_btn.clicked.connect(self._toggle_detection)
        self.window.settings_btn.clicked.connect(self._open_settings)
        self.window.game_list.games_changed.connect(self._on_games_changed)
        self.window.history_widget.clear_btn.clicked.connect(self._clear_history)

        # Tray signals
        self.tray.show_requested.connect(self._show_window)
        self.tray.quit_requested.connect(self._quit)
        self.tray.toggle_detection.connect(self._toggle_detection)

    def _toggle_detection(self):
        """Toggle game detection on/off."""
        if self._detecting:
            self.detector.stop()
            self._detecting = False
            self.window.status_card.detection_btn.setText("🔍 検知開始")
            self.window.status_card.set_idle()
            self.tray.update_status("停止中")
        else:
            self.detector.start()
            self._detecting = True
            self.window.status_card.detection_btn.setText("⏹️ 検知停止")
            self.window.status_card.set_detecting()
            self.tray.update_status("スキャン中")

    def _on_game_started(self, game):
        """Called when a game process is detected."""
        self.reminder.start_session(game.exe_name, game.display_name)
        self.window.status_card.set_game_active(game.display_name)
        self.tray.update_status(f"プレイ中: {game.display_name}")
        self.tray.show_reminder(
            "🎮 ゲーム検出",
            f"{game.display_name} のプレイを検知しました。"
        )

    def _on_game_stopped(self, game):
        """Called when a game process ends."""
        total = self.reminder.stop_session(game.exe_name)

        # Record history
        session = None
        # We need start_time from before, but it's already gone
        # Use current time minus elapsed seconds as approximation
        start = datetime.fromtimestamp(
            datetime.now().timestamp() - total
        )
        add_history_entry(game.display_name, game.exe_name, start, total)
        self._refresh_history()

        # Update UI if no more active games
        if not self.reminder.has_active_sessions():
            if self._detecting:
                self.window.status_card.set_detecting()
                self.tray.update_status("スキャン中")
            else:
                self.window.status_card.set_idle()

    def _on_time_updated(self, exe_name: str, elapsed: int, remaining: int):
        """Called every second to update the timer display."""
        session = self.reminder.get_session(exe_name)
        if session:
            self.window.status_card.update_time(
                session.format_elapsed(),
                session.format_remaining(),
                session.progress
            )

    def _on_reminder_triggered(self, exe_name: str, display_name: str, elapsed: int):
        """Called when a time limit is reached."""
        session = self.reminder.get_session(exe_name)
        elapsed_str = session.format_elapsed() if session else "N/A"

        # Play alarm sound
        if self.settings.get("sound_enabled", True):
            try:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception:
                pass

        # Show tray notification
        self.tray.show_reminder(
            "⏰ リマインダー",
            f"{display_name} のプレイ時間が制限に達しました！\n"
            f"プレイ時間: {elapsed_str}"
        )

        # Show popup dialog
        popup = ReminderPopup(display_name, elapsed_str, self.window)
        # Load style for popup
        popup.setStyleSheet(self.app.styleSheet())
        popup.exec()

    def _on_session_ended(self, exe_name: str, total_seconds: int):
        """Called when a session ends."""
        pass  # Handled in _on_game_stopped

    def _open_settings(self):
        """Open settings dialog."""
        dialog = SettingsDialog(self.settings, self.window)
        if dialog.exec() == QDialog.Accepted:
            self.settings = dialog.get_settings()
            save_settings(self.settings)
            self._apply_settings()

    def _on_games_changed(self):
        """Called when the game list is modified."""
        self.settings["games"] = self.window.game_list.get_games()
        save_settings(self.settings)
        self.detector.set_monitored_games(self.settings["games"])

        # Update per-game limits
        custom_limits = {}
        for g in self.settings["games"]:
            if g.get("custom_time_limit") is not None:
                custom_limits[g["exe_name"].lower()] = g["custom_time_limit"]
        self.reminder.set_game_time_limits(custom_limits)

    def _refresh_history(self):
        """Reload and display history."""
        history = load_history()
        self.window.history_widget.set_history(history)

    def _clear_history(self):
        """Clear all play history."""
        from data.storage import save_history
        save_history([])
        self._refresh_history()

    def _show_window(self):
        """Show and bring window to front."""
        self.window.show()
        self.window.activateWindow()
        self.window.raise_()

    def _quit(self):
        """Properly quit the application."""
        self.detector.stop()
        self.tray.hide()
        self.app.quit()

    def run(self) -> int:
        """Start the application."""
        # Show tray icon
        self.tray.show()

        # Show or hide window based on settings
        if not self.settings.get("start_minimized", False):
            self.window.show()

        # Auto-start detection if configured
        if self.settings.get("auto_start_detection", True):
            self._toggle_detection()

        return self.app.exec()


def main():
    # Ensure we're running from the correct directory
    try:
        os.chdir(sys._MEIPASS)
    except Exception:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    app = GameStopReminderApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
