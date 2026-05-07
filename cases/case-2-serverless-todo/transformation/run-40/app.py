from flask import Flask, jsonify, request

import database

app = Flask(__name__)


@app.route("/todos", methods=["POST"])
def create():
    data = request.get_json(silent=True) or {}
    if "text" not in data:
        return jsonify({"error": "Validation Failed"}), 400
    item = database.create_todo(data["text"])
    return jsonify(item), 200


@app.route("/todos", methods=["GET"])
def list_todos():
    items = database.list_todos()
    return jsonify(items), 200


@app.route("/todos/<todo_id>", methods=["GET"])
def get(todo_id):
    item = database.get_todo(todo_id)
    if item is None:
        return jsonify({"error": "Not Found"}), 404
    return jsonify(item), 200


@app.route("/todos/<todo_id>", methods=["PUT"])
def update(todo_id):
    data = request.get_json(silent=True) or {}
    if "text" not in data or "checked" not in data:
        return jsonify({"error": "Validation Failed"}), 400
    item = database.update_todo(todo_id, data["text"], data["checked"])
    if item is None:
        return jsonify({"error": "Not Found"}), 404
    return jsonify(item), 200


@app.route("/todos/<todo_id>", methods=["DELETE"])
def delete(todo_id):
    database.delete_todo(todo_id)
    return jsonify({}), 200


if __name__ == "__main__":
    app.run()
