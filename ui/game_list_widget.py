"""
ui/game_list_widget.py - Widget for managing the monitored games list.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QCheckBox, QSpinBox,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont


class GameEditDialog(QDialog):
    """Dialog for adding/editing a game entry."""
    def __init__(self, parent=None, game_data=None):
        super().__init__(parent)
        self.setWindowTitle("ゲームの追加" if game_data is None else "ゲームの編集")
        self.setMinimumWidth(380)
        self.setStyleSheet("")  # Inherit parent style

        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.exe_input = QLineEdit()
        self.exe_input.setPlaceholderText("例: game.exe")
        layout.addRow("実行ファイル名 (exe):", self.exe_input)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例: My Game")
        layout.addRow("表示名:", self.name_input)

        self.custom_time_check = QCheckBox("個別に制限時間を設定")
        layout.addRow(self.custom_time_check)

        self.time_spin = QSpinBox()
        self.time_spin.setRange(1, 600)
        self.time_spin.setValue(60)
        self.time_spin.setSuffix(" 分")
        self.time_spin.setEnabled(False)
        layout.addRow("制限時間:", self.time_spin)

        self.custom_time_check.toggled.connect(self.time_spin.setEnabled)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        if game_data:
            self.exe_input.setText(game_data.get("exe_name", ""))
            self.name_input.setText(game_data.get("display_name", ""))
            if game_data.get("custom_time_limit") is not None:
                self.custom_time_check.setChecked(True)
                self.time_spin.setValue(game_data["custom_time_limit"])

    def _validate_and_accept(self):
        if not self.exe_input.text().strip():
            QMessageBox.warning(self, "エラー", "実行ファイル名を入力してください。")
            return
        if not self.name_input.text().strip():
            self.name_input.setText(self.exe_input.text().replace(".exe", ""))
        self.accept()

    def get_data(self) -> dict:
        return {
            "exe_name": self.exe_input.text().strip(),
            "display_name": self.name_input.text().strip(),
            "enabled": True,
            "custom_time_limit": self.time_spin.value() if self.custom_time_check.isChecked() else None,
        }


class GameCard(QFrame):
    """A single game entry card in the list."""
    toggled = Signal(str, bool)     # exe_name, enabled
    edit_requested = Signal(str)    # exe_name
    delete_requested = Signal(str)  # exe_name

    def __init__(self, game_data: dict, parent=None):
        super().__init__(parent)
        self.game_data = game_data
        self.setObjectName("gameCard")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(game_data.get("enabled", True))
        self.enabled_check.toggled.connect(
            lambda checked: self.toggled.emit(self.game_data["exe_name"], checked)
        )
        layout.addWidget(self.enabled_check)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        name_label = QLabel(game_data.get("display_name", ""))
        name_label.setObjectName("gameName")
        name_font = QFont()
        name_font.setPointSize(11)
        name_font.setBold(True)
        name_label.setFont(name_font)
        info_layout.addWidget(name_label)

        exe_label = QLabel(game_data.get("exe_name", ""))
        exe_label.setObjectName("gameExe")
        exe_font = QFont()
        exe_font.setPointSize(8)
        exe_label.setFont(exe_font)
        info_layout.addWidget(exe_label)

        layout.addLayout(info_layout, 1)

        # Time limit display
        time_limit = game_data.get("custom_time_limit")
        if time_limit is not None:
            time_label = QLabel(f"⏱ {time_limit}分")
            time_label.setObjectName("gameTimeLimit")
            layout.addWidget(time_label)

        edit_btn = QPushButton("✏️")
        edit_btn.setObjectName("gameActionBtn")
        edit_btn.setFixedSize(32, 32)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.game_data["exe_name"]))
        layout.addWidget(edit_btn)

        del_btn = QPushButton("🗑️")
        del_btn.setObjectName("gameActionBtn")
        del_btn.setFixedSize(32, 32)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.game_data["exe_name"]))
        layout.addWidget(del_btn)


class GameListWidget(QWidget):
    """Widget that displays and manages the list of monitored games."""
    games_changed = Signal()  # Emitted when the game list is modified

    def __init__(self, parent=None):
        super().__init__(parent)
        self._games = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        title = QLabel("🎮 監視対象ゲーム")
        title.setObjectName("sectionTitle")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("＋ ゲームを追加")
        add_btn.setObjectName("addGameBtn")
        add_btn.clicked.connect(self._add_game)
        header.addWidget(add_btn)
        layout.addLayout(header)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 ゲームを検索...")
        self.search_input.setObjectName("searchInput")
        self.search_input.textChanged.connect(self._filter_games)
        layout.addWidget(self.search_input)

        # Scroll area for game cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("gameListScroll")
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(6)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area)

    def set_games(self, games: list[dict]):
        """Set the full list of games and rebuild the UI."""
        self._games = games
        self._rebuild_cards()

    def get_games(self) -> list[dict]:
        return self._games

    def _rebuild_cards(self, filter_text: str = ""):
        # Clear existing cards
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for game in self._games:
            if filter_text:
                search = filter_text.lower()
                if (search not in game.get("display_name", "").lower()
                        and search not in game.get("exe_name", "").lower()):
                    continue

            card = GameCard(game)
            card.toggled.connect(self._on_game_toggled)
            card.edit_requested.connect(self._edit_game)
            card.delete_requested.connect(self._delete_game)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _filter_games(self, text: str):
        self._rebuild_cards(text)

    def _add_game(self):
        dialog = GameEditDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            # Check for duplicate exe name
            for g in self._games:
                if g["exe_name"].lower() == data["exe_name"].lower():
                    QMessageBox.warning(self, "重複", "同じ実行ファイル名のゲームが既に存在します。")
                    return
            self._games.append(data)
            self._rebuild_cards(self.search_input.text())
            self.games_changed.emit()

    def _edit_game(self, exe_name: str):
        for i, g in enumerate(self._games):
            if g["exe_name"] == exe_name:
                dialog = GameEditDialog(self, g)
                if dialog.exec() == QDialog.Accepted:
                    self._games[i] = dialog.get_data()
                    self._rebuild_cards(self.search_input.text())
                    self.games_changed.emit()
                break

    def _delete_game(self, exe_name: str):
        reply = QMessageBox.question(
            self, "確認",
            f"「{exe_name}」を監視リストから削除しますか？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._games = [g for g in self._games if g["exe_name"] != exe_name]
            self._rebuild_cards(self.search_input.text())
            self.games_changed.emit()

    def _on_game_toggled(self, exe_name: str, enabled: bool):
        for g in self._games:
            if g["exe_name"] == exe_name:
                g["enabled"] = enabled
                self.games_changed.emit()
                break
