import json
import logging
import time
import uuid

from flask import Flask, jsonify, request

import database

app = Flask(__name__)
database.init_db()


@app.route('/todos', methods=['POST'])
def create_todo():
    data = request.get_json(silent=True) or {}
    if 'text' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't create the todo item.")

    timestamp = str(time.time())

    item = {
        'id': str(uuid.uuid1()),
        'text': data['text'],
        'checked': False,
        'createdAt': timestamp,
        'updatedAt': timestamp,
    }

    database.create_todo(item)

    return jsonify(item), 200


@app.route('/todos', methods=['GET'])
def list_todos():
    items = database.list_todos()
    return jsonify(items), 200


@app.route('/todos/<string:todo_id>', methods=['GET'])
def get_todo(todo_id):
    item = database.get_todo(todo_id)
    if item is None:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(item), 200


@app.route('/todos/<string:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    data = request.get_json(silent=True) or {}
    if 'text' not in data or 'checked' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't update the todo item.")

    timestamp = str(int(time.time() * 1000))

    updated = database.update_todo(todo_id, data['text'], data['checked'], timestamp)
    if updated is None:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(updated), 200


@app.route('/todos/<string:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    database.delete_todo(todo_id)
    return jsonify({}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(__import__('os').environ.get('PORT', 5000)))
