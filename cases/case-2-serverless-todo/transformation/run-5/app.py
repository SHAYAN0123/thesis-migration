import time
import uuid

from flask import Flask, jsonify, request, abort

from database import get_connection, init_db, row_to_dict

app = Flask(__name__)


@app.before_request
def setup():
    init_db()


@app.route("/todos", methods=["POST"])
def create_todo():
    data = request.get_json(silent=True) or {}
    if "text" not in data:
        abort(400, description="Couldn't create the todo item.")

    timestamp = str(time.time())
    item = {
        "id": str(uuid.uuid1()),
        "text": data["text"],
        "checked": False,
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }

    conn = get_connection()
    conn.execute(
        "INSERT INTO todos (id, text, checked, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)",
        (item["id"], item["text"], int(item["checked"]), item["createdAt"], item["updatedAt"]),
    )
    conn.commit()
    conn.close()

    return jsonify(item), 200


@app.route("/todos", methods=["GET"])
def list_todos():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM todos").fetchall()
    conn.close()
    return jsonify([row_to_dict(r) for r in rows]), 200


@app.route("/todos/<string:todo_id>", methods=["GET"])
def get_todo(todo_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    conn.close()
    if row is None:
        abort(404, description="Todo not found.")
    return jsonify(row_to_dict(row)), 200


@app.route("/todos/<string:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    data = request.get_json(silent=True) or {}
    if "text" not in data or "checked" not in data:
        abort(400, description="Couldn't update the todo item.")

    updated_at = str(time.time() * 1000)

    conn = get_connection()
    cursor = conn.execute(
        "UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?",
        (data["text"], int(data["checked"]), updated_at, todo_id),
    )
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        abort(404, description="Todo not found.")

    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row)), 200


@app.route("/todos/<string:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    conn = get_connection()
    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return jsonify({}), 200


if __name__ == "__main__":
    init_db()
    app.run(debug=False)
