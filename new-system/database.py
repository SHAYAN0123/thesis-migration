import sqlite3

from config import DB_PATH

_ALLOWED = {"title", "description", "status"}


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init():
    with _connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                status      TEXT NOT NULL DEFAULT 'pending'
            )"""
        )


_init()


def create_task(task):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO tasks (id, title, description, status) VALUES (?, ?, ?, ?)",
            (task["id"], task["title"], task.get("description", ""), task.get("status", "pending")),
        )
    return task


def get_all_tasks():
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM tasks").fetchall()
    return [dict(r) for r in rows]


def get_task(task_id):
    with _connect() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


def update_task(task_id, updates):
    safe = {k: v for k, v in updates.items() if k in _ALLOWED}
    if safe:
        set_clause = ", ".join(f"{k} = ?" for k in safe)
        with _connect() as conn:
            conn.execute(
                f"UPDATE tasks SET {set_clause} WHERE id = ?",
                list(safe.values()) + [task_id],
            )
    return get_task(task_id)


def delete_task(task_id):
    with _connect() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
