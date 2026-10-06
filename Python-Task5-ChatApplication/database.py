"""database.py - all SQLite access for the chat application.

Every query is parameterized (values are passed separately from the SQL text),
so user input can never change the meaning of a query (no SQL injection).
The database file and tables are created automatically on first use.
"""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat.db")
DEFAULT_ROOMS = ["General", "Python", "AI Projects", "Random"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rooms (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    room_name  TEXT NOT NULL UNIQUE COLLATE NOCASE,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id   INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    user_id   INTEGER NOT NULL REFERENCES users(id),
    message   TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_room ON messages(room_id, id);
"""


class DatabaseError(Exception):
    """Any SQLite failure, wrapped so callers don't need to import sqlite3."""


class DuplicateError(DatabaseError):
    """A UNIQUE constraint was violated (duplicate username / room name)."""


def now_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Database:
    def __init__(self, path=DEFAULT_DB_PATH):
        self.path = path
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self):
        """Open a short-lived connection (safe to use from many threads)."""
        conn = None
        try:
            conn = sqlite3.connect(self.path, timeout=10)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")  # enforce relationships
            yield conn
            conn.commit()
        except sqlite3.Error as exc:
            if conn is not None:
                conn.rollback()
            raise DatabaseError(str(exc)) from exc
        finally:
            if conn is not None:
                conn.close()

    @staticmethod
    def _is_unique_violation(exc):
        cause = exc.__cause__
        return isinstance(cause, sqlite3.IntegrityError) and "UNIQUE" in str(cause)

    # ---- users -----------------------------------------------------------
    def create_user(self, username, password_hash):
        try:
            with self._connect() as conn:
                cur = conn.execute(
                    "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                    (username, password_hash, now_string()))
                return cur.lastrowid
        except DatabaseError as exc:
            if self._is_unique_violation(exc):
                raise DuplicateError("username already exists") from exc
            raise

    def get_user(self, username):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
                (username,)).fetchone()
        return dict(row) if row else None

    # ---- rooms -----------------------------------------------------------
    def ensure_default_rooms(self):
        with self._connect() as conn:
            for name in DEFAULT_ROOMS:
                conn.execute("INSERT OR IGNORE INTO rooms (room_name, created_at) VALUES (?, ?)",
                             (name, now_string()))

    def create_room(self, room_name):
        try:
            with self._connect() as conn:
                cur = conn.execute("INSERT INTO rooms (room_name, created_at) VALUES (?, ?)",
                                   (room_name, now_string()))
                return cur.lastrowid
        except DatabaseError as exc:
            if self._is_unique_violation(exc):
                raise DuplicateError("room already exists") from exc
            raise

    def get_room(self, room_name):
        with self._connect() as conn:
            row = conn.execute("SELECT id, room_name FROM rooms WHERE room_name = ?",
                               (room_name,)).fetchone()
        return dict(row) if row else None

    def list_rooms(self):
        with self._connect() as conn:
            rows = conn.execute("SELECT id, room_name FROM rooms ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    # ---- messages --------------------------------------------------------
    def add_message(self, room_id, user_id, message, timestamp=None):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO messages (room_id, user_id, message, timestamp) VALUES (?, ?, ?, ?)",
                (room_id, user_id, message, timestamp or now_string()))

    def get_history(self, room_id, limit=100):
        """Return the newest `limit` messages of a room, oldest first."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT u.username AS user, m.message AS text, m.timestamp AS timestamp
                   FROM messages m JOIN users u ON u.id = m.user_id
                   WHERE m.room_id = ? ORDER BY m.id DESC LIMIT ?""",
                (room_id, limit)).fetchall()
        return [dict(r) for r in reversed(rows)]
