import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "todos.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
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


def create_todo(todo_id, text, checked, created_at, updated_at):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO todos (id, text, checked, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)",
            (todo_id, text, 1 if checked else 0, created_at, updated_at),
        )
        conn.commit()


def get_todo(todo_id):
    with _connect() as conn:
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        return dict(row) if row else None


def list_todos():
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM todos").fetchall()
        return [dict(row) for row in rows]


def update_todo(todo_id, text, checked, updated_at):
    with _connect() as conn:
        conn.execute(
            "UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?",
            (text, 1 if checked else 0, updated_at, todo_id),
        )
        conn.commit()


def delete_todo(todo_id):
    with _connect() as conn:
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
