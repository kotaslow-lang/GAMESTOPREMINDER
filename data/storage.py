"""
data/storage.py - JSON-based data persistence for settings and play history.
"""
import json
import os
from datetime import datetime

# Default data directory (in user's app data)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "appdata")

SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

DEFAULT_SETTINGS = {
    "default_time_limit_minutes": 60,
    "reminder_interval_minutes": 10,
    "sound_enabled": True,
    "auto_start_detection": True,
    "start_minimized": False,
    "games": [
        # Pre-populated with common game executables
        {"exe_name": "GTA5.exe", "display_name": "Grand Theft Auto V", "enabled": True, "custom_time_limit": None},
        {"exe_name": "VALORANT.exe", "display_name": "VALORANT", "enabled": True, "custom_time_limit": None},
        {"exe_name": "LeagueClient.exe", "display_name": "League of Legends", "enabled": True, "custom_time_limit": None},
        {"exe_name": "FortniteClient-Win64-Shipping.exe", "display_name": "Fortnite", "enabled": True, "custom_time_limit": None},
        {"exe_name": "Minecraft.exe", "display_name": "Minecraft", "enabled": True, "custom_time_limit": None},
        {"exe_name": "javaw.exe", "display_name": "Minecraft (Java)", "enabled": True, "custom_time_limit": None},
        {"exe_name": "eldenring.exe", "display_name": "Elden Ring", "enabled": True, "custom_time_limit": None},
        {"exe_name": "cs2.exe", "display_name": "Counter-Strike 2", "enabled": True, "custom_time_limit": None},
        {"exe_name": "RocketLeague.exe", "display_name": "Rocket League", "enabled": True, "custom_time_limit": None},
        {"exe_name": "ApexLegends.exe", "display_name": "Apex Legends", "enabled": True, "custom_time_limit": None},
        {"exe_name": "overwatch.exe", "display_name": "Overwatch 2", "enabled": True, "custom_time_limit": None},
        {"exe_name": "Genshin Impact.exe", "display_name": "Genshin Impact", "enabled": True, "custom_time_limit": None},
        {"exe_name": "ZenlessZoneZero.exe", "display_name": "Zenless Zone Zero", "enabled": True, "custom_time_limit": None},
        {"exe_name": "MONSTER HUNTER WILDS.exe", "display_name": "Monster Hunter Wilds", "enabled": True, "custom_time_limit": None},
        {"exe_name": "notepad.exe", "display_name": "Notepad (テスト用)", "enabled": False, "custom_time_limit": None},
    ]
}


def ensure_data_dir():
    """Ensure the data directory exists."""
    os.makedirs(DATA_DIR, exist_ok=True)


def load_settings() -> dict:
    """Load settings from JSON file, creating defaults if not present."""
    ensure_data_dir()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge with defaults to handle new keys added in updates
            merged = {**DEFAULT_SETTINGS, **data}
            return merged
        except (json.JSONDecodeError, IOError):
            pass
    # Return defaults
    save_settings(DEFAULT_SETTINGS)
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    """Save settings to JSON file."""
    ensure_data_dir()
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def load_history() -> list:
    """Load play history from JSON file."""
    ensure_data_dir()
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []


def save_history(history: list):
    """Save play history to JSON file."""
    ensure_data_dir()
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def add_history_entry(game_name: str, exe_name: str, start_time: datetime, duration_seconds: int):
    """Add a play session to history."""
    history = load_history()
    entry = {
        "game_name": game_name,
        "exe_name": exe_name,
        "start_time": start_time.isoformat(),
        "duration_seconds": duration_seconds,
        "date": start_time.strftime("%Y-%m-%d"),
    }
    history.insert(0, entry)
    # Keep only last 500 entries
    history = history[:500]
    save_history(history)
