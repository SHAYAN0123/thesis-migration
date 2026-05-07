import sqlite3
import time
import uuid
import os
from flask import Flask, g, jsonify, request

app = Flask(__name__)

DATABASE = os.environ.get('DATABASE', 'todos.db')


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            checked INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL
        )
    ''')
    db.commit()
    db.close()


def row_to_dict(row):
    d = dict(row)
    d['checked'] = bool(d['checked'])
    return d


@app.post('/todos')
def create():
    data = request.get_json(silent=True) or {}
    if 'text' not in data:
        return jsonify({'error': "Couldn't create the todo item."}), 400

    timestamp = str(time.time())
    item = {
        'id': str(uuid.uuid1()),
        'text': data['text'],
        'checked': False,
        'createdAt': timestamp,
        'updatedAt': timestamp,
    }

    db = get_db()
    db.execute(
        'INSERT INTO todos (id, text, checked, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)',
        (item['id'], item['text'], int(item['checked']), item['createdAt'], item['updatedAt'])
    )
    db.commit()

    return jsonify(item), 200


@app.get('/todos')
def list_todos():
    db = get_db()
    rows = db.execute('SELECT * FROM todos').fetchall()
    return jsonify([row_to_dict(r) for r in rows]), 200


@app.get('/todos/<todo_id>')
def get_todo(todo_id):
    db = get_db()
    row = db.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()
    if row is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(row_to_dict(row)), 200


@app.put('/todos/<todo_id>')
def update_todo(todo_id):
    data = request.get_json(silent=True) or {}
    if 'text' not in data or 'checked' not in data:
        return jsonify({'error': "Couldn't update the todo item."}), 400

    timestamp = str(time.time())

    db = get_db()
    db.execute(
        'UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?',
        (data['text'], int(data['checked']), timestamp, todo_id)
    )
    db.commit()

    row = db.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()
    if row is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(row_to_dict(row)), 200


@app.delete('/todos/<todo_id>')
def delete_todo(todo_id):
    db = get_db()
    db.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
    db.commit()
    return '', 200


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
