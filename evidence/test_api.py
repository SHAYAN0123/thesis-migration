"""
Spec-driven equivalence tests — Evidence (E).

Every test is derived from /spec/api_spec.md, NOT from implementation
details of the old-system.  These tests must pass on both:
  P_n  — old-system  (cloud-native, AWS)
  P_n+1 — new-system (cloud-agnostic, to be built)

Run against old-system (default):
    pytest evidence/

Run against new-system:
    TEST_SYSTEM_PATH=new-system pytest evidence/
"""
import io
import json


# ── Helper ────────────────────────────────────────────────────────────────────


def make_task(client, title="Test Task", description="A test task"):
    resp = client.post(
        "/tasks",
        json={"title": title, "description": description, "status": "pending"},
    )
    assert resp.status_code == 201, f"make_task failed: {resp.status_code}"
    return resp.get_json()


# ── POST /tasks ───────────────────────────────────────────────────────────────


def test_create_returns_201(client):
    resp = client.post(
        "/tasks",
        json={"title": "T", "description": "D", "status": "pending"},
    )
    assert resp.status_code == 201


def test_create_returns_task_with_id(client):
    task = make_task(client)
    assert "id" in task
    assert isinstance(task["id"], str)
    assert len(task["id"]) > 0


def test_create_persists_title_and_description(client):
    task = make_task(client, title="My Task", description="My desc")
    assert task["title"] == "My Task"
    assert task["description"] == "My desc"


def test_create_default_status_is_pending(client):
    task = make_task(client)
    assert task["status"] == "pending"


def test_create_ids_are_unique(client):
    a = make_task(client, title="Task A")
    b = make_task(client, title="Task B")
    assert a["id"] != b["id"]


# ── GET /tasks ────────────────────────────────────────────────────────────────


def test_list_returns_200(client):
    assert client.get("/tasks").status_code == 200


def test_list_is_empty_initially(client):
    assert client.get("/tasks").get_json() == []


def test_list_contains_created_tasks(client):
    make_task(client, title="Alpha")
    make_task(client, title="Beta")
    titles = [t["title"] for t in client.get("/tasks").get_json()]
    assert "Alpha" in titles
    assert "Beta" in titles


# ── GET /tasks/{id} ───────────────────────────────────────────────────────────


def test_get_one_returns_200(client):
    task = make_task(client)
    assert client.get(f"/tasks/{task['id']}").status_code == 200


def test_get_one_returns_correct_task(client):
    task = make_task(client, title="Needle")
    fetched = client.get(f"/tasks/{task['id']}").get_json()
    assert fetched["id"] == task["id"]
    assert fetched["title"] == "Needle"


def test_get_one_returns_404_when_missing(client):
    assert client.get("/tasks/nonexistent-id-xyz").status_code == 404


# ── PUT /tasks/{id} ───────────────────────────────────────────────────────────


def test_update_returns_200(client):
    task = make_task(client)
    resp = client.put(f"/tasks/{task['id']}", json={"title": "Updated"})
    assert resp.status_code == 200


def test_update_reflects_new_title(client):
    task = make_task(client, title="Before")
    updated = client.put(f"/tasks/{task['id']}", json={"title": "After"}).get_json()
    assert updated["title"] == "After"


def test_update_reflects_new_status(client):
    task = make_task(client)
    updated = client.put(
        f"/tasks/{task['id']}", json={"status": "completed"}
    ).get_json()
    assert updated["status"] == "completed"


def test_update_returns_404_when_missing(client):
    assert client.put("/tasks/nonexistent-id-xyz", json={"title": "X"}).status_code == 404


def test_update_sends_notification_on_first_completion(client, sqs_messages):
    task = make_task(client)
    client.put(f"/tasks/{task['id']}", json={"status": "completed"})
    messages = sqs_messages()
    assert len(messages) == 1
    assert messages[0]["event"] == "task_completed"
    assert messages[0]["task_id"] == task["id"]


def test_update_notification_includes_title(client, sqs_messages):
    task = make_task(client, title="Important Task")
    client.put(f"/tasks/{task['id']}", json={"status": "completed"})
    msg = sqs_messages()[0]
    assert msg["title"] == "Important Task"


def test_update_no_notification_for_non_completion_change(client, sqs_messages):
    task = make_task(client)
    client.put(f"/tasks/{task['id']}", json={"title": "Just a rename"})
    assert sqs_messages() == []


def test_update_no_duplicate_notification_when_already_completed(client, sqs_messages):
    task = make_task(client)
    client.put(f"/tasks/{task['id']}", json={"status": "completed"})
    client.put(f"/tasks/{task['id']}", json={"status": "completed"})
    assert len(sqs_messages()) == 1


# ── DELETE /tasks/{id} ────────────────────────────────────────────────────────


def test_delete_returns_204(client):
    task = make_task(client)
    assert client.delete(f"/tasks/{task['id']}").status_code == 204


def test_delete_removes_task_from_store(client):
    task = make_task(client)
    client.delete(f"/tasks/{task['id']}")
    assert client.get(f"/tasks/{task['id']}").status_code == 404


def test_delete_removes_task_from_list(client):
    task = make_task(client)
    client.delete(f"/tasks/{task['id']}")
    ids = [t["id"] for t in client.get("/tasks").get_json()]
    assert task["id"] not in ids


def test_delete_removes_attached_files(client):
    task = make_task(client)
    client.post(
        f"/tasks/{task['id']}/upload",
        data={"file": (io.BytesIO(b"data"), "attachment.txt")},
        content_type="multipart/form-data",
    )
    client.delete(f"/tasks/{task['id']}")
    files = client.get(f"/tasks/{task['id']}/files").get_json()
    assert files == []


# ── POST /tasks/{id}/upload ───────────────────────────────────────────────────


def test_upload_returns_201(client):
    task = make_task(client)
    resp = client.post(
        f"/tasks/{task['id']}/upload",
        data={"file": (io.BytesIO(b"hello"), "hello.txt")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201


def test_upload_returns_url_string(client):
    task = make_task(client)
    resp = client.post(
        f"/tasks/{task['id']}/upload",
        data={"file": (io.BytesIO(b"hello"), "hello.txt")},
        content_type="multipart/form-data",
    )
    body = resp.get_json()
    assert "url" in body
    assert isinstance(body["url"], str)
    assert len(body["url"]) > 0


def test_upload_returns_404_for_unknown_task(client):
    resp = client.post(
        "/tasks/nonexistent-id/upload",
        data={"file": (io.BytesIO(b"x"), "x.txt")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 404


def test_upload_file_url_not_stored_in_task_record(client):
    """Spec rule: file uploads go to object storage, not the database."""
    task = make_task(client)
    resp = client.post(
        f"/tasks/{task['id']}/upload",
        data={"file": (io.BytesIO(b"content"), "report.pdf")},
        content_type="multipart/form-data",
    )
    url = resp.get_json()["url"]
    task_json = json.dumps(client.get(f"/tasks/{task['id']}").get_json())
    assert url not in task_json


# ── GET /tasks/{id}/files ─────────────────────────────────────────────────────


def test_list_files_returns_200(client):
    task = make_task(client)
    assert client.get(f"/tasks/{task['id']}/files").status_code == 200


def test_list_files_empty_before_upload(client):
    task = make_task(client)
    assert client.get(f"/tasks/{task['id']}/files").get_json() == []


def test_list_files_contains_uploaded_url(client):
    task = make_task(client)
    url = client.post(
        f"/tasks/{task['id']}/upload",
        data={"file": (io.BytesIO(b"x"), "doc.txt")},
        content_type="multipart/form-data",
    ).get_json()["url"]
    assert url in client.get(f"/tasks/{task['id']}/files").get_json()


def test_list_files_returns_all_uploads(client):
    task = make_task(client)
    for name in ("a.txt", "b.txt", "c.txt"):
        client.post(
            f"/tasks/{task['id']}/upload",
            data={"file": (io.BytesIO(b"x"), name)},
            content_type="multipart/form-data",
        )
    assert len(client.get(f"/tasks/{task['id']}/files").get_json()) == 3


# ── Behavior rules (spec §Behavior Rules) ────────────────────────────────────


def test_task_id_is_a_non_empty_string(client):
    task = make_task(client)
    assert isinstance(task["id"], str) and len(task["id"]) > 0


def test_multiple_task_ids_are_unique(client):
    ids = [make_task(client, title=f"T{i}")["id"] for i in range(5)]
    assert len(ids) == len(set(ids))


def test_create_response_is_json(client):
    resp = client.post("/tasks", json={"title": "T", "description": "", "status": "pending"})
    assert "application/json" in resp.content_type


def test_list_response_is_json(client):
    assert "application/json" in client.get("/tasks").content_type


def test_get_one_response_is_json(client):
    task = make_task(client)
    assert "application/json" in client.get(f"/tasks/{task['id']}").content_type


def test_update_response_is_json(client):
    task = make_task(client)
    resp = client.put(f"/tasks/{task['id']}", json={"title": "X"})
    assert "application/json" in resp.content_type


def test_upload_response_is_json(client):
    task = make_task(client)
    resp = client.post(
        f"/tasks/{task['id']}/upload",
        data={"file": (io.BytesIO(b"x"), "f.txt")},
        content_type="multipart/form-data",
    )
    assert "application/json" in resp.content_type


def test_files_response_is_json(client):
    task = make_task(client)
    assert "application/json" in client.get(f"/tasks/{task['id']}/files").content_type
