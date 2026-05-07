import sqlite3
import time
import uuid

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


def _to_dict(row):
    return {
        "id": row["id"],
        "text": row["text"],
        "checked": bool(row["checked"]),
        "createdAt": row["createdAt"],
        "updatedAt": row["updatedAt"],
    }


def create_todo(text):
    now = str(time.time())
    item = {
        "id": str(uuid.uuid1()),
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
    return [_to_dict(r) for r in rows]


def get_todo(todo_id):
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM todos WHERE id = ?", (todo_id,)
        ).fetchone()
    return _to_dict(row) if row else None


def update_todo(todo_id, text, checked):
    now = str(time.time() * 1000)
    with _connect() as conn:
        conn.execute(
            "UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?",
            (text, 1 if checked else 0, now, todo_id),
        )
        row = conn.execute(
            "SELECT * FROM todos WHERE id = ?", (todo_id,)
        ).fetchone()
    return _to_dict(row) if row else None


def delete_todo(todo_id):
    with _connect() as conn:
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
