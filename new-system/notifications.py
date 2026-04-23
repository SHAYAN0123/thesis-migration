import json
import os

from config import QUEUE_PATH


def send_completion_notification(task):
    message = {
        "event": "task_completed",
        "task_id": task["id"],
        "title": task["title"],
    }
    with open(QUEUE_PATH, "a") as f:
        f.write(json.dumps(message) + "\n")
