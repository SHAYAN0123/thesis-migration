"""
Spec-driven equivalence tests — Evidence (E), case-2-serverless-todo.

Every test is derived exclusively from spec/api_spec.md.  No test references
DynamoDB, boto3, Lambda, or any other implementation detail of the old-system.

Run against old-system (default):
    pytest cases/case-2-serverless-todo/evidence/

Run against new-system:
    TEST_SYSTEM_PATH=cases/case-2-serverless-todo/new-system \
        pytest cases/case-2-serverless-todo/evidence/

Both systems must pass all 39 tests.  Passing on both systems is the proof of
semantic equivalence required by the migration thesis.

Spec reference: cases/case-2-serverless-todo/spec/api_spec.md
"""
import time
import uuid


# ── Helper ────────────────────────────────────────────────────────────────────


def make_todo(client, text="Buy milk"):
    resp = client.post("/todos", json={"text": text})
    assert resp.status_code == 200, f"make_todo failed with {resp.status_code}: {resp.data}"
    return resp.get_json()


# ── POST /todos ───────────────────────────────────────────────────────────────


def test_create_returns_200(client):
    # Spec: "Status: 200"
    resp = client.post("/todos", json={"text": "Walk the dog"})
    assert resp.status_code == 200


def test_create_response_is_json(client):
    resp = client.post("/todos", json={"text": "Walk the dog"})
    assert "application/json" in resp.content_type


def test_create_response_contains_id(client):
    # Spec data model: id field is required
    todo = make_todo(client)
    assert "id" in todo


def test_create_id_is_non_empty_string(client):
    # Spec: "id: string, required, Unique identifier (UUID)"
    todo = make_todo(client)
    assert isinstance(todo["id"], str)
    assert len(todo["id"]) > 0


def test_create_id_is_valid_uuid(client):
    # Spec: "Unique identifier (UUID)"
    todo = make_todo(client)
    # Raises ValueError if not a valid UUID of any version
    uuid.UUID(todo["id"])


def test_create_text_is_stored(client):
    # Spec: "text: string, required, The todo content"
    todo = make_todo(client, text="Buy coffee")
    assert todo["text"] == "Buy coffee"


def test_create_checked_defaults_to_false(client):
    # Spec behavior rule 2: "Every created todo MUST have `checked` set to `false` by default"
    todo = make_todo(client)
    assert todo["checked"] is False


def test_create_has_created_at(client):
    # Spec: "createdAt: string, required, Timestamp when created"
    todo = make_todo(client)
    assert "createdAt" in todo
    assert todo["createdAt"] is not None
    assert str(todo["createdAt"]) != ""


def test_create_has_updated_at(client):
    # Spec: "updatedAt: string, required, Timestamp when last updated"
    todo = make_todo(client)
    assert "updatedAt" in todo
    assert todo["updatedAt"] is not None
    assert str(todo["updatedAt"]) != ""


def test_create_without_text_returns_error(client):
    # Spec: "Request body: JSON with `text` field (required)"
    resp = client.post("/todos", json={})
    assert resp.status_code != 200


# ── GET /todos ────────────────────────────────────────────────────────────────


def test_list_returns_200(client):
    # Spec: "Status: 200"
    assert client.get("/todos").status_code == 200


def test_list_response_is_json(client):
    assert "application/json" in client.get("/todos").content_type


def test_list_returns_array(client):
    # Spec: "Returns: JSON array of all todos"
    body = client.get("/todos").get_json()
    assert isinstance(body, list)


def test_list_is_empty_before_any_create(client):
    assert client.get("/todos").get_json() == []


def test_list_contains_created_todo(client):
    # Spec behavior rule 7: "Listing todos MUST return ALL existing todos"
    todo = make_todo(client, text="Unique entry A")
    ids = [t["id"] for t in client.get("/todos").get_json()]
    assert todo["id"] in ids


def test_list_returns_all_todos(client):
    # Spec behavior rule 7
    a = make_todo(client, text="Alpha")
    b = make_todo(client, text="Beta")
    c = make_todo(client, text="Gamma")
    ids = {t["id"] for t in client.get("/todos").get_json()}
    assert {a["id"], b["id"], c["id"]}.issubset(ids)


# ── GET /todos/{id} ───────────────────────────────────────────────────────────


def test_get_one_returns_200(client):
    # Spec: "Status: 200"
    todo = make_todo(client)
    assert client.get(f"/todos/{todo['id']}").status_code == 200


def test_get_one_response_is_json(client):
    todo = make_todo(client)
    assert "application/json" in client.get(f"/todos/{todo['id']}").content_type


def test_get_one_returns_correct_todo(client):
    todo = make_todo(client, text="Needle in a haystack")
    fetched = client.get(f"/todos/{todo['id']}").get_json()
    assert fetched["id"] == todo["id"]
    assert fetched["text"] == "Needle in a haystack"


def test_get_one_returns_all_five_fields(client):
    # Spec data model requires: id, text, checked, createdAt, updatedAt
    todo = make_todo(client)
    fetched = client.get(f"/todos/{todo['id']}").get_json()
    for field in ("id", "text", "checked", "createdAt", "updatedAt"):
        assert field in fetched, f"field '{field}' missing from GET /todos/{{id}} response"


def test_get_one_returns_404_for_unknown_id(client):
    # Spec: "If not found: returns error (status 404 or equivalent)"
    resp = client.get("/todos/nonexistent-id-that-does-not-exist")
    assert resp.status_code == 404


# ── PUT /todos/{id} ───────────────────────────────────────────────────────────


def test_update_returns_200(client):
    # Spec: "Status: 200"
    todo = make_todo(client)
    resp = client.put(f"/todos/{todo['id']}", json={"text": "Updated", "checked": False})
    assert resp.status_code == 200


def test_update_response_is_json(client):
    todo = make_todo(client)
    resp = client.put(f"/todos/{todo['id']}", json={"text": "X", "checked": False})
    assert "application/json" in resp.content_type


def test_update_text_is_changed(client):
    # Spec: "Updates the todo's text"
    todo = make_todo(client, text="Before")
    result = client.put(
        f"/todos/{todo['id']}", json={"text": "After", "checked": False}
    ).get_json()
    assert result["text"] == "After"


def test_update_checked_can_be_set_to_true(client):
    # Spec: "Updates the todo's checked status"
    todo = make_todo(client)
    result = client.put(
        f"/todos/{todo['id']}", json={"text": todo["text"], "checked": True}
    ).get_json()
    assert result["checked"] is True


def test_update_checked_can_be_toggled_back_to_false(client):
    todo = make_todo(client)
    client.put(f"/todos/{todo['id']}", json={"text": todo["text"], "checked": True})
    result = client.put(
        f"/todos/{todo['id']}", json={"text": todo["text"], "checked": False}
    ).get_json()
    assert result["checked"] is False


def test_update_response_includes_updated_at(client):
    # Spec: "Returns: the updated todo attributes as JSON"
    todo = make_todo(client)
    result = client.put(
        f"/todos/{todo['id']}", json={"text": "New text", "checked": False}
    ).get_json()
    assert "updatedAt" in result


def test_update_changes_updated_at_timestamp(client):
    # Spec behavior rule 4: "Updating a todo MUST change the `updatedAt` timestamp"
    todo = make_todo(client)
    original_ts = str(todo["updatedAt"])
    time.sleep(0.05)  # ensure clock advances
    result = client.put(
        f"/todos/{todo['id']}", json={"text": "Changed", "checked": False}
    ).get_json()
    assert str(result["updatedAt"]) != original_ts


def test_update_does_not_change_id(client):
    # Spec behavior rule 5: "Updating a todo MUST NOT change the `id`"
    todo = make_todo(client)
    result = client.put(
        f"/todos/{todo['id']}", json={"text": "New", "checked": False}
    ).get_json()
    assert result["id"] == todo["id"]


def test_update_does_not_change_created_at(client):
    # Spec behavior rule 5: "Updating a todo MUST NOT change the `createdAt`"
    todo = make_todo(client)
    original_created_at = str(todo["createdAt"])
    time.sleep(0.05)
    # Read the persisted state via GET after the update
    client.put(f"/todos/{todo['id']}", json={"text": "Changed", "checked": False})
    fetched = client.get(f"/todos/{todo['id']}").get_json()
    assert str(fetched["createdAt"]) == original_created_at


# ── DELETE /todos/{id} ────────────────────────────────────────────────────────


def test_delete_returns_200(client):
    # Spec: "Status: 200"
    todo = make_todo(client)
    assert client.delete(f"/todos/{todo['id']}").status_code == 200


def test_delete_subsequent_get_returns_404(client):
    # Spec behavior rule 6: "subsequent GET returns not found"
    todo = make_todo(client)
    client.delete(f"/todos/{todo['id']}")
    assert client.get(f"/todos/{todo['id']}").status_code == 404


def test_delete_removes_todo_from_list(client):
    todo = make_todo(client)
    client.delete(f"/todos/{todo['id']}")
    ids = [t["id"] for t in client.get("/todos").get_json()]
    assert todo["id"] not in ids


def test_delete_does_not_affect_other_todos(client):
    keep = make_todo(client, text="Keep me")
    remove = make_todo(client, text="Remove me")
    client.delete(f"/todos/{remove['id']}")
    ids = [t["id"] for t in client.get("/todos").get_json()]
    assert keep["id"] in ids


# ── Behavior rules (spec §Behavior Rules) ────────────────────────────────────


def test_spec_rule_1_ids_are_unique_uuids(client):
    """Rule 1: Every created todo MUST have a unique UUID as its id."""
    ids = [make_todo(client, text=f"Item {i}")["id"] for i in range(5)]
    # All unique
    assert len(ids) == len(set(ids))
    # All valid UUIDs
    for id_ in ids:
        uuid.UUID(id_)


def test_spec_rule_2_checked_is_false_by_default(client):
    """Rule 2: Every created todo MUST have `checked` set to `false` by default."""
    for i in range(3):
        assert make_todo(client, text=f"T{i}")["checked"] is False


def test_spec_rule_3_timestamps_recorded_on_create(client):
    """Rule 3: Every created todo MUST record createdAt and updatedAt."""
    todo = make_todo(client)
    assert todo.get("createdAt") not in (None, "")
    assert todo.get("updatedAt") not in (None, "")


def test_spec_rule_4_updated_at_changes_on_update(client):
    """Rule 4: Updating a todo MUST change the updatedAt timestamp."""
    todo = make_todo(client)
    original_ts = str(todo["updatedAt"])
    time.sleep(0.05)
    client.put(f"/todos/{todo['id']}", json={"text": "Modified", "checked": False})
    fetched = client.get(f"/todos/{todo['id']}").get_json()
    assert str(fetched["updatedAt"]) != original_ts


def test_spec_rule_5_id_immutable_after_update(client):
    """Rule 5: Updating a todo MUST NOT change the id."""
    todo = make_todo(client)
    original_id = todo["id"]
    client.put(f"/todos/{todo['id']}", json={"text": "New text", "checked": True})
    fetched = client.get(f"/todos/{todo['id']}").get_json()
    assert fetched["id"] == original_id


def test_spec_rule_5_created_at_immutable_after_update(client):
    """Rule 5: Updating a todo MUST NOT change the createdAt."""
    todo = make_todo(client)
    original_created_at = str(todo["createdAt"])
    time.sleep(0.05)
    client.put(f"/todos/{todo['id']}", json={"text": "New text", "checked": False})
    fetched = client.get(f"/todos/{todo['id']}").get_json()
    assert str(fetched["createdAt"]) == original_created_at


def test_spec_rule_6_delete_is_permanent(client):
    """Rule 6: Deleting a todo MUST remove it permanently."""
    todo = make_todo(client)
    client.delete(f"/todos/{todo['id']}")
    # Not accessible by ID
    assert client.get(f"/todos/{todo['id']}").status_code == 404
    # Not in the list
    ids = [t["id"] for t in client.get("/todos").get_json()]
    assert todo["id"] not in ids


def test_spec_rule_7_list_returns_all_existing_todos(client):
    """Rule 7: Listing todos MUST return ALL existing todos."""
    created = {make_todo(client, text=f"Todo {i}")["id"] for i in range(4)}
    listed = {t["id"] for t in client.get("/todos").get_json()}
    assert created.issubset(listed)


def test_spec_rule_8_data_persists_between_requests(client):
    """Rule 8: The service MUST persist data between requests (not in-memory only)."""
    todo = make_todo(client, text="Persistent item")
    # Simulate a subsequent independent request (separate GET)
    fetched = client.get(f"/todos/{todo['id']}").get_json()
    assert fetched["id"] == todo["id"]
    assert fetched["text"] == "Persistent item"
    # Also survives appearing in the list
    ids = [t["id"] for t in client.get("/todos").get_json()]
    assert todo["id"] in ids
