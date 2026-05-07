import json
import time
import uuid

from flask import Flask, request, jsonify

from database import init_db, get_connection, row_to_dict

app = Flask(__name__)


@app.before_request
def setup():
    init_db()


@app.route('/todos', methods=['POST'])
def create_todo():
    data = request.get_json(force=True)
    if not data or 'text' not in data:
        return jsonify({'error': "Couldn't create the todo item."}), 400

    timestamp = str(time.time())
    item = {
        'id': str(uuid.uuid1()),
        'text': data['text'],
        'checked': False,
        'createdAt': timestamp,
        'updatedAt': timestamp,
    }

    with get_connection() as conn:
        conn.execute(
            'INSERT INTO todos (id, text, checked, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)',
            (item['id'], item['text'], int(item['checked']), item['createdAt'], item['updatedAt'])
        )
        conn.commit()

    return jsonify(item), 200


@app.route('/todos', methods=['GET'])
def list_todos():
    with get_connection() as conn:
        rows = conn.execute('SELECT * FROM todos').fetchall()
    return jsonify([row_to_dict(r) for r in rows]), 200


@app.route('/todos/<string:todo_id>', methods=['GET'])
def get_todo(todo_id):
    with get_connection() as conn:
        row = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()

    if row is None:
        return jsonify({'error': 'Todo not found'}), 404

    return jsonify(row_to_dict(row)), 200


@app.route('/todos/<string:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    data = request.get_json(force=True)
    if not data or 'text' not in data or 'checked' not in data:
        return jsonify({'error': "Couldn't update the todo item."}), 400

    timestamp = str(int(time.time() * 1000))

    with get_connection() as conn:
        conn.execute(
            'UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?',
            (data['text'], int(data['checked']), timestamp, todo_id)
        )
        conn.commit()
        row = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()

    if row is None:
        return jsonify({'error': 'Todo not found'}), 404

    return jsonify(row_to_dict(row)), 200


@app.route('/todos/<string:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    with get_connection() as conn:
        conn.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        conn.commit()

    return jsonify({}), 200


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
