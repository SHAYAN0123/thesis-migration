import time
import uuid

from flask import Flask, jsonify, request

import database

app = Flask(__name__)
database.init_db()


def _to_json(row):
    row["checked"] = bool(row["checked"])
    return row


@app.route("/todos", methods=["POST"])
def create():
    data = request.get_json(silent=True) or {}
    if "text" not in data:
        return jsonify({"error": "Couldn't create the todo item."}), 400

    timestamp = str(time.time())
    todo = {
        "id": str(uuid.uuid1()),
        "text": data["text"],
        "checked": False,
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }
    database.create_todo(
        todo["id"], todo["text"], todo["checked"], todo["createdAt"], todo["updatedAt"]
    )
    return jsonify(todo), 200


@app.route("/todos", methods=["GET"])
def list_todos():
    todos = [_to_json(t) for t in database.list_todos()]
    return jsonify(todos), 200


@app.route("/todos/<todo_id>", methods=["GET"])
def get_todo(todo_id):
    todo = database.get_todo(todo_id)
    if todo is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(_to_json(todo)), 200


@app.route("/todos/<todo_id>", methods=["PUT"])
def update_todo(todo_id):
    data = request.get_json(silent=True) or {}
    if "text" not in data or "checked" not in data:
        return jsonify({"error": "Couldn't update the todo item."}), 400

    updated_at = str(time.time())
    database.update_todo(todo_id, data["text"], data["checked"], updated_at)
    todo = database.get_todo(todo_id)
    return jsonify(_to_json(todo)), 200


@app.route("/todos/<todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    database.delete_todo(todo_id)
    return jsonify({}), 200


if __name__ == "__main__":
    app.run()
