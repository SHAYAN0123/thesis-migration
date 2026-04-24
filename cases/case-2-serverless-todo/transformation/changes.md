# Transformation Changes Report — Case 2: Serverless Todo

**From**: `cases/case-2-serverless-todo/old-system` (P_n) — AWS Lambda + DynamoDB
**To**:   `cases/case-2-serverless-todo/new-system` (P_n+1) — Flask + SQLite
**Spec**:  `cases/case-2-serverless-todo/spec/api_spec.md` (S_n, unchanged)
**Date**: 2026-04-24

---

## Semantic Equivalence Result

| System       | Tests | Passed | Failed |
|--------------|-------|--------|--------|
| P_n  (old)   | 43    | 43     | 0      |
| P_n+1 (new)  | 43    | 43     | 0      |

Both systems pass the identical 43 spec-driven tests derived from S_n.
This is the proof of semantic equivalence.

---

## Analyzer Metrics

| Metric         | P_n (old-system) | P_n+1 (new-system) |
|----------------|------------------|--------------------|
| Total files    | 8                | 4                  |
| Python files   | 7                | 3                  |
| Functions      | 5                | 14                 |
| Classes        | 1                | 0                  |
| Imports        | 24               | 7                  |
| Cloud deps     | **5**            | **0**              |

Cloud dependencies reduced from 5 to 0.

---

## File-by-File Changes

### Removed (P_n only)

| File                    | Reason removed                                                   |
|-------------------------|------------------------------------------------------------------|
| `todos/create.py`       | Lambda handler replaced by Flask route in `app.py`              |
| `todos/list.py`         | Lambda handler replaced by Flask route in `app.py`              |
| `todos/get.py`          | Lambda handler replaced by Flask route in `app.py`              |
| `todos/update.py`       | Lambda handler replaced by Flask route in `app.py`              |
| `todos/delete.py`       | Lambda handler replaced by Flask route in `app.py`              |
| `todos/__init__.py`     | Package marker for Lambda handler layout; not needed in Flask    |
| `todos/decimalencoder.py` | DynamoDB-specific workaround; SQLite returns native Python types |
| `serverless.yml`        | AWS deployment descriptor; replaced by portable `requirements.txt` |

### Added (P_n+1 only)

| File              | Purpose                                                          |
|-------------------|------------------------------------------------------------------|
| `app.py`          | Flask application; five HTTP routes matching spec endpoints      |
| `database.py`     | SQLite repository; all CRUD operations isolated from HTTP layer  |
| `config.py`       | Single source for `DB_PATH` environment variable                 |
| `requirements.txt` | Declares `flask>=3.0.0`; no cloud SDK dependencies             |

---

## Lock-In Point Resolution

Each of the 10 sovereignty violations catalogued in the lock-in report is addressed below.

### 1. boto3 / AWS SDK

**Old**: Every handler imports `boto3` and calls `boto3.resource('dynamodb')` at module scope.

**New**: `boto3` is not imported anywhere. `database.py` uses Python's standard-library `sqlite3` module exclusively.

```python
# Old — create.py
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
table.put_item(Item=item)

# New — database.py
import sqlite3
with _connect() as conn:
    conn.execute("INSERT INTO todos (...) VALUES (?, ?, ?, ?, ?)", (...))
```

### 2. Lambda Handler Contract `(event, context)`

**Old**: All five functions carry the AWS Lambda / API Gateway Proxy signature. Request data is extracted from `event['body']` and `event['pathParameters']['id']`.

**New**: Standard Flask view functions. Request data comes from `request.get_json()` and `<todo_id>` path parameters registered in the route decorator.

```python
# Old — get.py
def get(event, context):
    result = table.get_item(Key={'id': event['pathParameters']['id']})

# New — app.py
@app.route("/todos/<todo_id>", methods=["GET"])
def get_one(todo_id):
    todo = database.get_todo(todo_id)
```

### 3. DynamoDB Response Shape (`result['Item']`, `result['Items']`, `result['Attributes']`)

**Old**: Each handler unpacks DynamoDB SDK response keys directly in business logic:
- `result['Item']` (get_item)
- `result['Items']` (scan)
- `result['Attributes']` with `ReturnValues='ALL_NEW'` (update_item)

**New**: `database.py` functions return plain Python dicts. The HTTP layer never touches storage response shapes.

### 4. DynamoDB UpdateExpression Syntax

**Old**: `update.py` embeds DynamoDB's proprietary expression language — `UpdateExpression`, `ExpressionAttributeNames` (required because `text` is a reserved word in DynamoDB), and `ExpressionAttributeValues`.

**New**: Standard SQL `UPDATE` statement.

```python
# Old — update.py
table.update_item(
    Key={'id': event['pathParameters']['id']},
    ExpressionAttributeNames={'#todo_text': 'text'},
    ExpressionAttributeValues={':text': data['text'], ':checked': data['checked'], ':updatedAt': timestamp},
    UpdateExpression='SET #todo_text = :text, checked = :checked, updatedAt = :updatedAt',
    ReturnValues='ALL_NEW',
)

# New — database.py
conn.execute(
    "UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?",
    (text, int(checked), now, todo_id),
)
```

### 5. DecimalEncoder (DynamoDB Decimal type)

**Old**: `decimalencoder.py` exists solely because DynamoDB returns numeric attributes as Python `Decimal` objects, which are not JSON-serialisable by default.

**New**: SQLite returns native Python `int` and `str` types. No custom JSON encoder is needed. The class and its import are gone.

### 6. Inconsistent Timestamp Formats

**Old**: A latent bug in the old-system — `create.py` stores `updatedAt` as `str(time.time())` (a float string), while `update.py` stores `updatedAt` as `int(time.time() * 1000)` (a millisecond integer). The types differ between create and update.

**New**: All timestamps use `datetime.now(timezone.utc).isoformat()` — a consistent ISO 8601 string for both create and update. The spec requires timestamps to exist and change; it does not constrain the format.

### 7. `serverless.yml` — AWS Infrastructure-as-Code

**Old**: `serverless.yml` declares the entire AWS stack: provider name (`aws`), Lambda runtime, IAM role with DynamoDB ARN, API Gateway HTTP event triggers, and a CloudFormation `AWS::DynamoDB::Table` resource. The `serverless-localstack` plugin is also declared for local development.

**New**: No deployment descriptor. The application is a standard WSGI app runnable with `flask run` or any WSGI server. Deployment is infrastructure-agnostic.

### 8. AWS IAM Role with DynamoDB ARN

**Old**: `serverless.yml` includes:
```yaml
iamRoleStatements:
  - Effect: Allow
    Action: [dynamodb:Query, dynamodb:Scan, ...]
    Resource: "arn:aws:dynamodb:${opt:region}:*:table/..."
```

**New**: No IAM policies, no ARNs, no AWS-specific permission model. File system access is the only permission required.

### 9. `LOCALSTACK_HOSTNAME` Conditional

**Old**: All five handler files contain an `if 'LOCALSTACK_HOSTNAME' in os.environ` block that conditionally sets a LocalStack endpoint. This is an AWS emulator dev escape hatch, not an abstraction — both branches still use boto3.

**New**: Removed entirely. The only environment variable is `DB_PATH`, which points to the SQLite file. Same variable works in all environments: dev, test, and production.

### 10. `DYNAMODB_TABLE` Environment Variable

**Old**: All five handlers read `os.environ['DYNAMODB_TABLE']` to resolve the DynamoDB table name. The variable name encodes the storage technology.

**New**: `config.py` reads `os.environ.get("DB_PATH", "todos.db")` — a technology-neutral path variable. No AWS naming convention is preserved.

---

## Abstraction Layer: Before and After

### P_n — No Abstraction

```
create.py      ← validation + UUID + timestamp + boto3 put_item + response dict
list.py        ← boto3 scan + DecimalEncoder + response dict
get.py         ← boto3 get_item + result['Item'] + response dict
update.py      ← validation + timestamp + boto3 UpdateExpression + result['Attributes'] + response dict
delete.py      ← boto3 delete_item + response dict
```

Every concern (HTTP, business logic, persistence) is mixed in a single function per operation.

### P_n+1 — Two Clean Layers

```
app.py         ← HTTP only: parse request, call database, return jsonify()
database.py    ← persistence only: SQL, connection management, type conversion
config.py      ← configuration: DB_PATH
```

The Flask layer has no knowledge of SQL. The database layer has no knowledge of HTTP. Either can be swapped independently.

---

## What Was NOT Changed

The following are identical in P_n and P_n+1, as required by S_n:

| Aspect                     | Value                                              |
|----------------------------|----------------------------------------------------|
| API surface                | POST /todos, GET /todos, GET /todos/{id}, PUT /todos/{id}, DELETE /todos/{id} |
| Todo data model fields     | id, text, checked, createdAt, updatedAt            |
| Default `checked` value    | `false`                                            |
| UUID format for `id`       | Valid UUID (v1 → v4; both pass `uuid.UUID()`)      |
| Immutable fields on update | `id` and `createdAt` never change                  |
| Timestamp update on PUT    | `updatedAt` always changes                         |
| Permanent delete           | Subsequent GET returns 404                         |
| Persistence                | Data survives across requests                      |
| HTTP status codes          | POST→200, GET→200, PUT→200, DELETE→200, missing→404 |
