"""
main.py - Entry point for Game Stop Reminder application.

Initializes all modules, wires signals, and starts the app.
"""
import os
import sys
import winsound
from datetime import datetime

from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, QRect, Qt
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from data.storage import add_history_entry, load_history, load_settings, save_settings
from game_detector import GameDetector
from reminder_manager import ReminderManager
from ui.main_window import MainWindow
from ui.settings_dialog import SettingsDialog
from ui.tray_icon import TrayIcon


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class ReminderPopup(QDialog):
    """Overlay reminder popup shown when a time limit is reached."""

    def __init__(self, game_name: str, elapsed_str: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⏰ リマインダー")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(460, 280)

        container = QFrame(self)
        container.setObjectName("reminderPopup")
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(16)
        container_layout.setContentsMargins(32, 28, 32, 28)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 214, 255, 120))
        shadow.setOffset(0, 0)
        container.setGraphicsEffect(shadow)

        title = QLabel("⏰ 時間です！")
        title.setObjectName("reminderTitle")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title)

        message = QLabel(f"🎮 {game_name}\nプレイ時間: {elapsed_str}")
        message.setObjectName("reminderMessage")
        message_font = QFont()
        message_font.setPointSize(13)
        message.setFont(message_font)
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        container_layout.addWidget(message)

        advice = QLabel("そろそろ休憩しませんか？ 🌟")
        advice.setObjectName("reminderMessage")
        advice_font = QFont()
        advice_font.setPointSize(11)
        advice.setFont(advice_font)
        advice.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(advice)

        container_layout.addStretch()

        button_row = QHBoxLayout()
        button_row.setSpacing(12)

        dismiss_btn = QPushButton("👍 わかった")
        dismiss_btn.setObjectName("reminderDismissBtn")
        dismiss_btn.clicked.connect(self.accept)
        button_row.addWidget(dismiss_btn)

        snooze_btn = QPushButton("⏰ あと少し...")
        snooze_btn.setObjectName("reminderSnoozeBtn")
        snooze_btn.clicked.connect(self.reject)
        button_row.addWidget(snooze_btn)

        container_layout.addLayout(button_row)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(container)

    def showEvent(self, event):
        super().showEvent(event)
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.center().x() - self.width() // 2, geo.center().y() - self.height() // 2)
            self._play_show_animation()

    def _play_show_animation(self):
        """Animate popup with futuristic fade + slide-in motion."""
        final_rect = self.geometry()
        start_rect = QRect(final_rect.x(), final_rect.y() + 24, final_rect.width(), final_rect.height())

        self.setWindowOpacity(0.0)
        self.setGeometry(start_rect)

        slide = QPropertyAnimation(self, b"geometry", self)
        slide.setDuration(320)
        slide.setStartValue(start_rect)
        slide.setEndValue(final_rect)
        slide.setEasingCurve(QEasingCurve.OutCubic)

        fade = QPropertyAnimation(self, b"windowOpacity", self)
        fade.setDuration(260)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.OutCubic)

        self._show_anim = QParallelAnimationGroup(self)
        self._show_anim.addAnimation(slide)
        self._show_anim.addAnimation(fade)
        self._show_anim.start()


class GameStopReminderApp:
    """Main application controller."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self._load_styles()

        icon_path = get_resource_path(os.path.join("resources", "icons", "app_icon.ico"))
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))

        self.settings = load_settings()

        self.detector = GameDetector()
        self.reminder = ReminderManager()
        self.window = MainWindow()
        self.tray = TrayIcon()

        self._apply_settings()
        self._connect_signals()
        self._refresh_history()

        self._detecting = False

    def _load_styles(self):
        style_path = get_resource_path("style.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.app.setStyleSheet(f.read())

    def _apply_settings(self):
        games = self.settings.get("games", [])
        self.detector.set_monitored_games(games)
        self.window.game_list.set_games(games)

        self.reminder.set_default_time_limit(self.settings.get("default_time_limit_minutes", 60))
        self.reminder.set_reminder_interval(self.settings.get("reminder_interval_minutes", 10))

        custom_limits = {}
        for game in games:
            if game.get("custom_time_limit") is not None:
                custom_limits[game["exe_name"].lower()] = game["custom_time_limit"]
        self.reminder.set_game_time_limits(custom_limits)

    def _connect_signals(self):
        self.detector.game_started.connect(self._on_game_started)
        self.detector.game_stopped.connect(self._on_game_stopped)

        self.reminder.time_updated.connect(self._on_time_updated)
        self.reminder.reminder_triggered.connect(self._on_reminder_triggered)
        self.reminder.session_ended.connect(self._on_session_ended)

        self.window.status_card.detection_btn.clicked.connect(self._toggle_detection)
        self.window.settings_btn.clicked.connect(self._open_settings)
        self.window.game_list.games_changed.connect(self._on_games_changed)
        self.window.history_widget.clear_btn.clicked.connect(self._clear_history)

        self.tray.show_requested.connect(self._show_window)
        self.tray.quit_requested.connect(self._quit)
        self.tray.toggle_detection.connect(self._toggle_detection)

    def _toggle_detection(self):
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
        self.reminder.start_session(game.exe_name, game.display_name)
        self.window.status_card.set_game_active(game.display_name)
        self.tray.update_status(f"プレイ中: {game.display_name}")
        self.tray.show_reminder("🎮 ゲーム検出", f"{game.display_name} のプレイを検知しました。")

    def _on_game_stopped(self, game):
        total = self.reminder.stop_session(game.exe_name)

        start = datetime.fromtimestamp(datetime.now().timestamp() - total)
        add_history_entry(game.display_name, game.exe_name, start, total)
        self._refresh_history()

        if not self.reminder.has_active_sessions():
            if self._detecting:
                self.window.status_card.set_detecting()
                self.tray.update_status("スキャン中")
            else:
                self.window.status_card.set_idle()

    def _on_time_updated(self, exe_name: str, elapsed: int, remaining: int):
        session = self.reminder.get_session(exe_name)
        if session:
            self.window.status_card.update_time(
                session.format_elapsed(),
                session.format_remaining(),
                session.progress,
            )

    def _on_reminder_triggered(self, exe_name: str, display_name: str, elapsed: int):
        session = self.reminder.get_session(exe_name)
        elapsed_str = session.format_elapsed() if session else "N/A"

        if self.settings.get("sound_enabled", True):
            try:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception:
                pass

        self.tray.show_reminder(
            "⏰ リマインダー",
            f"{display_name} のプレイ時間が制限に達しました！\nプレイ時間: {elapsed_str}",
        )

        popup = ReminderPopup(display_name, elapsed_str, self.window)
        popup.setStyleSheet(self.app.styleSheet())
        popup.exec()

    def _on_session_ended(self, exe_name: str, total_seconds: int):
        del exe_name, total_seconds

    def _open_settings(self):
        dialog = SettingsDialog(self.settings, self.window)
        if dialog.exec() == QDialog.Accepted:
            self.settings = dialog.get_settings()
            save_settings(self.settings)
            self._apply_settings()

    def _on_games_changed(self):
        self.settings["games"] = self.window.game_list.get_games()
        save_settings(self.settings)
        self.detector.set_monitored_games(self.settings["games"])

        custom_limits = {}
        for game in self.settings["games"]:
            if game.get("custom_time_limit") is not None:
                custom_limits[game["exe_name"].lower()] = game["custom_time_limit"]
        self.reminder.set_game_time_limits(custom_limits)

    def _refresh_history(self):
        history = load_history()
        self.window.history_widget.set_history(history)

    def _clear_history(self):
        from data.storage import save_history

        save_history([])
        self._refresh_history()

    def _show_window(self):
        self.window.show()
        self.window.activateWindow()
        self.window.raise_()

    def _quit(self):
        self.detector.stop()
        self.tray.hide()
        self.app.quit()

    def run(self) -> int:
        self.tray.show()

        if not self.settings.get("start_minimized", False):
            self.window.show()

        if self.settings.get("auto_start_detection", True):
            self._toggle_detection()

        return self.app.exec()


def main():
    try:
        os.chdir(sys._MEIPASS)
    except Exception:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

    app = GameStopReminderApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()

