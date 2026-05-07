import sqlite3
import os

DB_PATH = os.environ.get("DATABASE_PATH", "todos.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                checked INTEGER NOT NULL DEFAULT 0,
                createdAt TEXT NOT NULL,
                updatedAt TEXT NOT NULL
            )
        """)
        conn.commit()


def row_to_dict(row):
    d = dict(row)
    d["checked"] = bool(d["checked"])
    return d


def create_todo(item):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO todos (id, text, checked, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)",
            (item["id"], item["text"], int(item["checked"]), item["createdAt"], item["updatedAt"]),
        )
        conn.commit()


def list_todos():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM todos").fetchall()
    return [row_to_dict(r) for r in rows]


def get_todo(todo_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    return row_to_dict(row) if row else None


def update_todo(todo_id, text, checked, updated_at):
    with get_connection() as conn:
        conn.execute(
            "UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?",
            (text, int(checked), updated_at, todo_id),
        )
        conn.commit()
    return get_todo(todo_id)


def delete_todo(todo_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
