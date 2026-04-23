import uuid
from flask import Flask, request, jsonify
from database import create_task, get_all_tasks, get_task, update_task, delete_task
from storage import upload_file, list_files, delete_files
from notifications import send_completion_notification

app = Flask(__name__)


@app.route("/tasks", methods=["POST"])
def create():
    data = request.get_json()
    task = {
        "id": str(uuid.uuid4()),
        "title": data["title"],
        "description": data.get("description", ""),
        "status": "pending",
    }
    created = create_task(task)
    return jsonify(created), 201


@app.route("/tasks", methods=["GET"])
def list_all():
    tasks = get_all_tasks()
    return jsonify(tasks)


@app.route("/tasks/<task_id>", methods=["GET"])
def get_one(task_id):
    task = get_task(task_id)
    if not task:
        return jsonify({"error": "not found"}), 404
    return jsonify(task)


@app.route("/tasks/<task_id>", methods=["PUT"])
def update(task_id):
    data = request.get_json()
    old_task = get_task(task_id)
    if not old_task:
        return jsonify({"error": "not found"}), 404

    updated = update_task(task_id, data)

    if data.get("status") == "completed" and old_task.get("status") != "completed":
        send_completion_notification(updated)

    return jsonify(updated)


@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete(task_id):
    delete_files(task_id)
    delete_task(task_id)
    return "", 204


@app.route("/tasks/<task_id>/upload", methods=["POST"])
def upload(task_id):
    task = get_task(task_id)
    if not task:
        return jsonify({"error": "not found"}), 404

    file = request.files["file"]
    url = upload_file(task_id, file.filename, file.read())
    return jsonify({"url": url}), 201


@app.route("/tasks/<task_id>/files", methods=["GET"])
def files(task_id):
    urls = list_files(task_id)
    return jsonify(urls)


if __name__ == "__main__":
    app.run(port=5000, debug=True)