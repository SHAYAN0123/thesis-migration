import os
import shutil

from config import STORAGE_PATH


def upload_file(task_id, filename, file_data):
    task_dir = os.path.join(STORAGE_PATH, task_id)
    os.makedirs(task_dir, exist_ok=True)
    with open(os.path.join(task_dir, filename), "wb") as f:
        f.write(file_data)
    return f"/files/{task_id}/{filename}"


def list_files(task_id):
    task_dir = os.path.join(STORAGE_PATH, task_id)
    if not os.path.isdir(task_dir):
        return []
    return [f"/files/{task_id}/{name}" for name in os.listdir(task_dir)]


def delete_files(task_id):
    task_dir = os.path.join(STORAGE_PATH, task_id)
    if os.path.isdir(task_dir):
        shutil.rmtree(task_dir)
