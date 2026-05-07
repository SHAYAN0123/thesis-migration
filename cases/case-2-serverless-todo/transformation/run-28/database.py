import sqlite3

from config import DB_PATH


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
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


def _row_to_dict(row):
    d = dict(row)
    d['checked'] = bool(d['checked'])
    return d


def create_todo(item):
    with _connect() as conn:
        conn.execute(
            'INSERT INTO todos (id, text, checked, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)',
            (item['id'], item['text'], int(item['checked']), item['createdAt'], item['updatedAt']),
        )
        conn.commit()


def list_todos():
    with _connect() as conn:
        rows = conn.execute('SELECT * FROM todos').fetchall()
    return [_row_to_dict(r) for r in rows]


def get_todo(todo_id):
    with _connect() as conn:
        row = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()
    if row is None:
        return None
    return _row_to_dict(row)


def update_todo(todo_id, text, checked, updated_at):
    with _connect() as conn:
        conn.execute(
            'UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?',
            (text, int(checked), updated_at, todo_id),
        )
        conn.commit()
        row = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()
    if row is None:
        return None
    return _row_to_dict(row)


def delete_todo(todo_id):
    with _connect() as conn:
        conn.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        conn.commit()
