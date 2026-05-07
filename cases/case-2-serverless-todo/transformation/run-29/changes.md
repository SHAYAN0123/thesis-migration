# Transformation Changes — Run 29

**Source**: `cases/case-2-serverless-todo/old-system/` (P_n)
**Target**: `cases/case-2-serverless-todo/transformation/run-29/` (P_n+1)
**Spec**: `cases/case-2-serverless-todo/spec/api_spec.md` (S_n)

---

## Analyzer Result

| Metric              | P_n (old-system) | P_n+1 (run-29) |
|---------------------|------------------|----------------|
| Cloud dependencies  | 5                | 0              |
| boto3 imports       | 5                | 0              |
| Python files        | 7                | 3              |

---

## Files Produced

| File             | Role                                      |
|------------------|-------------------------------------------|
| `app.py`         | Flask HTTP routing + business logic       |
| `database.py`    | SQLite persistence layer                  |
| `config.py`      | Generic path-based configuration          |
| `requirements.txt` | Runtime dependencies (flask only)       |

---

## Changes by Sovereignty Violation

### 1. boto3 / DynamoDB removed (Pattern 1 — Database)

**Before** (`create.py`, `list.py`, `get.py`, `update.py`, `delete.py`):
```python
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
table.put_item(Item=item)
result = table.scan()              # → result['Items']
result = table.get_item(Key=...)   # → result['Item']
result = table.update_item(...)    # → result['Attributes']
table.delete_item(Key=...)
```

**After** (`database.py`):
```python
import sqlite3
conn = sqlite3.connect(DB_PATH)
conn.execute('INSERT INTO todos ...')
conn.execute('SELECT * FROM todos')
conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,))
conn.execute('UPDATE todos SET text=?, checked=?, updatedAt=? WHERE id=?', ...)
conn.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
```

All DynamoDB-specific response shapes (`result['Item']`, `result['Items']`,
`result['Attributes']`) replaced with plain Python dicts from sqlite3 rows.

### 2. Lambda handler contract replaced (compute + routing)

**Before** (five files, each with):
```python
def create(event, context):
    data = json.loads(event['body'])
    todo_id = event['pathParameters']['id']
    return {"statusCode": 200, "body": json.dumps(...)}
```

**After** (`app.py`): standard Flask routes with `request.get_json()` and
`request.view_args` (path parameters via `<string:todo_id>`). Responses use
`flask.jsonify()` with HTTP status codes directly.

### 3. DynamoDB UpdateExpression syntax eliminated

**Before** (`update.py`):
```python
ExpressionAttributeNames={'#todo_text': 'text'},
ExpressionAttributeValues={':text': ..., ':checked': ..., ':updatedAt': ...},
UpdateExpression='SET #todo_text = :text, checked = :checked, updatedAt = :updatedAt',
ReturnValues='ALL_NEW',
```

**After** (`database.py`):
```python
conn.execute('UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?', ...)
```

### 4. DecimalEncoder deleted

`decimalencoder.py` existed solely because DynamoDB returns numeric attributes
as Python `Decimal` objects. SQLite returns native Python types; no custom
JSON encoder is required.

### 5. LOCALSTACK_HOSTNAME conditional removed

All five handlers contained an AWS-emulator escape hatch that selected between
a LocalStack endpoint and the real AWS endpoint. Replaced by the single
`DB_PATH` config variable pointing to a local SQLite file.

### 6. DYNAMODB_TABLE env var replaced (Pattern 4 — Config)

**Before**: `os.environ['DYNAMODB_TABLE']` — technology-encoding name,
injected by `serverless.yml`.

**After**: `DB_PATH = os.environ.get('DB_PATH', 'todos.db')` — generic
filesystem path with a safe default.

### 7. serverless.yml not carried forward

The deployment descriptor hardcoded AWS provider, Lambda runtime, IAM roles,
API Gateway HTTP events, and a CloudFormation DynamoDB resource. It is
replaced by the standard Flask dev server (`app.run`) and a minimal
`requirements.txt`. A container-based deployment descriptor (`Dockerfile`) can
be added on top without changing application code.

---

## Behavior Preserved (S_n compliance)

| Rule | Description                                      | Verified |
|------|--------------------------------------------------|----------|
| R1   | Every todo has a unique UUID id                  | ✓        |
| R2   | checked defaults to false on create              | ✓        |
| R3   | createdAt and updatedAt recorded on create       | ✓        |
| R4   | updatedAt changes on update                      | ✓        |
| R5   | id and createdAt are immutable after update      | ✓        |
| R6   | delete is permanent; subsequent GET → 404        | ✓        |
| R7   | list returns all existing todos                  | ✓        |
| R8   | data persists between requests                   | ✓        |

**Test result**: 43/43 passed (`TEST_SYSTEM_PATH=transformation/run-29 pytest evidence/ -v`)
