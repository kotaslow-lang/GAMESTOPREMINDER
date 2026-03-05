"""
ui/main_window.py - Main application window with game status, timer, and history.
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QFrame, QProgressBar,
    QScrollArea, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon

from ui.game_list_widget import GameListWidget
from ui.settings_dialog import SettingsDialog


class StatusCard(QFrame):
    """Card displaying current game detection status and timer."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(24, 20, 24, 20)

        # Status indicator row
        status_row = QHBoxLayout()
        self.status_indicator = QLabel("●")
        self.status_indicator.setObjectName("statusIndicator")
        status_row.addWidget(self.status_indicator)

        self.status_label = QLabel("待機中")
        self.status_label.setObjectName("statusLabel")
        status_font = QFont()
        status_font.setPointSize(11)
        self.status_label.setFont(status_font)
        status_row.addWidget(self.status_label)
        status_row.addStretch()

        self.detection_btn = QPushButton("🔍 検知開始")
        self.detection_btn.setObjectName("detectionBtn")
        status_row.addWidget(self.detection_btn)

        layout.addLayout(status_row)

        # Game name
        self.game_name_label = QLabel("ゲーム未検出")
        self.game_name_label.setObjectName("gameName")
        game_font = QFont()
        game_font.setPointSize(18)
        game_font.setBold(True)
        self.game_name_label.setFont(game_font)
        self.game_name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.game_name_label)

        # Timer display
        timer_row = QHBoxLayout()

        # Elapsed time
        elapsed_block = QVBoxLayout()
        elapsed_header = QLabel("プレイ時間")
        elapsed_header.setObjectName("timerHeader")
        elapsed_header.setAlignment(Qt.AlignCenter)
        elapsed_block.addWidget(elapsed_header)

        self.elapsed_label = QLabel("00:00:00")
        self.elapsed_label.setObjectName("elapsedTime")
        elapsed_font = QFont("Consolas", 28)
        elapsed_font.setBold(True)
        self.elapsed_label.setFont(elapsed_font)
        self.elapsed_label.setAlignment(Qt.AlignCenter)
        elapsed_block.addWidget(self.elapsed_label)
        timer_row.addLayout(elapsed_block)

        # Separator
        sep = QFrame()
        sep.setObjectName("timerSep")
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(2)
        timer_row.addWidget(sep)

        # Remaining time
        remaining_block = QVBoxLayout()
        remaining_header = QLabel("残り時間")
        remaining_header.setObjectName("timerHeader")
        remaining_header.setAlignment(Qt.AlignCenter)
        remaining_block.addWidget(remaining_header)

        self.remaining_label = QLabel("--:--:--")
        self.remaining_label.setObjectName("remainingTime")
        remaining_font = QFont("Consolas", 28)
        remaining_font.setBold(True)
        self.remaining_label.setFont(remaining_font)
        self.remaining_label.setAlignment(Qt.AlignCenter)
        remaining_block.addWidget(self.remaining_label)
        timer_row.addLayout(remaining_block)

        layout.addLayout(timer_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("timeProgress")
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)

    def set_idle(self):
        """Set to idle/waiting state."""
        self.status_indicator.setText("●")
        self.status_indicator.setStyleSheet("color: #666;")
        self.status_label.setText("待機中")
        self.game_name_label.setText("ゲーム未検出")
        self.elapsed_label.setText("00:00:00")
        self.remaining_label.setText("--:--:--")
        self.progress_bar.setValue(0)

    def set_detecting(self):
        """Set to actively scanning state."""
        self.status_indicator.setText("●")
        self.status_indicator.setStyleSheet("color: #00f5d4;")
        self.status_label.setText("スキャン中...")
        self.game_name_label.setText("ゲーム未検出")

    def set_game_active(self, game_name: str):
        """Set to game detected state."""
        self.status_indicator.setText("●")
        self.status_indicator.setStyleSheet("color: #ff6b6b;")
        self.status_label.setText("ゲーム検出中")
        self.game_name_label.setText(f"🎮 {game_name}")

    def update_time(self, elapsed_str: str, remaining_str: str, progress: float):
        """Update timer display."""
        self.elapsed_label.setText(elapsed_str)
        self.remaining_label.setText(remaining_str)
        self.progress_bar.setValue(int(progress * 1000))

        # Change color when over time
        if progress >= 1.0:
            self.elapsed_label.setStyleSheet("color: #ff6b6b;")
            self.remaining_label.setStyleSheet("color: #ff6b6b;")
        else:
            self.elapsed_label.setStyleSheet("")
            self.remaining_label.setStyleSheet("")


class HistoryWidget(QWidget):
    """Display play history."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)

        # Header
        header = QHBoxLayout()
        title = QLabel("📊 プレイ履歴")
        title.setObjectName("sectionTitle")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)
        header.addStretch()

        self.clear_btn = QPushButton("🗑️ クリア")
        self.clear_btn.setObjectName("clearHistoryBtn")
        header.addWidget(self.clear_btn)
        layout.addLayout(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setObjectName("historyScroll")

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(4)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.addStretch()

        scroll.setWidget(self.container)
        layout.addWidget(scroll)

        self.empty_label = QLabel("まだ履歴がありません")
        self.empty_label.setObjectName("emptyLabel")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.container_layout.insertWidget(0, self.empty_label)

    def set_history(self, history: list):
        """Populate history entries."""
        # Clear
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not history:
            self.empty_label.show()
            return

        self.empty_label.hide()

        for entry in history[:100]:  # Show last 100
            card = QFrame()
            card.setObjectName("historyCard")
            card.setFrameShape(QFrame.StyledPanel)

            h_layout = QHBoxLayout(card)
            h_layout.setContentsMargins(12, 8, 12, 8)

            # Game info
            info = QVBoxLayout()
            name = QLabel(entry.get("game_name", entry.get("exe_name", "Unknown")))
            name.setObjectName("historyGameName")
            name_font = QFont()
            name_font.setBold(True)
            name.setFont(name_font)
            info.addWidget(name)

            date_str = entry.get("date", "")
            start = entry.get("start_time", "")
            if start:
                try:
                    dt = datetime.fromisoformat(start)
                    date_str = dt.strftime("%Y/%m/%d %H:%M")
                except ValueError:
                    pass
            date_label = QLabel(f"📅 {date_str}")
            date_label.setObjectName("historyDate")
            date_font = QFont()
            date_font.setPointSize(8)
            date_label.setFont(date_font)
            info.addWidget(date_label)

            h_layout.addLayout(info, 1)

            # Duration
            secs = entry.get("duration_seconds", 0)
            hours = secs // 3600
            mins = (secs % 3600) // 60
            if hours > 0:
                dur_text = f"{hours}時間{mins}分"
            else:
                dur_text = f"{mins}分"
            dur_label = QLabel(dur_text)
            dur_label.setObjectName("historyDuration")
            dur_font = QFont()
            dur_font.setPointSize(12)
            dur_font.setBold(True)
            dur_label.setFont(dur_font)
            h_layout.addWidget(dur_label)

            self.container_layout.insertWidget(
                self.container_layout.count() - 1, card
            )


class MainWindow(QMainWindow):
    """Main application window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎮 Game Stop Reminder")
        self.setMinimumSize(520, 680)
        self.resize(560, 740)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header_layout = QHBoxLayout()

        app_title = QLabel("🎮 Game Stop Reminder")
        app_title.setObjectName("appTitle")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        app_title.setFont(title_font)
        header_layout.addWidget(app_title)

        header_layout.addStretch()

        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setFixedSize(36, 36)
        self.settings_btn.setToolTip("設定")
        header_layout.addWidget(self.settings_btn)

        self.minimize_btn = QPushButton("─")
        self.minimize_btn.setObjectName("minimizeBtn")
        self.minimize_btn.setFixedSize(36, 36)
        self.minimize_btn.setToolTip("トレイに最小化")
        self.minimize_btn.clicked.connect(self._minimize_to_tray)
        header_layout.addWidget(self.minimize_btn)

        main_layout.addLayout(header_layout)

        # Status card
        self.status_card = StatusCard()
        main_layout.addWidget(self.status_card)

        # Tab widget for Games / History
        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")

        # Games tab
        self.game_list = GameListWidget()
        self.tabs.addTab(self.game_list, "🎮 ゲーム一覧")

        # History tab
        self.history_widget = HistoryWidget()
        self.tabs.addTab(self.history_widget, "📊 履歴")

        main_layout.addWidget(self.tabs)

    def _minimize_to_tray(self):
        self.hide()

    def closeEvent(self, event):
        """Minimize to tray instead of closing."""
        event.ignore()
        self.hide()
