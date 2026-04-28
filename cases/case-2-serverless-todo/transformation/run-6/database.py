import sqlite3
import uuid
from datetime import datetime, timezone

from config import DB_PATH


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _ensure_table():
    with _get_conn() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS todos (
                id        TEXT PRIMARY KEY,
                text      TEXT NOT NULL,
                checked   INTEGER NOT NULL DEFAULT 0,
                createdAt TEXT NOT NULL,
                updatedAt TEXT NOT NULL
            )"""
        )
        conn.commit()


_ensure_table()


def _timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


def _row_to_dict(row):
    return {
        "id": row["id"],
        "text": row["text"],
        "checked": bool(row["checked"]),
        "createdAt": row["createdAt"],
        "updatedAt": row["updatedAt"],
    }


def create_todo(text):
    todo_id = str(uuid.uuid4())
    now = _timestamp()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO todos (id, text, checked, createdAt, updatedAt) VALUES (?, ?, 0, ?, ?)",
            (todo_id, text, now, now),
        )
        conn.commit()
    return {
        "id": todo_id,
        "text": text,
        "checked": False,
        "createdAt": now,
        "updatedAt": now,
    }


def list_todos():
    with _get_conn() as conn:
        rows = conn.execute("SELECT id, text, checked, createdAt, updatedAt FROM todos").fetchall()
    return [_row_to_dict(r) for r in rows]


def get_todo(todo_id):
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT id, text, checked, createdAt, updatedAt FROM todos WHERE id = ?",
            (todo_id,),
        ).fetchone()
    return _row_to_dict(row) if row else None


def update_todo(todo_id, text, checked):
    now = _timestamp()
    with _get_conn() as conn:
        conn.execute(
            "UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?",
            (text, 1 if checked else 0, now, todo_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, text, checked, createdAt, updatedAt FROM todos WHERE id = ?",
            (todo_id,),
        ).fetchone()
    return _row_to_dict(row) if row else None


def delete_todo(todo_id):
    with _get_conn() as conn:
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
