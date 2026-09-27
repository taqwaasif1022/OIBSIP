"""
Oasis Infobyte - Python Programming Internship
Task 2: Advanced BMI Calculator

Database layer for SQLite persistence.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


# Store the database inside the Task 2 project folder.
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "bmi_data.db"


class DatabaseError(Exception):
    """Custom exception for BMI database errors."""


class BMIDatabase:
    """Handles users and BMI records using SQLite."""

    def __init__(self, database_path: Path = DATABASE_PATH):
        self.database_path = Path(database_path)
        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        """Create a SQLite connection with useful settings."""
        try:
            connection = sqlite3.connect(self.database_path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            return connection
        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Unable to connect to the database: {exc}"
            ) from exc

    def _initialize_database(self) -> None:
        """Create required tables if they do not already exist."""
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                        created_at TEXT NOT NULL
                    )
                    """
                )

                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS bmi_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        weight REAL NOT NULL,
                        height REAL NOT NULL,
                        bmi REAL NOT NULL,
                        category TEXT NOT NULL,
                        recorded_at TEXT NOT NULL,
                        FOREIGN KEY (user_id)
                            REFERENCES users(id)
                            ON DELETE CASCADE
                    )
                    """
                )

                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_bmi_records_user_date
                    ON bmi_records(user_id, recorded_at)
                    """
                )

                connection.commit()

        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Unable to initialize the database: {exc}"
            ) from exc

    def get_or_create_user(self, name: str) -> int:
        """
        Return an existing user's ID or create a new user.

        User names are treated case-insensitively.
        """
        clean_name = name.strip()

        if not clean_name:
            raise DatabaseError("User name cannot be empty.")

        try:
            with self._connect() as connection:
                existing_user = connection.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE name = ?
                    """,
                    (clean_name,),
                ).fetchone()

                if existing_user:
                    return int(existing_user["id"])

                cursor = connection.execute(
                    """
                    INSERT INTO users (name, created_at)
                    VALUES (?, ?)
                    """,
                    (
                        clean_name,
                        datetime.now().isoformat(timespec="seconds"),
                    ),
                )

                connection.commit()

                return int(cursor.lastrowid)

        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Unable to create or retrieve user: {exc}"
            ) from exc

    def get_users(self) -> list[str]:
        """Return all saved user names alphabetically."""
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT name
                    FROM users
                    ORDER BY name COLLATE NOCASE
                    """
                ).fetchall()

                return [str(row["name"]) for row in rows]

        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Unable to read users: {exc}"
            ) from exc

    def save_bmi_record(
        self,
        user_name: str,
        weight: float,
        height: float,
        bmi: float,
        category: str,
    ) -> None:
        """Save a BMI measurement for a user."""
        try:
            user_id = self.get_or_create_user(user_name)

            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO bmi_records (
                        user_id,
                        weight,
                        height,
                        bmi,
                        category,
                        recorded_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        weight,
                        height,
                        bmi,
                        category,
                        datetime.now().isoformat(timespec="seconds"),
                    ),
                )

                connection.commit()

        except DatabaseError:
            raise
        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Unable to save BMI record: {exc}"
            ) from exc

    def get_user_history(
        self,
        user_name: str,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """Return BMI history for a specific user."""
        try:
            with self._connect() as connection:
                query = """
                    SELECT
                        r.id,
                        u.name,
                        r.weight,
                        r.height,
                        r.bmi,
                        r.category,
                        r.recorded_at
                    FROM bmi_records AS r
                    INNER JOIN users AS u
                        ON r.user_id = u.id
                    WHERE u.name = ?
                    ORDER BY r.recorded_at DESC
                """

                parameters: list = [user_name.strip()]

                if limit is not None:
                    if limit <= 0:
                        return []

                    query += " LIMIT ?"
                    parameters.append(limit)

                rows = connection.execute(
                    query,
                    parameters,
                ).fetchall()

                return [dict(row) for row in rows]

        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Unable to read BMI history: {exc}"
            ) from exc

    def get_user_trend(self, user_name: str) -> list[dict]:
        """Return chronological BMI data for trend visualization."""
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT
                        r.bmi,
                        r.recorded_at
                    FROM bmi_records AS r
                    INNER JOIN users AS u
                        ON r.user_id = u.id
                    WHERE u.name = ?
                    ORDER BY r.recorded_at ASC
                    """,
                    (user_name.strip(),),
                ).fetchall()

                return [dict(row) for row in rows]

        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Unable to read BMI trend data: {exc}"
            ) from exc

    def delete_all_data(self) -> None:
        """
        Delete all users and BMI records.

        This method is included for development/testing purposes.
        The GUI will not expose it as a normal user feature.
        """
        try:
            with self._connect() as connection:
                connection.execute("DELETE FROM bmi_records")
                connection.execute("DELETE FROM users")
                connection.commit()

        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Unable to clear database: {exc}"
            ) from exc