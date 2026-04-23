# Transformation Log — P_n → P_n+1

**From:** `old-system/` (cloud-native, AWS-backed)
**To:** `new-system/` (cloud-agnostic, stdlib-only)
**Specification:** `/spec/api_spec.md` — unchanged
**Evidence:** `evidence/` — 39 tests pass on both P_n and P_n+1

---

## Summary

Four infrastructure modules were rewritten to remove all `boto3` / AWS
dependencies.  `app.py` is byte-for-byte identical in both systems.  The
public function signatures in `database.py`, `storage.py`, and
`notifications.py` are unchanged so `app.py` required zero edits.

| File | P_n (old-system) | P_n+1 (new-system) | Change |
|------|-----------------|-------------------|--------|
| `app.py` | Flask routes | Flask routes | **None** — identical copy |
| `config.py` | AWS env vars | Generic env vars | Rewritten |
| `database.py` | DynamoDB via boto3 | SQLite via stdlib `sqlite3` | Rewritten |
| `storage.py` | S3 via boto3 | Local filesystem via stdlib `os`/`shutil` | Rewritten |
| `notifications.py` | SQS via boto3 | File-based queue via stdlib `json`/`os` | Rewritten |
| `requirements.txt` | `flask`, `boto3` | `flask` only | boto3 removed |

Lock-in points resolved: **4 / 4** (DEP-1 DynamoDB, DEP-2 S3, DEP-3 SQS, DEP-4 config)

---

## File-by-file changes

### `config.py`

**Lock-in addressed:** DEP-4 (AWS Region + SQS URL hard-coding)

| Old | New |
|-----|-----|
| `AWS_REGION = "eu-west-1"` | *(removed)* |
| `DYNAMODB_TABLE = "tasks"` | `DB_PATH = "tasks.db"` |
| `S3_BUCKET = "task-attachments"` | `STORAGE_PATH = "uploads"` |
| `SQS_QUEUE_URL = "https://sqs.eu-west-1.amazonaws.com/..."` | `QUEUE_PATH = "notifications.queue"` |

All three variables remain overridable via environment variables.
AWS-specific names and URI defaults are gone.

---

### `database.py`

**Lock-in addressed:** DEP-1 (DynamoDB / boto3)

Replaced the DynamoDB resource (`boto3.resource("dynamodb")`) and all five
proprietary API calls with standard SQL via Python's built-in `sqlite3`.

| Old (DynamoDB) | New (SQLite) |
|----------------|-------------|
| `boto3.resource("dynamodb")` | `sqlite3.connect(DB_PATH)` |
| `table.put_item(Item=task)` | `INSERT INTO tasks ...` |
| `table.scan()` | `SELECT * FROM tasks` |
| `table.get_item(Key={"id": id})` | `SELECT * FROM tasks WHERE id = ?` |
| `table.update_item(UpdateExpression=..., ExpressionAttributeNames=...)` | `UPDATE tasks SET <cols> = ? WHERE id = ?` |
| `table.delete_item(Key={"id": id})` | `DELETE FROM tasks WHERE id = ?` |

The DynamoDB `UpdateExpression` syntax (`SET #key = :value`,
`ExpressionAttributeNames`) is proprietary and has no standard equivalent;
it was replaced with a parameterised SQL `UPDATE`.

**Security note:** column names in `UPDATE` are filtered against an
explicit allowlist (`title`, `description`, `status`) before interpolation
into the query string, preventing SQL injection from user-supplied keys.

All five public function signatures are unchanged:
`create_task`, `get_all_tasks`, `get_task`, `update_task`, `delete_task`.

---

### `storage.py`

**Lock-in addressed:** DEP-2 (S3 / boto3)

Replaced the S3 client (`boto3.client("s3")`) and three API calls with
stdlib `os` / `shutil` operations on the local filesystem under
`STORAGE_PATH`.

| Old (S3) | New (filesystem) |
|----------|-----------------|
| `boto3.client("s3")` | `os`, `shutil` (stdlib) |
| `s3.put_object(Bucket, Key, Body)` | `open(path, "wb").write(data)` |
| `s3.list_objects_v2(Bucket, Prefix)` | `os.listdir(task_dir)` |
| `s3.delete_object(Bucket, Key)` | `shutil.rmtree(task_dir)` |
| URL: `https://{bucket}.s3.{region}.amazonaws.com/{key}` | URL: `/files/{task_id}/{filename}` |

The hard-coded `amazonaws.com` URL template is replaced with a
path-style URL that is portable and requires no external service.
The `list_files` return values are consistent with `upload_file` output
so the spec contract (upload URL appears in file list) is preserved.

All three public function signatures are unchanged:
`upload_file`, `list_files`, `delete_files`.

---

### `notifications.py`

**Lock-in addressed:** DEP-3 (SQS / boto3)

Replaced the SQS client (`boto3.client("sqs")`) with a JSONL file-based
queue written to `QUEUE_PATH`.

| Old (SQS) | New (file queue) |
|-----------|-----------------|
| `boto3.client("sqs")` | stdlib `json`, `os` |
| `sqs.send_message(QueueUrl=..., MessageBody=...)` | `open(QUEUE_PATH, "a").write(json.dumps(msg) + "\n")` |
| AWS-proprietary protocol | JSONL — open, human-readable, no external service |

The spec requires "completion notifications are sent via a message queue
(async)".  A file-based queue satisfies this: the notification is written
to the queue file and the API call returns immediately without waiting for
a consumer.  The decoupling (producer/consumer separation) is preserved.

The public function signature is unchanged: `send_completion_notification`.

---

### `requirements.txt`

| Old | New |
|-----|-----|
| `flask==3.0.0` | `flask==3.0.0` |
| `boto3==1.34.0` | *(removed)* |

`boto3` is the only removed dependency.  All replacement infrastructure
uses Python stdlib (`sqlite3`, `os`, `shutil`, `json`), so no new
third-party packages are introduced.

---

### `evidence/conftest.py` (updated, not new-system code)

To make the same 39 tests runnable against both systems, the test
harness was extended:

1. **New-system temp paths** — `DB_PATH`, `STORAGE_PATH`, `QUEUE_PATH` are
   set to a `tempfile.mkdtemp()` directory before any app module is
   imported, so P_n+1's `config.py` picks them up on load.

2. **Dual cleanup in `_clean_state`** — after each test the fixture resets
   both AWS mock state (DynamoDB items, S3 objects, SQS messages) and
   new-system state (SQLite rows, uploaded files, queue file).  For each
   system the other system's cleanup paths are no-ops.

3. **Dual-source `sqs_messages` fixture** — reads from moto SQS (populated
   by old-system) and the queue file (populated by new-system) and
   combines them.  For a given system only one source will have data.

---

## Sovereignty improvements (vs. lock-in report)

| Theme | P_n | P_n+1 |
|-------|-----|-------|
| T1 Jurisdiction | ✗ US CLOUD Act (AWS) | ✓ No external operator |
| T2 Data Localisation | ~ Config-dependent | ✓ Data stays on local disk |
| T3 Operational Autonomy | ✗ Requires AWS account | ✓ Runs anywhere with Python |
| T4 Lock-in Avoidance | ✗ boto3 in 3 modules | ✓ stdlib only |
| T5 Supply-Chain Control | ✗ Single vendor (AWS) | ✓ No vendor dependency |
| T6 Openness & Standards | ✗ Proprietary DynamoDB/SQS APIs | ✓ SQL + JSONL (open standards) |
| T7 Sustainability | ✗ Managed-service dependent | ✓ Self-hosted, no managed services |

All 7 themes satisfied in P_n+1.
