"""SQLite Database manager for Website Blocker."""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple
from database.models import Website, Session, Schedule, Setting
from utils.config import DB_PATH
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages SQLite database connections and operations."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Returns a SQLite connection configured with WAL journal mode and row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def initialize(self) -> None:
        """Creates the database schema if tables do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Websites table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS websites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT UNIQUE NOT NULL,
                    category_id INTEGER,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_seconds INTEGER NOT NULL,
                    type TEXT NOT NULL DEFAULT 'manual',
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL
                );
            """)

            # Schedules table (ready for post-MVP / extensions)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    days TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );
            """)

            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)
            conn.commit()
            logger.info("Database initialized successfully at %s", self.db_path)

    # -------------------------------------------------------------
    # Websites Operations
    # -------------------------------------------------------------

    def get_websites(self) -> List[Website]:
        """Returns all configured websites ordered by id descending."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, domain, category_id, enabled, created_at, updated_at FROM websites ORDER BY id DESC"
            )
            rows = cursor.fetchall()
            return [
                Website(
                    id=row["id"],
                    domain=row["domain"],
                    category_id=row["category_id"],
                    enabled=bool(row["enabled"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    def get_website_by_domain(self, domain: str) -> Optional[Website]:
        """Fetches a single website record by domain."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, domain, category_id, enabled, created_at, updated_at FROM websites WHERE domain = ?",
                (domain.lower(),),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Website(
                id=row["id"],
                domain=row["domain"],
                category_id=row["category_id"],
                enabled=bool(row["enabled"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def add_website(self, domain: str, category_id: Optional[int] = None, enabled: bool = True) -> Website:
        """Adds a new website to the database."""
        now = datetime.now().isoformat()
        clean_domain = domain.strip().lower()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO websites (domain, category_id, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (clean_domain, category_id, 1 if enabled else 0, now, now),
            )
            conn.commit()
            new_id = cursor.lastrowid
            logger.info("Added website '%s' with id %d", clean_domain, new_id)
            return Website(
                id=new_id,
                domain=clean_domain,
                category_id=category_id,
                enabled=enabled,
                created_at=now,
                updated_at=now,
            )

    def remove_website(self, website_id: int) -> bool:
        """Deletes a website by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM websites WHERE id = ?", (website_id,))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info("Removed website with id %d", website_id)
            return success

    def toggle_website(self, website_id: int, enabled: bool) -> bool:
        """Enables or disables a website."""
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE websites SET enabled = ?, updated_at = ? WHERE id = ?",
                (1 if enabled else 0, now, website_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    # -------------------------------------------------------------
    # Session Operations
    # -------------------------------------------------------------

    def create_session(
        self,
        duration_seconds: int,
        session_type: str = "manual",
        status: str = "active",
        start_time: Optional[str] = None,
    ) -> Session:
        """Creates and returns a new blocking session record."""
        now = start_time or datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sessions (start_time, duration_seconds, type, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (now, duration_seconds, session_type, status, now),
            )
            conn.commit()
            new_id = cursor.lastrowid
            logger.info("Created session #%d (duration=%ds, status=%s)", new_id, duration_seconds, status)
            return Session(
                id=new_id,
                start_time=now,
                end_time=None,
                duration_seconds=duration_seconds,
                type=session_type,
                status=status,
                created_at=now,
            )

    def get_active_session(self) -> Optional[Session]:
        """Returns the currently active session if one exists."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, start_time, end_time, duration_seconds, type, status, created_at
                FROM sessions
                WHERE status = 'active'
                ORDER BY id DESC LIMIT 1
                """
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Session(
                id=row["id"],
                start_time=row["start_time"],
                end_time=row["end_time"],
                duration_seconds=row["duration_seconds"],
                type=row["type"],
                status=row["status"],
                created_at=row["created_at"],
            )

    def end_session(self, session_id: int, status: str = "completed", end_time: Optional[str] = None) -> bool:
        """Marks an active session as completed/stopped/interrupted."""
        now = end_time or datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE sessions
                SET status = ?, end_time = ?
                WHERE id = ?
                """,
                (status, now, session_id),
            )
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info("Ended session #%d with status '%s'", session_id, status)
            return success

    def get_sessions(self, limit: int = 50) -> List[Session]:
        """Returns recent sessions ordered by id descending."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, start_time, end_time, duration_seconds, type, status, created_at
                FROM sessions
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            return [
                Session(
                    id=row["id"],
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    duration_seconds=row["duration_seconds"],
                    type=row["type"],
                    status=row["status"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    def clear_sessions(self) -> None:
        """Clears all session history."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions")
            conn.commit()
            logger.info("Cleared all session history.")

    def get_today_stats(self) -> Tuple[int, int]:
        """
        Returns (total_focus_seconds_today, completed_sessions_today).
        """
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT duration_seconds, status
                FROM sessions
                WHERE start_time >= ? AND status IN ('completed', 'stopped')
                """,
                (today_start,),
            )
            rows = cursor.fetchall()
            total_sec = sum(row["duration_seconds"] for row in rows)
            count = len(rows)
            return total_sec, count

    def get_week_stats(self) -> Tuple[int, int]:
        """
        Returns (total_focus_seconds_this_week, completed_sessions_this_week).
        """
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT duration_seconds, status
                FROM sessions
                WHERE start_time >= ? AND status IN ('completed', 'stopped')
                """,
                (week_start,),
            )
            rows = cursor.fetchall()
            total_sec = sum(row["duration_seconds"] for row in rows)
            count = len(rows)
            return total_sec, count

    # -------------------------------------------------------------
    # Settings Operations
    # -------------------------------------------------------------

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieves a setting value by key."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return str(row["value"])
            return default

    def set_setting(self, key: str, value: str) -> None:
        """Sets or updates a setting value."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (key, str(value)),
            )
            conn.commit()
