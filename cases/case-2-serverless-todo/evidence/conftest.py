"""
Pytest configuration for case-2-serverless-todo spec-driven equivalence tests.

Supports two systems via the TEST_SYSTEM_PATH env var:

  P_n  (old-system, default) — wraps Lambda handlers in a Flask adapter;
                               uses moto to mock DynamoDB.
  P_n+1 (new-system)         — loads a Flask/WSGI app directly; uses SQLite.
                               Set TEST_SYSTEM_PATH=<path-to-new-system>.

Both systems are exercised through the same Flask test client so every test
is identical for both.  The Lambda adapter translates HTTP-style requests
into API Gateway Proxy event dicts and converts the handler response dicts
back to Flask Response objects.

Design notes
────────────
• moto is started at module-load time (before any app import) so that the
  boto3 clients initialised at module scope inside each Lambda handler land
  inside the mock.  For P_n+1 no boto3 is used; the mock context is harmless.
• The old-system directory is exposed as the 'todos' package (mirroring the
  serverless.yml handler paths 'todos/create.create' etc.) by inserting a
  synthetic module into sys.modules before importing the handler modules.
• _clean_state (autouse) wipes all possible storage after every test.  The
  cleanup paths that do not apply to the active system are no-ops.
"""
import importlib
import json
import os
import sqlite3
import sys
import tempfile
import types

import boto3
import pytest
from flask import Flask, Response, request
from moto import mock_aws

# ── System under test ────────────────────────────────────────────────────────

_SYSTEM_PATH = os.path.abspath(
    os.environ.get(
        "TEST_SYSTEM_PATH",
        os.path.join(os.path.dirname(__file__), "..", "old-system"),
    )
)
_IS_OLD_SYSTEM = os.path.basename(_SYSTEM_PATH) == "old-system"

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
        "DYNAMODB_TABLE": "todos",
    }
)

# ── Mocked DynamoDB table (old-system) ────────────────────────────────────────

_dynamo = boto3.resource("dynamodb", region_name="eu-west-1")
_table = _dynamo.create_table(
    TableName="todos",
    KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
    AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
    BillingMode="PAY_PER_REQUEST",
)

# ── Local resource paths (new-system) ─────────────────────────────────────────

_tmpdir = tempfile.mkdtemp(prefix="evidence_case2_")
_db_path = os.path.join(_tmpdir, "test_todos.db")
os.environ.setdefault("DB_PATH", _db_path)


# ── Lambda → Flask adapter ────────────────────────────────────────────────────

def _build_lambda_adapter():
    """
    Wrap the five Lambda handler functions in a Flask app so all tests can
    use a single, uniform Flask test client regardless of which system is
    under test.

    The old-system files live at:
        old-system/{create,list,get,update,delete}.py

    In the serverless deployment the project root is the parent of the todos/
    package and the handlers are addressed as 'todos.create.create' etc.  We
    replicate that layout by inserting a synthetic 'todos' package whose
    __path__ points at _SYSTEM_PATH, then importing each handler module via
    the 'todos.*' namespace.
    """
    # Expose old-system/ as the 'todos' package
    todos_pkg = types.ModuleType("todos")
    todos_pkg.__path__ = [_SYSTEM_PATH]
    todos_pkg.__package__ = "todos"
    sys.modules["todos"] = todos_pkg

    if _SYSTEM_PATH not in sys.path:
        sys.path.insert(0, _SYSTEM_PATH)

    # Clear any stale module cache before (re)importing
    for _name in [
        "todos.create", "todos.list", "todos.get",
        "todos.update", "todos.delete", "todos.decimalencoder",
    ]:
        sys.modules.pop(_name, None)

    create_mod = importlib.import_module("todos.create")
    list_mod = importlib.import_module("todos.list")
    get_mod = importlib.import_module("todos.get")
    update_mod = importlib.import_module("todos.update")
    delete_mod = importlib.import_module("todos.delete")

    adapter = Flask(__name__)

    def _event(path_params=None):
        """Build a minimal API Gateway Proxy event from the current request."""
        body = request.get_data(as_text=True) or None
        return {"body": body, "pathParameters": path_params}

    def _respond(result):
        """Convert a Lambda response dict to a Flask Response."""
        status = result.get("statusCode", 200)
        body = result.get("body", "")
        ctype = "application/json" if body else "text/plain"
        return Response(body or "", status=status, content_type=ctype)

    @adapter.route("/todos", methods=["POST"])
    def do_create():
        try:
            return _respond(create_mod.create(_event(), None))
        except Exception as exc:
            return Response(
                json.dumps({"error": str(exc)}), status=400,
                content_type="application/json",
            )

    @adapter.route("/todos", methods=["GET"])
    def do_list():
        return _respond(list_mod.list(_event(), None))

    @adapter.route("/todos/<todo_id>", methods=["GET"])
    def do_get(todo_id):
        try:
            return _respond(get_mod.get(_event({"id": todo_id}), None))
        except KeyError:
            return Response(
                json.dumps({"error": "not found"}), status=404,
                content_type="application/json",
            )

    @adapter.route("/todos/<todo_id>", methods=["PUT"])
    def do_update(todo_id):
        return _respond(update_mod.update(_event({"id": todo_id}), None))

    @adapter.route("/todos/<todo_id>", methods=["DELETE"])
    def do_delete(todo_id):
        return _respond(delete_mod.delete(_event({"id": todo_id}), None))

    return adapter


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def app():
    if _IS_OLD_SYSTEM:
        return _build_lambda_adapter()

    # New-system: import a Flask/WSGI app directly from the system path.
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
    """Reset all storage state between tests."""
    yield

    # ── old-system: DynamoDB (moto) ───────────────────────────────────────
    items = _table.scan().get("Items", [])
    with _table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={"id": item["id"]})

    # ── new-system: SQLite ────────────────────────────────────────────────
    if os.path.exists(_db_path):
        conn = sqlite3.connect(_db_path)
        try:
            conn.execute("DELETE FROM todos")
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()
