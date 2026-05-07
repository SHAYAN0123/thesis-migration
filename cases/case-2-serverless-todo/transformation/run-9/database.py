import sqlite3
import os

DB_PATH = os.environ.get('DB_PATH', 'todos.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                checked INTEGER NOT NULL DEFAULT 0,
                createdAt TEXT NOT NULL,
                updatedAt TEXT NOT NULL
            )
        ''')
        conn.commit()


def row_to_dict(row):
    d = dict(row)
    d['checked'] = bool(d['checked'])
    return d
