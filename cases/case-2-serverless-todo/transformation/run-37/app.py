from flask import Flask, jsonify, request, abort

import database

app = Flask(__name__)
database.init_db()


@app.route('/todos', methods=['POST'])
def create():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': "Couldn't create the todo item."}), 400
    todo = database.create_todo(data['text'])
    return jsonify(todo), 200


@app.route('/todos', methods=['GET'])
def list_todos():
    return jsonify(database.list_todos()), 200


@app.route('/todos/<todo_id>', methods=['GET'])
def get_todo(todo_id):
    todo = database.get_todo(todo_id)
    if todo is None:
        abort(404)
    return jsonify(todo), 200


@app.route('/todos/<todo_id>', methods=['PUT'])
def update_todo(todo_id):
    data = request.get_json()
    if not data or 'text' not in data or 'checked' not in data:
        return jsonify({'error': "Couldn't update the todo item."}), 400
    todo = database.update_todo(todo_id, data['text'], data['checked'])
    return jsonify(todo), 200


@app.route('/todos/<todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    database.delete_todo(todo_id)
    return '', 200


if __name__ == '__main__':
    app.run()
