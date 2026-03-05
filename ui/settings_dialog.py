"""
ui/settings_dialog.py - Settings dialog for configuring reminders.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QCheckBox, QPushButton, QDialogButtonBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class SettingsDialog(QDialog):
    """Dialog for editing global app settings."""
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️  設定")
        self.setMinimumWidth(420)
        self.settings = settings.copy()

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("アプリ設定")
        title.setObjectName("settingsTitle")
        title_font = QFont()
        title_font.setPointSize(15)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Timer settings group
        timer_group = QGroupBox("⏱  タイマー設定")
        timer_layout = QFormLayout()
        timer_layout.setSpacing(12)

        self.time_limit_spin = QSpinBox()
        self.time_limit_spin.setRange(1, 600)
        self.time_limit_spin.setValue(settings.get("default_time_limit_minutes", 60))
        self.time_limit_spin.setSuffix(" 分")
        timer_layout.addRow("デフォルト制限時間:", self.time_limit_spin)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 120)
        self.interval_spin.setValue(settings.get("reminder_interval_minutes", 10))
        self.interval_spin.setSuffix(" 分")
        timer_layout.addRow("リマインド間隔:", self.interval_spin)

        timer_group.setLayout(timer_layout)
        layout.addWidget(timer_group)

        # Notification settings group
        notif_group = QGroupBox("🔔  通知設定")
        notif_layout = QVBoxLayout()

        self.sound_check = QCheckBox("アラーム音を鳴らす")
        self.sound_check.setChecked(settings.get("sound_enabled", True))
        notif_layout.addWidget(self.sound_check)

        notif_group.setLayout(notif_layout)
        layout.addWidget(notif_group)

        # Startup settings group
        startup_group = QGroupBox("🚀  起動設定")
        startup_layout = QVBoxLayout()

        self.auto_detect_check = QCheckBox("起動時に自動でゲーム検知を開始")
        self.auto_detect_check.setChecked(settings.get("auto_start_detection", True))
        startup_layout.addWidget(self.auto_detect_check)

        self.start_minimized_check = QCheckBox("最小化状態で起動（トレイ常駐）")
        self.start_minimized_check.setChecked(settings.get("start_minimized", False))
        startup_layout.addWidget(self.start_minimized_check)

        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)

        layout.addStretch()

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self) -> dict:
        """Return updated settings dict."""
        self.settings["default_time_limit_minutes"] = self.time_limit_spin.value()
        self.settings["reminder_interval_minutes"] = self.interval_spin.value()
        self.settings["sound_enabled"] = self.sound_check.isChecked()
        self.settings["auto_start_detection"] = self.auto_detect_check.isChecked()
        self.settings["start_minimized"] = self.start_minimized_check.isChecked()
        return self.settings
