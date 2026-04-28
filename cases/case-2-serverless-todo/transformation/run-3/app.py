import logging
import os
import sqlite3
import time
import uuid

from flask import Flask, jsonify, request

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "todos.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS todos (
            id        TEXT PRIMARY KEY,
            text      TEXT NOT NULL,
            checked   INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


_init_db()


def _row_to_dict(row):
    d = dict(row)
    d["checked"] = bool(d["checked"])
    return d


@app.route("/todos", methods=["POST"])
def create():
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        logging.error("Validation Failed")
        return jsonify({"error": "Couldn't create the todo item."}), 400

    timestamp = str(time.time())
    item = {
        "id": str(uuid.uuid4()),
        "text": data["text"],
        "checked": False,
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO todos (id, text, checked, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)",
            (item["id"], item["text"], 0, item["createdAt"], item["updatedAt"]),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify(item), 200


@app.route("/todos", methods=["GET"])
def list_todos():
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM todos").fetchall()
    finally:
        conn.close()

    return jsonify([_row_to_dict(r) for r in rows]), 200


@app.route("/todos/<todo_id>", methods=["GET"])
def get_todo(todo_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    finally:
        conn.close()

    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify(_row_to_dict(row)), 200


@app.route("/todos/<todo_id>", methods=["PUT"])
def update_todo(todo_id):
    data = request.get_json(silent=True)
    if not data or "text" not in data or "checked" not in data:
        logging.error("Validation Failed")
        return jsonify({"error": "Couldn't update the todo item."}), 400

    timestamp = str(time.time())

    conn = get_db()
    try:
        conn.execute(
            "UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?",
            (data["text"], 1 if data["checked"] else 0, timestamp, todo_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    finally:
        conn.close()

    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify(_row_to_dict(row)), 200


@app.route("/todos/<todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
    finally:
        conn.close()

    return jsonify({}), 200


if __name__ == "__main__":
    app.run(debug=True)
