import os

DB_PATH = os.environ.get("DB_PATH", "tasks.db")
STORAGE_PATH = os.environ.get("STORAGE_PATH", "uploads")
QUEUE_PATH = os.environ.get("QUEUE_PATH", "notifications.queue")
