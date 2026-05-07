import sqlite3
import os

DATABASE_PATH = os.environ.get("DATABASE_PATH", "todos.db")


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
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
    conn.close()


def row_to_dict(row):
    d = dict(row)
    d["checked"] = bool(d["checked"])
    return d
