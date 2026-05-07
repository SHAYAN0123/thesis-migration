import os
import sqlite3
import time
import uuid

from flask import Flask, jsonify, request

app = Flask(__name__)


def get_db():
    db_path = os.environ.get("DB_PATH", "todos.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            checked INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL
        )
    """)
    return conn


def row_to_dict(row):
    d = dict(row)
    d["checked"] = bool(d["checked"])
    return d


@app.route("/todos", methods=["POST"])
def create():
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "Couldn't create the todo item."}), 400

    timestamp = str(int(time.time() * 1000))
    todo = {
        "id": str(uuid.uuid4()),
        "text": data["text"],
        "checked": False,
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }

    with get_db() as conn:
        conn.execute(
            "INSERT INTO todos (id, text, checked, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)",
            (todo["id"], todo["text"], 0, todo["createdAt"], todo["updatedAt"]),
        )

    return jsonify(todo), 200


@app.route("/todos", methods=["GET"])
def list_todos():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM todos").fetchall()
    return jsonify([row_to_dict(r) for r in rows]), 200


@app.route("/todos/<todo_id>", methods=["GET"])
def get_todo(todo_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(row_to_dict(row)), 200


@app.route("/todos/<todo_id>", methods=["PUT"])
def update_todo(todo_id):
    data = request.get_json(silent=True)
    if not data or "text" not in data or "checked" not in data:
        return jsonify({"error": "Couldn't update the todo item."}), 400

    timestamp = str(int(time.time() * 1000))

    with get_db() as conn:
        conn.execute(
            "UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?",
            (data["text"], 1 if data["checked"] else 0, timestamp, todo_id),
        )
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()

    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify(row_to_dict(row)), 200


@app.route("/todos/<todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    with get_db() as conn:
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    return jsonify({}), 200


if __name__ == "__main__":
    app.run(debug=True)
