"""
Pytest configuration for spec-driven equivalence tests (Evidence — E).

Supports two systems via the TEST_SYSTEM_PATH env var:

  P_n  (old-system, default) — uses moto to mock DynamoDB + S3 + SQS.
  P_n+1 (new-system)         — uses SQLite + local filesystem + file queue.
                               Set TEST_SYSTEM_PATH=<path-to-new-system>.

Both sets of 39 tests must pass on both systems — that is the proof of
semantic equivalence.

Design notes
────────────
• moto is started at module-load time (before any app import) so that
  boto3 clients created at module scope in the old-system land inside
  the mock. For P_n+1 no boto3 is used; the mock context is harmless.
• Temp paths (DB_PATH, STORAGE_PATH, QUEUE_PATH) are set before any
  app module is imported so P_n+1's config.py picks them up.
• _clean_state (autouse) resets ALL possible state after every test:
  AWS mocks (old-system) + SQLite/filesystem/queue (new-system).
  The cleanup paths that are irrelevant for the active system are no-ops.
• sqs_messages reads from both sources and combines; only one will be
  populated for a given system.
"""
import json
import os
import shutil
import sqlite3
import tempfile

import boto3
import pytest
from moto import mock_aws

# ── System under test ────────────────────────────────────────────────────────

_SYSTEM_PATH = os.path.abspath(
    os.environ.get(
        "TEST_SYSTEM_PATH",
        os.path.join(os.path.dirname(__file__), "..", "old-system"),
    )
)

# ── Start moto before any app module is imported ─────────────────────────────

_mock = mock_aws()
_mock.start()

# ── Fake AWS credentials (required by moto / boto3) ──────────────────────────

os.environ.update(
    {
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_SECURITY_TOKEN": "testing",
        "AWS_SESSION_TOKEN": "testing",
        "AWS_DEFAULT_REGION": "eu-west-1",
        "DYNAMODB_TABLE": "tasks",
        "S3_BUCKET": "task-attachments",
    }
)

# ── Mocked AWS resources (old-system) ────────────────────────────────────────

_dynamo = boto3.resource("dynamodb", region_name="eu-west-1")
_table = _dynamo.create_table(
    TableName="tasks",
    KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
    AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
    BillingMode="PAY_PER_REQUEST",
)

_s3 = boto3.client("s3", region_name="eu-west-1")
_s3.create_bucket(
    Bucket="task-attachments",
    CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
)

_sqs = boto3.client("sqs", region_name="eu-west-1")
_queue = _sqs.create_queue(QueueName="task-notifications")
# Write the moto-assigned URL back so old-system config.py picks it up.
os.environ["SQS_QUEUE_URL"] = _queue["QueueUrl"]

# ── Local resource paths (new-system) ────────────────────────────────────────

_tmpdir = tempfile.mkdtemp(prefix="evidence_")
_db_path = os.path.join(_tmpdir, "test_tasks.db")
_storage_path = os.path.join(_tmpdir, "uploads")
_queue_path = os.path.join(_tmpdir, "notifications.queue")

os.makedirs(_storage_path, exist_ok=True)

# Set before any app import; new-system config.py reads these.
os.environ.setdefault("DB_PATH", _db_path)
os.environ.setdefault("STORAGE_PATH", _storage_path)
os.environ.setdefault("QUEUE_PATH", _queue_path)

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def app():
    import sys

    if _SYSTEM_PATH not in sys.path:
        sys.path.insert(0, _SYSTEM_PATH)
    import app as flask_module  # noqa: PLC0415

    flask_module.app.config["TESTING"] = True
    return flask_module.app


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def _clean_state():
    """Reset all infrastructure state after each test."""
    yield

    # ── old-system: AWS mocks ──────────────────────────────────────────────
    # DynamoDB
    items = _table.scan().get("Items", [])
    with _table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={"id": item["id"]})
    # S3
    for obj in _s3.list_objects_v2(Bucket="task-attachments").get("Contents", []):
        _s3.delete_object(Bucket="task-attachments", Key=obj["Key"])
    # SQS
    _sqs.purge_queue(QueueUrl=_queue["QueueUrl"])

    # ── new-system: SQLite ─────────────────────────────────────────────────
    if os.path.exists(_db_path):
        conn = sqlite3.connect(_db_path)
        conn.execute("DELETE FROM tasks")
        conn.commit()
        conn.close()

    # ── new-system: filesystem storage ────────────────────────────────────
    if os.path.isdir(_storage_path):
        for entry in os.listdir(_storage_path):
            entry_path = os.path.join(_storage_path, entry)
            if os.path.isdir(entry_path):
                shutil.rmtree(entry_path)
            else:
                os.remove(entry_path)

    # ── new-system: file queue ────────────────────────────────────────────
    if os.path.exists(_queue_path):
        open(_queue_path, "w").close()  # truncate


@pytest.fixture
def sqs_messages():
    """
    Return a callable that reads all notification messages sent during a test.

    Reads from both sources and combines:
    • SQS  — populated by old-system (moto); empty for new-system.
    • File — populated by new-system; empty for old-system.
    """

    def _receive():
        # SQS (old-system)
        response = _sqs.receive_message(
            QueueUrl=_queue["QueueUrl"],
            MaxNumberOfMessages=10,
            WaitTimeSeconds=0,
        )
        messages = [json.loads(m["Body"]) for m in response.get("Messages", [])]

        # File queue (new-system)
        if os.path.exists(_queue_path):
            with open(_queue_path) as f:
                messages.extend(json.loads(line) for line in f if line.strip())

        return messages

    return _receive
