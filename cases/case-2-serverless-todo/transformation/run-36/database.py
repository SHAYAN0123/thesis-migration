import sqlite3

from config import DB_PATH


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id        TEXT PRIMARY KEY,
                text      TEXT NOT NULL,
                checked   INTEGER NOT NULL DEFAULT 0,
                createdAt TEXT NOT NULL,
                updatedAt TEXT NOT NULL
            )
        ''')
        conn.commit()
    finally:
        conn.close()


def _row_to_dict(row):
    d = dict(row)
    d['checked'] = bool(d['checked'])
    return d


def create_todo(item):
    conn = _get_connection()
    try:
        conn.execute(
            'INSERT INTO todos (id, text, checked, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)',
            (item['id'], item['text'], int(item['checked']), item['createdAt'], item['updatedAt']),
        )
        conn.commit()
    finally:
        conn.close()


def list_todos():
    conn = _get_connection()
    try:
        rows = conn.execute('SELECT * FROM todos').fetchall()
    finally:
        conn.close()
    return [_row_to_dict(r) for r in rows]


def get_todo(todo_id):
    conn = _get_connection()
    try:
        row = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


def update_todo(todo_id, text, checked, updated_at):
    conn = _get_connection()
    try:
        conn.execute(
            'UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?',
            (text, int(checked), updated_at, todo_id),
        )
        conn.commit()
        row = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


def delete_todo(todo_id):
    conn = _get_connection()
    try:
        conn.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        conn.commit()
    finally:
        conn.close()
