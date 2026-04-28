import os
import sqlite3
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)

_DB_PATH = os.environ.get("DB_PATH", "todos.db")


def _get_conn():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db(conn):
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


def _row_to_dict(row):
    d = dict(row)
    d["checked"] = bool(d["checked"])
    return d


def _now():
    return datetime.now(timezone.utc).isoformat()


@app.route("/todos", methods=["POST"])
def create_todo():
    data = request.get_json(silent=True) or {}
    if "text" not in data:
        return jsonify({"error": "Couldn't create the todo item."}), 400

    todo = {
        "id": str(uuid.uuid4()),
        "text": data["text"],
        "checked": False,
        "createdAt": _now(),
        "updatedAt": _now(),
    }

    with _get_conn() as conn:
        _init_db(conn)
        conn.execute(
            "INSERT INTO todos (id, text, checked, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)",
            (todo["id"], todo["text"], int(todo["checked"]), todo["createdAt"], todo["updatedAt"]),
        )

    return jsonify(todo), 200


@app.route("/todos", methods=["GET"])
def list_todos():
    with _get_conn() as conn:
        _init_db(conn)
        rows = conn.execute("SELECT * FROM todos").fetchall()
    return jsonify([_row_to_dict(r) for r in rows]), 200


@app.route("/todos/<todo_id>", methods=["GET"])
def get_todo(todo_id):
    with _get_conn() as conn:
        _init_db(conn)
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()

    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify(_row_to_dict(row)), 200


@app.route("/todos/<todo_id>", methods=["PUT"])
def update_todo(todo_id):
    data = request.get_json(silent=True) or {}
    if "text" not in data or "checked" not in data:
        return jsonify({"error": "Couldn't update the todo item."}), 400

    updated_at = _now()

    with _get_conn() as conn:
        _init_db(conn)
        conn.execute(
            "UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?",
            (data["text"], int(data["checked"]), updated_at, todo_id),
        )
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()

    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify(_row_to_dict(row)), 200


@app.route("/todos/<todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    with _get_conn() as conn:
        _init_db(conn)
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))

    return "", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
