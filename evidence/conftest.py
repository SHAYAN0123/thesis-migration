"""
Pytest configuration for spec-driven equivalence tests (Evidence — E).

This conftest starts a moto AWS mock at import time — before any app
module is imported — so that boto3 clients created at module scope inside
the old-system (database.py, storage.py, notifications.py) land inside
the mock rather than hitting real AWS.

The same test suite runs against P_n+1 by setting:
    TEST_SYSTEM_PATH=<path-to-new-system> pytest evidence/

P_n+1 may not use boto3 at all; the moto mock is then harmless.
If P_n+1 needs its own infrastructure cleanup between tests, override
the `_clean_state` fixture in a second conftest inside the new-system
test directory.
"""
import atexit
import json
import os
import sys

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

# ── Start moto at module-load time ───────────────────────────────────────────
# This must happen before any boto3 client/resource is instantiated so that
# all module-level boto3 objects (in database.py etc.) bind to the mock.

_mock = mock_aws()
_mock.start()
atexit.register(_mock.stop)

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

# ── Create mocked AWS resources ──────────────────────────────────────────────

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
# Write the real moto URL back so config.py picks it up on import.
os.environ["SQS_QUEUE_URL"] = _queue["QueueUrl"]

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def app():
    """Import and return the Flask application under test."""
    if _SYSTEM_PATH not in sys.path:
        sys.path.insert(0, _SYSTEM_PATH)
    import app as flask_module  # noqa: PLC0415

    flask_module.app.config["TESTING"] = True
    return flask_module.app


@pytest.fixture
def client(app):
    """Yield a Flask test client for a single test."""
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def _clean_state():
    """Reset all mocked AWS state after each test for isolation."""
    yield
    # DynamoDB — delete every item
    items = _table.scan().get("Items", [])
    with _table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={"id": item["id"]})
    # S3 — delete every object
    for obj in _s3.list_objects_v2(Bucket="task-attachments").get("Contents", []):
        _s3.delete_object(Bucket="task-attachments", Key=obj["Key"])
    # SQS — purge all messages (moto: no 60-second cooldown enforced)
    _sqs.purge_queue(QueueUrl=_queue["QueueUrl"])


@pytest.fixture
def sqs_messages():
    """Return a callable that reads all messages from the notification queue."""

    def _receive():
        response = _sqs.receive_message(
            QueueUrl=_queue["QueueUrl"],
            MaxNumberOfMessages=10,
            WaitTimeSeconds=0,
        )
        return [json.loads(m["Body"]) for m in response.get("Messages", [])]

    return _receive
