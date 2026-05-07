import time
import uuid

from flask import Flask, jsonify, request

from database import delete_todo, get_todo, init_db, list_todos, create_todo, update_todo

app = Flask(__name__)


@app.before_request
def setup():
    init_db()


@app.post("/todos")
def create():
    data = request.get_json(force=True, silent=True) or {}
    if "text" not in data:
        return jsonify({"error": "Couldn't create the todo item."}), 400

    timestamp = str(time.time())
    item = {
        "id": str(uuid.uuid1()),
        "text": data["text"],
        "checked": False,
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }
    create_todo(item)
    return jsonify(item), 200


@app.get("/todos")
def list_all():
    return jsonify(list_todos()), 200


@app.get("/todos/<todo_id>")
def get(todo_id):
    item = get_todo(todo_id)
    if item is None:
        return jsonify({"error": "Todo not found."}), 404
    return jsonify(item), 200


@app.put("/todos/<todo_id>")
def update(todo_id):
    data = request.get_json(force=True, silent=True) or {}
    if "text" not in data or "checked" not in data:
        return jsonify({"error": "Couldn't update the todo item."}), 400

    timestamp = str(time.time())
    updated = update_todo(todo_id, data["text"], data["checked"], timestamp)
    if updated is None:
        return jsonify({"error": "Todo not found."}), 404
    return jsonify(updated), 200


@app.delete("/todos/<todo_id>")
def delete(todo_id):
    delete_todo(todo_id)
    return "", 200


if __name__ == "__main__":
    init_db()
    app.run(debug=False)
