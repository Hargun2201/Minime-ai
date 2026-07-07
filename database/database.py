import sqlite3
import os
import datetime
from typing import List, Dict, Any, Tuple, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "minime.db")

class DatabaseManager:
    """
    Thread-safe Database Manager for SQLite operations in MiniMe AI.
    Opens and closes connections per operation to ensure safety across PySide GUI and background threads.
    """
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = os.path.abspath(db_path)
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.initialize_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_schema(self):
        """Initializes tables if they do not exist."""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS user_stats (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS water_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount INTEGER,
                timestamp TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS focus_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                duration_minutes INTEGER,
                type TEXT,
                timestamp TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                xp_reward INTEGER DEFAULT 10,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS mood_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mood TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        ]
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for q in queries:
                cursor.execute(q)
            conn.commit()
            
        # Seed default settings if empty
        self._seed_default_settings()

    def _seed_default_settings(self):
        defaults = {
            "theme": "dark",
            "username": "Hargun",
            "avatar_style": "classic",
            "water_target_ml": "2000",
            "water_interval_mins": "60",
            "pomodoro_duration": "25",
            "short_break_duration": "5",
            "long_break_duration": "15",
            "voice_enabled": "1",
            "sound_enabled": "1",
            "transparency": "0.9",
            "startup_launch": "0",
            "animation_speed": "1.0",
            "ai_api_key": ""
        }
        
        default_stats = {
            "level": "1",
            "xp": "0",
            "streak": "0",
            "last_login_date": ""
        }
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for key, val in defaults.items():
                cursor.execute("INSERT OR IGNORE INTO user_settings (key, value) VALUES (?, ?)", (key, val))
            for key, val in default_stats.items():
                cursor.execute("INSERT OR IGNORE INTO user_stats (key, value) VALUES (?, ?)", (key, val))
            conn.commit()

    # --- SETTINGS CRUD ---
    def get_setting(self, key: str, default: Any = None) -> Any:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: Any):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO user_settings (key, value) VALUES (?, ?)",
                (key, str(value))
            )
            conn.commit()

    # --- STATS CRUD ---
    def get_stat(self, key: str, default: Any = None) -> Any:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_stats WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def set_stat(self, key: str, value: Any):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO user_stats (key, value) VALUES (?, ?)",
                (key, str(value))
            )
            conn.commit()

    # --- WATER LOGS ---
    def add_water(self, amount_ml: int, timestamp: Optional[str] = None) -> int:
        """Logs water consumption. Returns daily total."""
        if not timestamp:
            timestamp = datetime.datetime.now().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO water_logs (amount, timestamp) VALUES (?, ?)",
                (amount_ml, timestamp)
            )
            conn.commit()
        return self.get_daily_water(timestamp[:10])

    def get_daily_water(self, date_str: str) -> int:
        """date_str in YYYY-MM-DD format"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT SUM(amount) as total FROM water_logs WHERE timestamp LIKE ?",
                (f"{date_str}%",)
            )
            row = cursor.fetchone()
            return row["total"] if row and row["total"] else 0

    def get_weekly_water_data(self) -> List[Tuple[str, int]]:
        """Returns list of (date_str, daily_total) for the last 7 days."""
        data = []
        today = datetime.date.today()
        for i in range(6, -1, -1):
            day = today - datetime.timedelta(days=i)
            day_str = day.isoformat()
            total = self.get_daily_water(day_str)
            data.append((day_str, total))
        return data

    # --- FOCUS SESSIONS ---
    def add_focus_session(self, duration_mins: int, session_type: str):
        timestamp = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO focus_sessions (duration_minutes, type, timestamp) VALUES (?, ?, ?)",
                (duration_mins, session_type, timestamp)
            )
            conn.commit()

    def get_weekly_focus_data(self) -> Dict[str, List[Tuple[str, int]]]:
        """Returns study & coding minutes grouped by day for last 7 days."""
        today = datetime.date.today()
        study_data = []
        coding_data = []
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for i in range(6, -1, -1):
                day = today - datetime.timedelta(days=i)
                day_str = day.isoformat()
                
                cursor.execute(
                    "SELECT SUM(duration_minutes) as total FROM focus_sessions WHERE timestamp LIKE ? AND type = 'study'",
                    (f"{day_str}%",)
                )
                r_study = cursor.fetchone()
                study_val = r_study["total"] if r_study and r_study["total"] else 0
                study_data.append((day_str, study_val))
                
                cursor.execute(
                    "SELECT SUM(duration_minutes) as total FROM focus_sessions WHERE timestamp LIKE ? AND type = 'coding'",
                    (f"{day_str}%",)
                )
                r_coding = cursor.fetchone()
                coding_val = r_coding["total"] if r_coding and r_coding["total"] else 0
                coding_data.append((day_str, coding_val))
                
        return {"study": study_data, "coding": coding_data}

    # --- TASKS ---
    def add_task(self, title: str, xp_reward: int = 10) -> int:
        created_at = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (title, status, xp_reward, created_at) VALUES (?, 'pending', ?, ?)",
                (title, xp_reward, created_at)
            )
            conn.commit()
            return cursor.lastrowid

    def toggle_task(self, task_id: int, completed: bool) -> int:
        """Toggles status. If completed, logs completion time and returns XP gained."""
        status = "completed" if completed else "pending"
        completed_at = datetime.datetime.now().isoformat() if completed else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT xp_reward FROM tasks WHERE id = ?", (task_id,)
            )
            row = cursor.fetchone()
            xp = row["xp_reward"] if row else 0
            
            cursor.execute(
                "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
                (status, completed_at, task_id)
            )
            conn.commit()
            return xp if completed else -xp

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_task(self, task_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()

    # --- MOOD LOGS ---
    def log_mood(self, mood: str):
        timestamp = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO mood_logs (mood, timestamp) VALUES (?, ?)",
                (mood, timestamp)
            )
            conn.commit()

    def get_mood_trends(self, limit: int = 10) -> List[Tuple[str, str]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp, mood FROM mood_logs ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return [(row["timestamp"], row["mood"]) for row in cursor.fetchall()]
