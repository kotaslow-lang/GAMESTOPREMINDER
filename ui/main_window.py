"""
ui/main_window.py - Main application window with near-future UI effects.
"""
from datetime import datetime

from PySide6.QtCore import QEasingCurve, QEvent, QParallelAnimationGroup, QPoint, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedLayout,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ui.futuristic_effects import DynamicBackgroundWidget, ScanlineOverlay, fade_in_widget
from ui.game_list_widget import GameListWidget


class StatusCard(QFrame):
    """Card displaying current game detection status and timer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusCard")
        self.setProperty("scanState", "idle")
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(24, 20, 24, 20)

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

        self.detection_btn = QPushButton("検知開始")
        self.detection_btn.setObjectName("detectionBtn")
        status_row.addWidget(self.detection_btn)

        layout.addLayout(status_row)

        self.game_name_label = QLabel("ゲーム未検出")
        self.game_name_label.setObjectName("statusGameName")
        game_font = QFont()
        game_font.setPointSize(18)
        game_font.setBold(True)
        self.game_name_label.setFont(game_font)
        self.game_name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.game_name_label)

        timer_row = QHBoxLayout()

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

        sep = QFrame()
        sep.setObjectName("timerSep")
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(2)
        timer_row.addWidget(sep)

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

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("timeProgress")
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)

        self._progress_anim = QPropertyAnimation(self.progress_bar, b"value", self)
        self._progress_anim.setDuration(320)
        self._progress_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._scan_overlay = ScanlineOverlay(self)
        self._scan_overlay.set_active(False)
        self._scan_overlay.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scan_overlay.setGeometry(self.rect())

    def _refresh_card_style(self):
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _set_scan_state(self, state: str):
        self.setProperty("scanState", state)
        self._refresh_card_style()

    def set_idle(self):
        """Set to idle/waiting state."""
        self._set_scan_state("idle")
        self.status_indicator.setStyleSheet("color: #7A8CA5;")
        self.status_label.setText("待機中")
        self.game_name_label.setText("ゲーム未検出")
        self.elapsed_label.setText("00:00:00")
        self.remaining_label.setText("--:--:--")
        self.elapsed_label.setStyleSheet("")
        self.remaining_label.setStyleSheet("")

        self._progress_anim.stop()
        self.progress_bar.setValue(0)
        self._scan_overlay.set_active(False)

    def set_detecting(self):
        """Set to actively scanning state."""
        self._set_scan_state("detecting")
        self.status_indicator.setStyleSheet("color: #00EDFF;")
        self.status_label.setText("スキャン中...")
        self.game_name_label.setText("ゲーム未検出")
        self._scan_overlay.set_active(True, QColor("#00EDFF"))

    def set_game_active(self, game_name: str):
        """Set to game detected state."""
        self._set_scan_state("active")
        self.status_indicator.setStyleSheet("color: #FF5AC9;")
        self.status_label.setText("ゲーム検出中")
        self.game_name_label.setText(f"🎮 {game_name}")
        self._scan_overlay.set_active(True, QColor("#FF5AC9"))

    def update_time(self, elapsed_str: str, remaining_str: str, progress: float):
        """Update timer display."""
        self.elapsed_label.setText(elapsed_str)
        self.remaining_label.setText(remaining_str)

        target_value = int(max(0.0, min(progress, 1.0)) * 1000)
        self._progress_anim.stop()
        self._progress_anim.setStartValue(self.progress_bar.value())
        self._progress_anim.setEndValue(target_value)
        self._progress_anim.start()

        if progress >= 1.0:
            self.elapsed_label.setStyleSheet("color: #FF6585;")
            self.remaining_label.setStyleSheet("color: #FF6585;")
        else:
            self.elapsed_label.setStyleSheet("")
            self.remaining_label.setStyleSheet("")


class HistoryWidget(QWidget):
    """Display play history."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)

        header = QHBoxLayout()
        title = QLabel("プレイ履歴")
        title.setObjectName("sectionTitle")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)
        header.addStretch()

        self.clear_btn = QPushButton("クリア")
        self.clear_btn.setObjectName("clearHistoryBtn")
        header.addWidget(self.clear_btn)
        layout.addLayout(header)

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
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not history:
            self.empty_label.show()
            return

        self.empty_label.hide()

        for entry in history[:100]:
            card = QFrame()
            card.setObjectName("historyCard")
            card.setFrameShape(QFrame.StyledPanel)

            h_layout = QHBoxLayout(card)
            h_layout.setContentsMargins(12, 8, 12, 8)

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

            self.container_layout.insertWidget(self.container_layout.count() - 1, card)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setWindowTitle("Game Stop Reminder")
        self.setMinimumSize(560, 720)
        self.resize(620, 780)

        self._dragging = False
        self._drag_offset = QPoint()

        central = QWidget()
        self.setCentralWidget(central)

        stack = QStackedLayout(central)
        stack.setStackingMode(QStackedLayout.StackAll)

        self.background = DynamicBackgroundWidget()
        stack.addWidget(self.background)

        content = QWidget()
        content.setObjectName("contentShell")
        stack.addWidget(content)
        stack.setCurrentWidget(content)

        main_layout = QVBoxLayout(content)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(18, 18, 18, 18)

        self.header_strip = QFrame()
        self.header_strip.setObjectName("headerStrip")
        header_layout = QHBoxLayout(self.header_strip)
        header_layout.setContentsMargins(14, 12, 14, 12)

        self.app_title = QLabel("GAME STOP REMINDER")
        self.app_title.setObjectName("appTitle")
        title_font = QFont("Bahnschrift", 16)
        title_font.setBold(True)
        self.app_title.setFont(title_font)
        header_layout.addWidget(self.app_title)

        header_layout.addStretch()

        self.settings_btn = QPushButton("\uE713")
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setFixedSize(36, 36)
        self.settings_btn.setToolTip("設定")
        header_layout.addWidget(self.settings_btn)

        self.minimize_btn = QPushButton("\uE8BB")
        self.minimize_btn.setObjectName("minimizeBtn")
        self.minimize_btn.setFixedSize(36, 36)
        self.minimize_btn.setToolTip("閉じる (トレイに最小化)")
        self.minimize_btn.clicked.connect(self._minimize_to_tray)
        header_layout.addWidget(self.minimize_btn)

        main_layout.addWidget(self.header_strip)

        self.status_card = StatusCard()
        main_layout.addWidget(self.status_card)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")

        self.game_list = GameListWidget()
        self.tabs.addTab(self.game_list, "ゲーム一覧")

        self.history_widget = HistoryWidget()
        self.tabs.addTab(self.history_widget, "履歴")

        self.tabs.currentChanged.connect(self._animate_tab_transition)
        main_layout.addWidget(self.tabs)

        self._intro_animation = None
        self._tab_animation = None
        self._intro_played = False

        self.header_strip.installEventFilter(self)
        self.app_title.installEventFilter(self)

        QTimer.singleShot(80, self._play_intro_animation)

    def _play_intro_animation(self):
        if self._intro_played:
            return
        self._intro_played = True

        group = QParallelAnimationGroup(self)
        group.addAnimation(fade_in_widget(self.header_strip, delay_ms=0, duration_ms=420))
        group.addAnimation(fade_in_widget(self.status_card, delay_ms=80, duration_ms=520))
        group.addAnimation(fade_in_widget(self.tabs, delay_ms=150, duration_ms=540))

        self._intro_animation = group
        self._intro_animation.start()

    def _animate_tab_transition(self, index: int):
        page = self.tabs.widget(index)
        if page is None:
            return

        effect = QGraphicsOpacityEffect(page)
        effect.setOpacity(0.0)
        page.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity", page)
        animation.setDuration(260)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)

        def _cleanup():
            page.setGraphicsEffect(None)

        animation.finished.connect(_cleanup)
        self._tab_animation = animation
        self._tab_animation.start()

    def _minimize_to_tray(self):
        self.hide()

    def eventFilter(self, obj, event):
        if obj in (self.header_strip, self.app_title):
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._dragging = True
                self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return True
            if event.type() == QEvent.MouseMove and self._dragging and event.buttons() & Qt.LeftButton:
                self.move(event.globalPosition().toPoint() - self._drag_offset)
                return True
            if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self._dragging = False
                return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        """Minimize to tray instead of closing."""
        event.ignore()
        self.hide()

