import time
import uuid

from flask import Flask, jsonify, request

from database import init_db, get_db

app = Flask(__name__)
init_db()


@app.route("/todos", methods=["POST"])
def create_todo():
    data = request.get_json(force=True)
    if not data or "text" not in data:
        return jsonify({"error": "Couldn't create the todo item."}), 400

    timestamp = str(time.time())
    item = {
        "id": str(uuid.uuid1()),
        "text": data["text"],
        "checked": False,
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }

    db = get_db()
    db.execute(
        "INSERT INTO todos (id, text, checked, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?)",
        (item["id"], item["text"], item["checked"], item["createdAt"], item["updatedAt"]),
    )
    db.commit()

    return jsonify(item), 200


@app.route("/todos", methods=["GET"])
def list_todos():
    db = get_db()
    rows = db.execute("SELECT id, text, checked, createdAt, updatedAt FROM todos").fetchall()
    items = [_row_to_dict(row) for row in rows]
    return jsonify(items), 200


@app.route("/todos/<string:todo_id>", methods=["GET"])
def get_todo(todo_id):
    db = get_db()
    row = db.execute(
        "SELECT id, text, checked, createdAt, updatedAt FROM todos WHERE id = ?", (todo_id,)
    ).fetchone()
    if row is None:
        return jsonify({"error": "Todo not found."}), 404
    return jsonify(_row_to_dict(row)), 200


@app.route("/todos/<string:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    data = request.get_json(force=True)
    if not data or "text" not in data or "checked" not in data:
        return jsonify({"error": "Couldn't update the todo item."}), 400

    timestamp = str(int(time.time() * 1000))

    db = get_db()
    cursor = db.execute(
        "UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?",
        (data["text"], data["checked"], timestamp, todo_id),
    )
    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Todo not found."}), 404

    row = db.execute(
        "SELECT id, text, checked, createdAt, updatedAt FROM todos WHERE id = ?", (todo_id,)
    ).fetchone()
    return jsonify(_row_to_dict(row)), 200


@app.route("/todos/<string:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    db = get_db()
    db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    db.commit()
    return jsonify({}), 200


def _row_to_dict(row):
    return {
        "id": row["id"],
        "text": row["text"],
        "checked": bool(row["checked"]),
        "createdAt": row["createdAt"],
        "updatedAt": row["updatedAt"],
    }


if __name__ == "__main__":
    app.run(debug=True)
