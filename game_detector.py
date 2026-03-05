"""
game_detector.py - Detects running game processes using psutil.
"""
import psutil
from PySide6.QtCore import QObject, Signal, QTimer


class DetectedGame:
    """Represents a detected running game."""
    def __init__(self, exe_name: str, display_name: str, pid: int):
        self.exe_name = exe_name
        self.display_name = display_name
        self.pid = pid

    def __eq__(self, other):
        if isinstance(other, DetectedGame):
            return self.exe_name.lower() == other.exe_name.lower()
        return False

    def __hash__(self):
        return hash(self.exe_name.lower())


class GameDetector(QObject):
    """
    Periodically scans running processes and emits signals
    when a monitored game starts or stops.
    """
    game_started = Signal(object)   # DetectedGame
    game_stopped = Signal(object)   # DetectedGame

    def __init__(self, parent=None):
        super().__init__(parent)
        self._monitored_games = {}   # exe_name_lower -> {"exe_name": ..., "display_name": ..., "enabled": bool}
        self._active_games = {}      # exe_name_lower -> DetectedGame
        self._scan_timer = QTimer(self)
        self._scan_timer.setInterval(5000)  # 5 second scan interval
        self._scan_timer.timeout.connect(self._scan_processes)

    def set_monitored_games(self, games: list[dict]):
        """
        Update the list of games to monitor.
        Each dict should have: exe_name, display_name, enabled
        """
        self._monitored_games = {}
        for g in games:
            if g.get("enabled", True):
                key = g["exe_name"].lower()
                self._monitored_games[key] = {
                    "exe_name": g["exe_name"],
                    "display_name": g.get("display_name", g["exe_name"]),
                }

    def start(self):
        """Start periodic scanning."""
        self._scan_processes()  # Immediate first scan
        self._scan_timer.start()

    def stop(self):
        """Stop scanning."""
        self._scan_timer.stop()

    def get_active_games(self) -> list:
        """Return list of currently active DetectedGame objects."""
        return list(self._active_games.values())

    def _scan_processes(self):
        """Scan all running processes and detect game starts/stops."""
        current_running = {}

        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    name = proc.info['name']
                    if name:
                        key = name.lower()
                        if key in self._monitored_games:
                            info = self._monitored_games[key]
                            current_running[key] = DetectedGame(
                                exe_name=info["exe_name"],
                                display_name=info["display_name"],
                                pid=proc.info['pid']
                            )
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception:
            return

        # Detect newly started games
        for key, game in current_running.items():
            if key not in self._active_games:
                self._active_games[key] = game
                self.game_started.emit(game)

        # Detect stopped games
        stopped_keys = []
        for key, game in self._active_games.items():
            if key not in current_running:
                stopped_keys.append(key)
                self.game_stopped.emit(game)

        for key in stopped_keys:
            del self._active_games[key]
