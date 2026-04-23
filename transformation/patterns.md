# Transformation Patterns — The Algebra for Migration Steps

## What This Is
These are reusable, formal patterns for migrating cloud-native dependencies
to cloud-agnostic alternatives. Each pattern describes:
- What to detect (deterministic — analyzer finds it)
- What to generate (stochastic — LLM generates replacement code)
- How to verify (deterministic — tests + analyzer confirm correctness)

This is the mix: stochastic for generation, deterministic for evaluation
and quality control.

---

## Pattern 1: Database Service Replacement

### Detect (Deterministic)
- Analyzer finds: `import boto3` in a file that calls `.resource("dynamodb")`
- Lock-in type: API-level (DynamoDB query syntax is proprietary)
- Sovereignty themes violated: Jurisdiction, Autonomy, Lock-in Avoidance

### Generate (Stochastic — LLM)
- Replace boto3 DynamoDB with SQLite (stdlib `sqlite3`)
- Create table matching the DynamoDB key schema
- Rewrite each function body but KEEP the same function signatures:
  - `create_task(task)` → INSERT
  - `get_all_tasks()` → SELECT *
  - `get_task(task_id)` → SELECT WHERE id=
  - `update_task(task_id, updates)` → UPDATE SET
  - `delete_task(task_id)` → DELETE WHERE id=
- Return dicts (not Row objects) to match original interface

### Verify (Deterministic)
- Analyzer confirms: no `boto3` import in new file
- Tests: all CRUD operations pass with same inputs/outputs
- Function signatures unchanged (same names, same parameters)

### Generalizable Rule
> When a cloud-specific NoSQL database is used, replace with SQLite.
> Keep function signatures identical. The calling code (app.py) must
> not change. SQLite is stdlib, portable, zero-config.

---

## Pattern 2: Object Storage Replacement

### Detect (Deterministic)
- Analyzer finds: `import boto3` in a file that calls `.client("s3")`
- Lock-in type: API-level (S3 put_object/list_objects_v2 are AWS-specific)
- Sovereignty themes violated: Jurisdiction, Localisation, Lock-in Avoidance

### Generate (Stochastic — LLM)
- Replace S3 with local filesystem (stdlib `os`, `shutil`)
- Map S3 concepts to filesystem:
  - Bucket → root directory
  - Key (task_id/filename) → subdirectory/file
  - put_object → os.makedirs + open().write()
  - list_objects_v2 → os.listdir
  - delete_object → os.remove
- URL format changes: `https://bucket.s3.region.amazonaws.com/key` → `/files/task_id/filename`
- KEEP same function signatures:
  - `upload_file(task_id, filename, file_data)` → returns URL
  - `list_files(task_id)` → returns list of URLs
  - `delete_files(task_id)` → removes all files for task

### Verify (Deterministic)
- Analyzer confirms: no `boto3` import in new file
- Tests: upload, list, delete operations work with same interface
- Function signatures unchanged

### Generalizable Rule
> When cloud object storage is used for file uploads, replace with
> local filesystem. Map bucket/key hierarchy to directory/file structure.
> Keep function signatures identical. Stdlib only.

---

## Pattern 3: Message Queue Replacement

### Detect (Deterministic)
- Analyzer finds: `import boto3` in a file that calls `.client("sqs")`
- Lock-in type: API-level + service-level (SQS protocol is proprietary)
- Sovereignty themes violated: Jurisdiction, Autonomy, Lock-in Avoidance, Supply-Chain Control

### Generate (Stochastic — LLM)
- Replace SQS with file-based JSONL queue (stdlib `json`, `os`)
- Map SQS concepts to file:
  - send_message → append JSON line to file
  - receive_message → read lines from file
  - Queue URL → file path
- KEEP same function signature:
  - `send_completion_notification(task)` → appends to queue file

### Verify (Deterministic)
- Analyzer confirms: no `boto3` import in new file
- Tests: notification sent on task completion, message readable
- Function signature unchanged

### Generalizable Rule
> When a cloud message queue is used for async notifications, replace
> with a JSONL file queue. One line per message, append-only.
> Keep function signatures identical. Stdlib only.
> Limitation: not concurrent-write-safe (acceptable for demo scope).

---

## Pattern 4: Configuration Decoupling

### Detect (Deterministic)
- Analyzer finds: environment variables referencing cloud-specific values
  (AWS_REGION, S3_BUCKET, SQS_QUEUE_URL, DYNAMODB_TABLE)
- Lock-in type: configuration-level

### Generate (Stochastic — LLM)
- Replace cloud-specific variable names with generic ones:
  - DYNAMODB_TABLE → DB_PATH
  - S3_BUCKET → STORAGE_PATH
  - SQS_QUEUE_URL → QUEUE_PATH
  - AWS_REGION → removed (not needed)
- Default values point to local resources, not cloud endpoints

### Verify (Deterministic)
- Analyzer confirms: no AWS/cloud-specific strings in config
- Tests: app starts and works with default config values

### Generalizable Rule
> Replace all cloud-provider-specific configuration with generic,
> infrastructure-agnostic names. Defaults should work locally
> without any cloud credentials.

---

## Meta-Pattern: The Interface Preservation Principle

All four patterns share one rule:

> **The function signatures at the boundary between app logic and
> infrastructure MUST NOT CHANGE.**

This is why app.py needed zero changes. The LLM generates new
implementations behind the same interface. The tests verify behavior
through that interface. The analyzer confirms the interface is preserved.

This is the fundamental migration pattern:
1. Detect the cloud-specific implementation (deterministic)
2. Generate a portable replacement behind the same interface (stochastic)
3. Verify the replacement satisfies the same spec (deterministic)

Stochastic for generation. Deterministic for evaluation and quality control.

---

## How to Apply These Patterns to a New Project

1. Run `python3 analyzer.py <project> --json` — get all cloud dependencies
2. For each dependency, match it to a pattern above
3. Generate the replacement using Claude Code (stochastic)
4. Run the tests (deterministic) — do they still pass?
5. Run the analyzer on the new system (deterministic) — are cloud deps gone?
6. Check sovereignty themes (deterministic) — all 7 satisfied?

If a dependency doesn't match any existing pattern, that's a NEW pattern
to document. The pattern library grows with each migration.