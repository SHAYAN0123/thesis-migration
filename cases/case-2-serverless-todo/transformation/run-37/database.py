import sqlite3
import time
import uuid

import config


def _get_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS todos (
            id        TEXT PRIMARY KEY,
            text      TEXT NOT NULL,
            checked   INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def _row_to_dict(row):
    d = dict(row)
    d['checked'] = bool(d['checked'])
    return d


def create_todo(text):
    todo_id = str(uuid.uuid1())
    timestamp = str(time.time())
    conn = _get_connection()
    conn.execute(
        "INSERT INTO todos (id, text, checked, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)",
        (todo_id, text, 0, timestamp, timestamp),
    )
    conn.commit()
    conn.close()
    return get_todo(todo_id)


def list_todos():
    conn = _get_connection()
    rows = conn.execute("SELECT * FROM todos").fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_todo(todo_id):
    conn = _get_connection()
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


def update_todo(todo_id, text, checked):
    timestamp = str(time.time())
    conn = _get_connection()
    conn.execute(
        "UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?",
        (text, 1 if checked else 0, timestamp, todo_id),
    )
    conn.commit()
    conn.close()
    return get_todo(todo_id)


def delete_todo(todo_id):
    conn = _get_connection()
    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
