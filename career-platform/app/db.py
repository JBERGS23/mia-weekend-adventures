"""SQLite access.

Deliberately thin: a connection helper, a schema initialiser, and small query
helpers. Every module talks to the database through plain SQL rather than an
ORM, which keeps the code readable and the eventual Postgres port mechanical.

Threading note: scans run in a background thread, so connections are created
per-use rather than shared. SQLite is fine with that as long as we don't pass
a connection between threads, which we never do.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

import config

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def utcnow() -> str:
    """ISO-8601 UTC timestamp. One format everywhere, no local-time surprises."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def today() -> str:
    """Today's date as YYYY-MM-DD, used to key the daily quiz."""
    return datetime.now().strftime("%Y-%m-%d")


def connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open a connection with the settings the rest of the app assumes."""
    path = Path(db_path or config.DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL lets the background scan write while the browser reads.
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def session(db_path: Optional[Path] = None) -> Iterator[sqlite3.Connection]:
    """Transactional connection: commits on success, rolls back on error."""
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[Path] = None) -> None:
    """Create any missing tables. Safe to run on every start."""
    with session(db_path) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def query(conn: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    return conn.execute(sql, tuple(params)).fetchall()


def query_one(conn: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> Optional[sqlite3.Row]:
    return conn.execute(sql, tuple(params)).fetchone()


def scalar(conn: sqlite3.Connection, sql: str, params: Iterable[Any] = (), default: Any = None) -> Any:
    row = conn.execute(sql, tuple(params)).fetchone()
    if row is None or row[0] is None:
        return default
    return row[0]


def execute(conn: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
    return conn.execute(sql, tuple(params))


def insert(conn: sqlite3.Connection, table: str, values: dict[str, Any]) -> int:
    """Insert a row from a dict and return its new id."""
    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    cur = conn.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
        tuple(values.values()),
    )
    return int(cur.lastrowid)


def update(conn: sqlite3.Connection, table: str, row_id: Any, values: dict[str, Any],
           key: str = "id") -> None:
    if not values:
        return
    assignments = ", ".join(f"{column} = ?" for column in values)
    conn.execute(
        f"UPDATE {table} SET {assignments} WHERE {key} = ?",
        (*values.values(), row_id),
    )


# ---------------------------------------------------------------------------
# app_state: small key/value store for "when did we last do X"
# ---------------------------------------------------------------------------

def get_state(conn: sqlite3.Connection, key: str, default: Optional[str] = None) -> Optional[str]:
    row = query_one(conn, "SELECT value FROM app_state WHERE key = ?", (key,))
    return row["value"] if row else default


def set_state(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO app_state (key, value, updated_at) VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value,
                                       updated_at = excluded.updated_at
        """,
        (key, value, utcnow()),
    )
