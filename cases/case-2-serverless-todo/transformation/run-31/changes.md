# Transformation Changes — Run 31

**Source**: `cases/case-2-serverless-todo/old-system/` (P_n)
**Target**: `cases/case-2-serverless-todo/transformation/run-31/` (P_n+1)
**Spec**: `cases/case-2-serverless-todo/spec/api_spec.md` (S_n)

---

## Files Created

| File | Status | Description |
|------|--------|-------------|
| `app.py` | New | Flask WSGI application replacing Lambda handler contract |
| `database.py` | New | SQLite persistence layer replacing boto3 + DynamoDB |
| `config.py` | New | Generic path config replacing `DYNAMODB_TABLE` env var |
| `requirements.txt` | New | flask only; boto3 removed |

## Files Removed (not carried forward)

| File | Reason |
|------|--------|
| `create.py` | Lambda handler merged into Flask route in `app.py` |
| `list.py` | Lambda handler merged into Flask route in `app.py` |
| `get.py` | Lambda handler merged into Flask route in `app.py` |
| `update.py` | Lambda handler merged into Flask route in `app.py` |
| `delete.py` | Lambda handler merged into Flask route in `app.py` |
| `decimalencoder.py` | DynamoDB-specific Decimal workaround; not needed with SQLite |
| `serverless.yml` | AWS IaC replaced by standard WSGI process |

---

## Changes by Lock-In Violation

### 1. boto3 / DynamoDB → SQLite (Pattern 1: Database)

All five handlers called `boto3.resource('dynamodb')` at module scope and used
DynamoDB-specific APIs (`put_item`, `scan`, `get_item`, `update_item`,
`delete_item`). These are replaced by standard `sqlite3` calls in `database.py`.

- `Table.put_item(Item=...)` → `INSERT INTO todos ...`
- `Table.scan()` → `SELECT * FROM todos`
- `Table.get_item(Key={'id': ...})` → `SELECT * FROM todos WHERE id = ?`
- `Table.update_item(... UpdateExpression ...)` → `UPDATE todos SET ... WHERE id = ?`
- `Table.delete_item(Key={'id': ...})` → `DELETE FROM todos WHERE id = ?`

DynamoDB response key unpacking (`result['Item']`, `result['Items']`,
`result['Attributes']`) is eliminated; `sqlite3` returns plain `Row` objects
converted to dicts via `_to_dict()`.

### 2. Lambda handler contract → Flask routes (Pattern 4: Compute)

Old signature: `def <op>(event, context)` with AWS API Gateway Proxy event shape.

- `event['body']` (raw JSON string) → `request.get_json()`
- `event['pathParameters']['id']` → Flask `<todo_id>` route variable

New signature: standard Flask view functions with no AWS-specific contract.

### 3. DynamoDB UpdateExpression syntax eliminated

`update.py` used `ExpressionAttributeNames={'#todo_text': 'text'}` as a
DynamoDB reserved-word workaround and `ReturnValues='ALL_NEW'` to get the
updated row back. Replaced with a plain SQL `UPDATE` followed by a `SELECT`
to fetch the updated row — no proprietary query language required.

### 4. DecimalEncoder eliminated

`DecimalEncoder` existed solely because DynamoDB returns numerics as Python
`Decimal` objects. SQLite returns native Python `int`/`str`, so no custom
JSON encoder is needed.

### 5. LOCALSTACK_HOSTNAME escape hatch eliminated

All five handlers had a conditional `if 'LOCALSTACK_HOSTNAME' in os.environ`
block pointing to an AWS emulator. Removed entirely; the new system has no
AWS dependency in either branch.

### 6. Config: DYNAMODB_TABLE → DB_PATH (Pattern 4: Config)

`os.environ['DYNAMODB_TABLE']` encoded the storage technology in the variable
name. Replaced with `DB_PATH` (defaulting to `"todos.db"`) in `config.py`.

### 7. serverless.yml → standard WSGI process

The AWS CloudFormation / Serverless Framework deployment descriptor is not
carried forward. The Flask app can be run with `python app.py` or any
WSGI server (gunicorn, waitress) and deployed as a container or process.

---

## Behavior Preservation

All eight behavior rules from `spec/api_spec.md` are preserved:

1. UUIDs generated with `uuid.uuid4()` — unique per call.
2. `checked` defaults to `False` on create.
3. `createdAt` and `updatedAt` set to UTC ISO-8601 timestamp on create.
4. `updatedAt` refreshed on every `update_todo()` call.
5. `id` and `createdAt` are never modified by `update_todo()`.
6. `DELETE` issues `DELETE FROM todos WHERE id = ?` — permanent removal.
7. `list_todos()` issues `SELECT * FROM todos` — returns all rows.
8. SQLite file persistence satisfies the between-requests durability rule.
