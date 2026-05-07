import sqlite3
import uuid
from datetime import datetime, timezone

from config import DB_PATH


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init():
    with _connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS todos (
                id        TEXT PRIMARY KEY,
                text      TEXT NOT NULL,
                checked   INTEGER NOT NULL DEFAULT 0,
                createdAt TEXT NOT NULL,
                updatedAt TEXT NOT NULL
            )"""
        )


_init()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row):
    return {
        "id": row["id"],
        "text": row["text"],
        "checked": bool(row["checked"]),
        "createdAt": row["createdAt"],
        "updatedAt": row["updatedAt"],
    }


def create_todo(text):
    now = _now()
    item = {
        "id": str(uuid.uuid4()),
        "text": text,
        "checked": False,
        "createdAt": now,
        "updatedAt": now,
    }
    with _connect() as conn:
        conn.execute(
            "INSERT INTO todos (id, text, checked, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)",
            (item["id"], item["text"], 0, item["createdAt"], item["updatedAt"]),
        )
    return item


def list_todos():
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM todos").fetchall()
    return [_row_to_dict(r) for r in rows]


def get_todo(todo_id):
    with _connect() as conn:
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    return _row_to_dict(row) if row else None


def update_todo(todo_id, text, checked):
    now = _now()
    with _connect() as conn:
        conn.execute(
            "UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?",
            (text, int(checked), now, todo_id),
        )
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    return _row_to_dict(row) if row else None


def delete_todo(todo_id):
    with _connect() as conn:
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
