# Verification Report — Semantic Equivalence of P_n and P_n+1

**Date:** 2026-04-23
**Specification:** `/spec/api_spec.md` (unchanged throughout)
**Analyzer:** `python3 analyzer.py <system> --json`
**Test suite:** `evidence/` (39 spec-driven tests)

---

## 1. Structural Comparison

### File inventory

| File | P_n (old-system) | P_n+1 (new-system) | Identical? |
|------|-----------------|-------------------|-----------|
| `app.py` | 7 route functions | 7 route functions | **Yes** — byte-for-byte |
| `config.py` | 0 functions | 0 functions | No — variable names changed |
| `database.py` | 5 public functions | 5 public + 2 private helpers | No — implementation rewritten |
| `storage.py` | 3 public functions | 3 public functions | No — implementation rewritten |
| `notifications.py` | 1 function | 1 function | No — implementation rewritten |
| `requirements.txt` | flask, boto3 | flask only | No — boto3 removed |

**Total files:** 6 in both systems (equal).
**Total Python files:** 5 in both systems (equal).
**Classes:** 0 in both systems.

### Public function surface (the interface `app.py` calls)

| Module | P_n functions | P_n+1 functions | Match? |
|--------|--------------|----------------|--------|
| `database` | `create_task`, `get_all_tasks`, `get_task`, `update_task`, `delete_task` | `create_task`, `get_all_tasks`, `get_task`, `update_task`, `delete_task` | ✓ |
| `storage` | `upload_file`, `list_files`, `delete_files` | `upload_file`, `list_files`, `delete_files` | ✓ |
| `notifications` | `send_completion_notification` | `send_completion_notification` | ✓ |
| `app` (routes) | `create`, `list_all`, `get_one`, `update`, `delete`, `upload`, `files` | `create`, `list_all`, `get_one`, `update`, `delete`, `upload`, `files` | ✓ |

New-system adds two **private** helpers in `database.py` (`_connect`, `_init`) that are internal to the module and not part of the interface. These are invisible to `app.py`.

---

## 2. Cloud Dependencies Removed

The analyzer found **3 cloud dependency files** in P_n and **0** in P_n+1.

| File | P_n import | P_n+1 import | Replaced with |
|------|-----------|-------------|---------------|
| `database.py` | `boto3` (DynamoDB) | `sqlite3` | Python stdlib — built-in SQL database |
| `storage.py` | `boto3` (S3) | `os`, `shutil` | Python stdlib — local filesystem |
| `notifications.py` | `boto3` (SQS) | `os`, `json` | Python stdlib — JSONL file queue |
| `config.py` | *(none, but AWS URIs)* | *(none)* | Generic env var names + no hard-coded URIs |

**boto3 import count:** P_n = 3 files, P_n+1 = 0 files.
**Hard-coded AWS URIs:** P_n = 1 (`config.py`), P_n+1 = 0.

### What specifically changed

**`database.py`**
- `boto3.resource("dynamodb")` → `sqlite3.connect(DB_PATH)`
- DynamoDB proprietary `UpdateExpression`/`ExpressionAttributeNames` → standard SQL `UPDATE ... SET col = ?`
- All 5 function signatures preserved exactly.
- Column names in UPDATE are filtered against an explicit allowlist (`title`, `description`, `status`) to prevent SQL injection from user-supplied keys.

**`storage.py`**
- `boto3.client("s3")` → stdlib `os`/`shutil`
- `s3.put_object` → `open(path, "wb").write(data)`
- `s3.list_objects_v2` → `os.listdir`
- `s3.delete_object` (per object) → `shutil.rmtree` (per task directory)
- URL format: `https://{bucket}.s3.{region}.amazonaws.com/{key}` → `/files/{task_id}/{filename}`
  - The new URL is relative and portable; the old URL was an AWS-specific HTTPS template.

**`notifications.py`**
- `boto3.client("sqs")` → stdlib `open`
- `sqs.send_message(QueueUrl=..., MessageBody=json.dumps(...))` → `open(QUEUE_PATH, "a").write(json.dumps(msg) + "\n")`
- Message envelope (`event`, `task_id`, `title`) is identical.

**`config.py`**
- `AWS_REGION`, `DYNAMODB_TABLE`, `S3_BUCKET`, `SQS_QUEUE_URL` → `DB_PATH`, `STORAGE_PATH`, `QUEUE_PATH`
- No AWS region defaults, no hard-coded SQS endpoint URI.

---

## 3. Cloud Dependencies Remaining

**Analyzer result for P_n+1: `"cloud_dependencies": []`**

No `boto3` imports, no AWS SDK usage, no hard-coded cloud URIs detected in any file.

### Honest assessment of remaining third-party dependencies

| Dependency | Type | Concern? |
|-----------|------|---------|
| `flask` | Third-party Python web framework | Not a cloud provider; open-source (BSD); self-hostable; widely portable. Acceptable. |
| `sqlite3` | Python stdlib | No external vendor; built into CPython. No concern. |
| `os`, `shutil`, `json`, `uuid` | Python stdlib | No concern. |

**Honest caveat — file queue:** The `notifications.queue` JSONL file is a valid decoupled queue for single-process deployments but is not durable under concurrent writes (no file locking) and not observable by external consumers without reading the file. For production use, a proper message broker (RabbitMQ, Redis Streams) would be appropriate. This is a deliberate simplification within scope — the spec requires "a message queue (async)" and the file queue satisfies the observable contract tested by the evidence suite.

---

## 4. Test Results

Tests run with `python3 -m pytest evidence/ -v`.

### P_n — old-system

```
39 passed in 0.30s
```

| Category | Tests | Passed | Failed |
|----------|-------|--------|--------|
| POST /tasks | 5 | 5 | 0 |
| GET /tasks | 3 | 3 | 0 |
| GET /tasks/{id} | 3 | 3 | 0 |
| PUT /tasks/{id} | 8 | 8 | 0 |
| DELETE /tasks/{id} | 4 | 4 | 0 |
| POST /tasks/{id}/upload | 4 | 4 | 0 |
| GET /tasks/{id}/files | 4 | 4 | 0 |
| Behavior rules | 8 | 8 | 0 |
| **Total** | **39** | **39** | **0** |

### P_n+1 — new-system

```
39 passed in 0.43s
```

| Category | Tests | Passed | Failed |
|----------|-------|--------|--------|
| POST /tasks | 5 | 5 | 0 |
| GET /tasks | 3 | 3 | 0 |
| GET /tasks/{id} | 3 | 3 | 0 |
| PUT /tasks/{id} | 8 | 8 | 0 |
| DELETE /tasks/{id} | 4 | 4 | 0 |
| POST /tasks/{id}/upload | 4 | 4 | 0 |
| GET /tasks/{id}/files | 4 | 4 | 0 |
| Behavior rules | 8 | 8 | 0 |
| **Total** | **39** | **39** | **0** |

**Both systems: 39/39 (100%).**

---

## 5. Sovereignty Compliance

Checked against the 7 EU Cloud Sovereignty themes from `/spec/sovereignty_themes.md`.

### T1 — Jurisdiction

> No dependency on non-EU cloud provider APIs?

| | P_n | P_n+1 |
|--|-----|-------|
| Uses AWS (US entity, US CLOUD Act) | Yes | **No** |
| Verdict | ✗ Violated | ✓ Satisfied |

P_n+1 has no external cloud provider. All code runs under the operator's own jurisdiction.

### T2 — Data Localisation

> Data stays local / within a defined boundary?

| | P_n | P_n+1 |
|--|-----|-------|
| Data location controlled by operator | Partially (config-dependent) | **Yes — filesystem path** |
| Hard-coded foreign endpoint | Yes (SQS URL) | **No** |
| Verdict | ~ Partially satisfied | ✓ Satisfied |

P_n+1 writes all data to `DB_PATH`, `STORAGE_PATH`, and `QUEUE_PATH` — operator-controlled paths that can be set to any local or network-mounted location.

### T3 — Operational Autonomy

> Can operate independently without an external cloud account?

| | P_n | P_n+1 |
|--|-----|-------|
| Requires active AWS account + credentials | Yes | **No** |
| Can run offline / air-gapped | No | **Yes** |
| Verdict | ✗ Violated | ✓ Satisfied |

P_n+1 runs with `python3 app.py` on any machine with Python 3 and Flask installed. No network connectivity required.

### T4 — Lock-in Avoidance

> No vendor-specific APIs in application code?

| | P_n | P_n+1 |
|--|-----|-------|
| `boto3` imports | 3 files | **0 files** |
| Proprietary query language | Yes (DynamoDB UpdateExpression) | **No (standard SQL)** |
| Proprietary messaging protocol | Yes (SQS) | **No (JSONL file)** |
| Verdict | ✗ Violated | ✓ Satisfied |

### T5 — Supply-Chain Control

> No single vendor controls the infrastructure stack?

| | P_n | P_n+1 |
|--|-----|-------|
| Infrastructure vendor(s) | Amazon (DB + storage + messaging) | **None (stdlib only)** |
| Single point of vendor failure | Yes | **No** |
| Verdict | ✗ Violated | ✓ Satisfied |

P_n+1's only non-stdlib dependency is Flask, which is vendor-neutral, open-source, and replaceable.

### T6 — Openness & Standards

> Uses open, documented, standards-based protocols?

| | P_n | P_n+1 |
|--|-----|-------|
| Database interface | DynamoDB proprietary API | **SQL (ISO standard)** |
| Storage interface | S3 API (de-facto, not standard) | **POSIX filesystem** |
| Messaging interface | SQS proprietary protocol | **JSONL (open, human-readable)** |
| Verdict | ✗ Violated (DB + messaging) | ✓ Satisfied |

### T7 — Sustainability

> Portable and maintainable without a specific managed service?

| | P_n | P_n+1 |
|--|-----|-------|
| Requires managed AWS services | Yes | **No** |
| Self-hostable | No | **Yes** |
| Replaceable infrastructure layer | No | **Yes (same signatures, swap implementations)** |
| Verdict | ✗ Violated | ✓ Satisfied |

### Sovereignty summary

| Theme | P_n | P_n+1 |
|-------|:---:|:-----:|
| T1 Jurisdiction | ✗ | ✓ |
| T2 Data Localisation | ~ | ✓ |
| T3 Operational Autonomy | ✗ | ✓ |
| T4 Lock-in Avoidance | ✗ | ✓ |
| T5 Supply-Chain Control | ✗ | ✓ |
| T6 Openness & Standards | ✗ | ✓ |
| T7 Sustainability | ✗ | ✓ |
| **Score** | **0/7 (T2 partial)** | **7/7** |

---

## 6. Semantic Equivalence Verdict

**VERDICT: EQUIVALENT**

Both P_n and P_n+1 satisfy specification S_n, as demonstrated by:

1. **Same specification** — `/spec/api_spec.md` was not modified at any point. All 7 endpoints and 5 behaviour rules are unchanged.

2. **Same test suite** — `evidence/test_api.py` contains 39 tests derived exclusively from the spec, with no knowledge of implementation details. The identical test file was run against both systems without modification.

3. **Same results** — Both systems pass 39/39 tests (100%). No test passes on one system and fails on the other.

4. **Identical orchestration layer** — `app.py` is byte-for-byte identical in both systems. All route logic, status codes, error handling, and notification triggering are unchanged.

5. **Preserved public interface** — All 9 public functions called by `app.py` (`create_task`, `get_all_tasks`, `get_task`, `update_task`, `delete_task`, `upload_file`, `list_files`, `delete_files`, `send_completion_notification`) have the same names and signatures in both systems.

### What changed (infrastructure only)

| Concern | P_n | P_n+1 |
|---------|-----|-------|
| Database | DynamoDB (AWS) | SQLite (stdlib) |
| Object storage | S3 (AWS) | Local filesystem (stdlib) |
| Message queue | SQS (AWS) | JSONL file queue (stdlib) |
| Config | AWS-specific env vars + hard-coded URI | Generic env vars |
| External dependencies | `boto3` | None |

### Known limitations of P_n+1 (honest)

- **File queue** (`notifications.queue`) is not safe for concurrent multi-process writes. For a production deployment with multiple workers, a file-locking mechanism or a real broker would be required. The spec does not mandate multi-process safety, and the single-process Flask dev server satisfies the observable contract.
- **SQLite** is not suitable for high-concurrency production use. The spec does not define scale requirements; SQLite is the correct portable replacement for a single-node deployment.
- These are deployment-scale concerns, not semantic equivalence concerns. The observable API behaviour is identical.
