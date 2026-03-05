"""
reminder_manager.py - Tracks play time per game and triggers reminders.
"""
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QTimer


class GameSession:
    """Tracks a single game play session."""
    def __init__(self, exe_name: str, display_name: str, time_limit_minutes: int):
        self.exe_name = exe_name
        self.display_name = display_name
        self.time_limit_minutes = time_limit_minutes
        self.start_time = datetime.now()
        self.elapsed_seconds = 0
        self.reminder_sent_count = 0

    @property
    def remaining_seconds(self) -> int:
        limit = self.time_limit_minutes * 60
        remaining = limit - self.elapsed_seconds
        return max(0, remaining)

    @property
    def is_over_limit(self) -> bool:
        return self.elapsed_seconds >= self.time_limit_minutes * 60

    @property
    def progress(self) -> float:
        """Return progress as 0.0 to 1.0."""
        limit = self.time_limit_minutes * 60
        if limit <= 0:
            return 0.0
        return min(1.0, self.elapsed_seconds / limit)

    def format_elapsed(self) -> str:
        """Format elapsed time as HH:MM:SS."""
        h = self.elapsed_seconds // 3600
        m = (self.elapsed_seconds % 3600) // 60
        s = self.elapsed_seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def format_remaining(self) -> str:
        """Format remaining time as HH:MM:SS."""
        r = self.remaining_seconds
        h = r // 3600
        m = (r % 3600) // 60
        s = r % 60
        return f"{h:02d}:{m:02d}:{s:02d}"


class ReminderManager(QObject):
    """
    Manages play-time tracking for active games and emits
    reminder signals when time limits are reached.
    """
    # Signals
    time_updated = Signal(str, int, int)      # exe_name, elapsed_sec, remaining_sec
    reminder_triggered = Signal(str, str, int) # exe_name, display_name, elapsed_sec
    session_ended = Signal(str, int)           # exe_name, total_seconds

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sessions = {}   # exe_name_lower -> GameSession
        self._default_time_limit = 60  # minutes
        self._reminder_interval = 10   # minutes
        self._game_time_limits = {}    # exe_name_lower -> minutes (custom per-game)

        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(1000)  # 1 second tick
        self._tick_timer.timeout.connect(self._tick)

    def set_default_time_limit(self, minutes: int):
        self._default_time_limit = minutes

    def set_reminder_interval(self, minutes: int):
        self._reminder_interval = minutes

    def set_game_time_limits(self, limits: dict):
        """Set per-game custom time limits. {exe_name_lower: minutes}"""
        self._game_time_limits = limits

    def start_session(self, exe_name: str, display_name: str):
        """Start tracking a game session."""
        key = exe_name.lower()
        if key in self._sessions:
            return  # Already tracking

        time_limit = self._game_time_limits.get(key, self._default_time_limit)
        session = GameSession(exe_name, display_name, time_limit)
        self._sessions[key] = session

        if not self._tick_timer.isActive():
            self._tick_timer.start()

    def stop_session(self, exe_name: str) -> int:
        """Stop tracking a game session. Returns total elapsed seconds."""
        key = exe_name.lower()
        session = self._sessions.pop(key, None)
        if session:
            self.session_ended.emit(exe_name, session.elapsed_seconds)
            if not self._sessions:
                self._tick_timer.stop()
            return session.elapsed_seconds
        return 0

    def get_session(self, exe_name: str) -> GameSession | None:
        """Get the current session for a game."""
        return self._sessions.get(exe_name.lower())

    def get_all_sessions(self) -> dict:
        """Get all active sessions."""
        return dict(self._sessions)

    def has_active_sessions(self) -> bool:
        return len(self._sessions) > 0

    def _tick(self):
        """Called every second to update all sessions."""
        for key, session in self._sessions.items():
            session.elapsed_seconds += 1

            # Emit time update
            self.time_updated.emit(
                session.exe_name,
                session.elapsed_seconds,
                session.remaining_seconds
            )

            # Check if reminder should trigger
            if session.is_over_limit:
                # First reminder at the limit, subsequent at intervals
                limit_sec = session.time_limit_minutes * 60
                interval_sec = self._reminder_interval * 60
                over_by = session.elapsed_seconds - limit_sec

                should_remind = False
                if session.reminder_sent_count == 0 and over_by == 0:
                    should_remind = True
                elif interval_sec > 0 and over_by > 0 and over_by % interval_sec == 0:
                    should_remind = True

                if should_remind:
                    session.reminder_sent_count += 1
                    self.reminder_triggered.emit(
                        session.exe_name,
                        session.display_name,
                        session.elapsed_seconds
                    )
