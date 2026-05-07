# Transformation Changes — Run 38

**Source**: `cases/case-2-serverless-todo/old-system/` (P_n)
**Target**: `cases/case-2-serverless-todo/transformation/run-38/` (P_n+1)
**Spec**: `cases/case-2-serverless-todo/spec/api_spec.md` (S_n)

---

## Overview

The old system is a serverless AWS Lambda application with five handler files
(`create.py`, `list.py`, `get.py`, `update.py`, `delete.py`) that each embed
boto3/DynamoDB calls directly alongside business logic. There is no abstraction
layer. The new system replaces all AWS dependencies with a Flask HTTP app backed
by SQLite, satisfying the same S_n specification.

---

## Changes Applied

### 1. Compute: Lambda handler contract → Flask routes (app.py — new file)

**Old**: Five separate Lambda handler functions with signature `def op(event, context)`,
parsing `event['body']` and `event['pathParameters']['id']` (AWS API Gateway
Proxy event shape).

**New**: A single `app.py` Flask application with five routes:
- `POST /todos` — `create()`
- `GET /todos` — `list_all()`
- `GET /todos/<todo_id>` — `get_one(todo_id)`
- `PUT /todos/<todo_id>` — `update(todo_id)`
- `DELETE /todos/<todo_id>` — `delete(todo_id)`

Flask parses `request.get_json()` and route parameters — no AWS-specific event
shapes involved.

### 2. Database: boto3 / DynamoDB → sqlite3 (database.py — new file)

**Old** (repeated in all five handlers):
```python
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
table.put_item(Item=...)
table.scan()
table.get_item(Key={'id': ...})
table.update_item(Key, ExpressionAttributeNames, ExpressionAttributeValues,
                  UpdateExpression, ReturnValues='ALL_NEW')
table.delete_item(Key={'id': ...})
```

**New**: `database.py` using stdlib `sqlite3`:
- `create_todo(text)` → `INSERT INTO todos`
- `list_todos()` → `SELECT * FROM todos`
- `get_todo(todo_id)` → `SELECT * FROM todos WHERE id = ?`
- `update_todo(todo_id, text, checked)` → `UPDATE todos SET ... WHERE id = ?`
- `delete_todo(todo_id)` → `DELETE FROM todos WHERE id = ?`

The table is created on first import via `CREATE TABLE IF NOT EXISTS`. Results
are returned as plain Python dicts — no DynamoDB response key unpacking
(`result['Item']`, `result['Items']`, `result['Attributes']`).

### 3. DynamoDB UpdateExpression syntax eliminated (update handler)

**Old**: Required proprietary DynamoDB expression syntax to work around the
reserved word `text`:
```python
ExpressionAttributeNames={'#todo_text': 'text'},
ExpressionAttributeValues={':text': ..., ':checked': ..., ':updatedAt': ...},
UpdateExpression='SET #todo_text = :text, checked = :checked, updatedAt = :updatedAt',
ReturnValues='ALL_NEW',
```

**New**: Standard SQL — `UPDATE todos SET text = ?, checked = ?, updatedAt = ?
WHERE id = ?` with parameterised placeholders. No reserved-word workarounds needed.

### 4. DynamoDB response key unpacking eliminated

**Old**: `result['Item']` (get), `result['Items']` (list), `result['Attributes']`
(update) — DynamoDB SDK conventions.

**New**: Functions return plain `dict` values directly; `_to_dict(row)` converts
`sqlite3.Row` objects to dicts with correct Python types.

### 5. DecimalEncoder eliminated (decimalencoder.py — not present in new system)

**Old**: `DecimalEncoder` existed solely because DynamoDB returns numeric
attributes as Python `Decimal` objects, which are not JSON-serialisable.

**New**: SQLite returns integers and strings natively; Flask's `jsonify` handles
serialisation without a custom encoder.

### 6. Config: cloud-specific env var → generic path (config.py — new file)

**Old**: `os.environ['DYNAMODB_TABLE']` — variable name encodes the storage
technology; value injected by `serverless.yml` as `${self:service}-${opt:stage}`.

**New**: `config.py` reads `DB_PATH` from environment (defaulting to `todos.db`).
Variable name is storage-technology-agnostic and human-readable.

### 7. LOCALSTACK_HOSTNAME escape hatch eliminated (all handlers)

**Old**: Every handler contained:
```python
if 'LOCALSTACK_HOSTNAME' in os.environ:
    dynamodb_endpoint = 'http://%s:4566' % os.environ['LOCALSTACK_HOSTNAME']
    dynamodb = boto3.resource('dynamodb', endpoint_url=dynamodb_endpoint)
else:
    dynamodb = boto3.resource('dynamodb')
```

**New**: No AWS emulator needed. SQLite works locally without any special
environment configuration.

### 8. serverless.yml — not migrated (infrastructure descriptor replaced)

**Old**: `serverless.yml` hardcoded AWS provider, Lambda runtime, IAM roles
with DynamoDB ARNs, API Gateway HTTP events, and a CloudFormation DynamoDB table
resource.

**New**: No deployment descriptor in this run. The Flask app can be run directly
(`python app.py`) or containerised with a standard `Dockerfile`. No
AWS-specific infrastructure descriptor is required.

### 9. requirements.txt — boto3 removed

**Old**: Implicitly required `boto3` (AWS SDK), `moto` for testing, and
`serverless-python-requirements` plugin.

**New**: `flask>=3.0.0` only. All persistence uses stdlib `sqlite3`; no
third-party database drivers needed.

---

## File Inventory

| File             | Status      | Description                                      |
|------------------|-------------|--------------------------------------------------|
| `app.py`         | New         | Flask routes replacing Lambda handlers           |
| `database.py`    | New         | SQLite repository replacing boto3/DynamoDB calls |
| `config.py`      | New         | Generic `DB_PATH` replacing `DYNAMODB_TABLE`     |
| `requirements.txt` | New       | `flask>=3.0.0` only — boto3 removed              |
| `serverless.yml` | Not ported  | AWS-specific IaC; replaced by direct Flask run   |
| `decimalencoder.py` | Not ported | DynamoDB-specific; no longer needed             |

---

## Sovereignty Violations Resolved

| # | Violation (from lock-in report)                               | Resolution                                      |
|---|---------------------------------------------------------------|-------------------------------------------------|
| 1 | Direct boto3 import and use in all handlers                   | Replaced with sqlite3 in database.py            |
| 2 | AWS Lambda handler signature `(event, context)`               | Replaced with Flask route functions             |
| 3 | API Gateway event shape `event['pathParameters']`             | Replaced with Flask `<todo_id>` path params     |
| 4 | DynamoDB response keys `['Item']`, `['Items']`, `['Attributes']` | Replaced with plain dict returns             |
| 5 | DynamoDB UpdateExpression / ExpressionAttributeNames          | Replaced with standard SQL UPDATE               |
| 6 | DecimalEncoder (DynamoDB Decimal type)                        | Eliminated — not needed with SQLite             |
| 7 | CloudFormation DynamoDB table definition                      | Eliminated — table created via CREATE TABLE IF NOT EXISTS |
| 8 | AWS IAM role with DynamoDB ARN                                | Eliminated — no cloud permissions model needed  |
| 9 | LOCALSTACK_HOSTNAME conditional (boto3 in both branches)      | Eliminated — no AWS emulator needed             |
| 10 | `DYNAMODB_TABLE` env var convention                           | Replaced with generic `DB_PATH`                 |

---

## Behavioral Equivalence

All behavior rules from S_n are preserved:

1. Every created todo has a unique UUID (`uuid.uuid4()`) as its `id`.
2. Every created todo has `checked = False` by default.
3. Every created todo records `createdAt` and `updatedAt` (ISO 8601 UTC).
4. Updating a todo changes `updatedAt` to a new `datetime.now()` value.
5. Updating a todo does NOT change `id` or `createdAt` (SQL UPDATE touches only the specified columns).
6. Deleting a todo removes it permanently — subsequent GET returns 404.
7. Listing todos returns all existing todos via `SELECT * FROM todos`.
8. Data persists between requests — SQLite writes to disk (`DB_PATH`).
