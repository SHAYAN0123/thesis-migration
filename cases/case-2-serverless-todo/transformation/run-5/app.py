from flask import Flask, jsonify, request

import database

app = Flask(__name__)


@app.route("/todos", methods=["POST"])
def create():
    data = request.get_json(silent=True) or {}
    if "text" not in data:
        return jsonify({"error": "text is required"}), 400
    return jsonify(database.create_todo(data["text"])), 200


@app.route("/todos", methods=["GET"])
def list_all():
    return jsonify(database.list_todos()), 200


@app.route("/todos/<todo_id>", methods=["GET"])
def get_one(todo_id):
    todo = database.get_todo(todo_id)
    if todo is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(todo), 200


@app.route("/todos/<todo_id>", methods=["PUT"])
def update(todo_id):
    data = request.get_json(silent=True) or {}
    if "text" not in data or "checked" not in data:
        return jsonify({"error": "text and checked are required"}), 400
    todo = database.update_todo(todo_id, data["text"], data["checked"])
    if todo is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(todo), 200


@app.route("/todos/<todo_id>", methods=["DELETE"])
def delete(todo_id):
    database.delete_todo(todo_id)
    return jsonify({}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
