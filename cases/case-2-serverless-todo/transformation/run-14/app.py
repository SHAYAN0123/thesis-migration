import logging
import time
import uuid

from flask import Flask, jsonify, request

import database

app = Flask(__name__)
database.init_db()


@app.route("/todos", methods=["POST"])
def create():
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        logging.error("Validation Failed")
        return jsonify({"error": "Couldn't create the todo item."}), 400

    timestamp = str(time.time())
    item = {
        "id": str(uuid.uuid1()),
        "text": data["text"],
        "checked": False,
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }

    database.create_todo(item)
    return jsonify(item), 200


@app.route("/todos", methods=["GET"])
def list_todos():
    items = database.list_todos()
    return jsonify(items), 200


@app.route("/todos/<todo_id>", methods=["GET"])
def get_todo(todo_id):
    item = database.get_todo(todo_id)
    if item is None:
        return jsonify({"error": "Todo not found"}), 404
    return jsonify(item), 200


@app.route("/todos/<todo_id>", methods=["PUT"])
def update_todo(todo_id):
    data = request.get_json(silent=True)
    if not data or "text" not in data or "checked" not in data:
        logging.error("Validation Failed")
        return jsonify({"error": "Couldn't update the todo item."}), 400

    timestamp = str(time.time())
    updated = database.update_todo(todo_id, data["text"], data["checked"], timestamp)
    if updated is None:
        return jsonify({"error": "Todo not found"}), 404
    return jsonify(updated), 200


@app.route("/todos/<todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    database.delete_todo(todo_id)
    return ("", 200)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
