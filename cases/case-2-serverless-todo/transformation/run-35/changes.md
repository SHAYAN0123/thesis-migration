# Transformation Changes — Run 35

## Summary

Migrated `cases/case-2-serverless-todo/old-system` (P_n, AWS Lambda + DynamoDB)
to a cloud-agnostic Flask + SQLite application (P_n+1).

---

## Changes by File

### NEW: app.py

Replaces all five Lambda handler files (`create.py`, `list.py`, `get.py`,
`update.py`, `delete.py`) with a single Flask application.

| Old (P_n) | New (P_n+1) |
|-----------|-------------|
| `def create(event, context)` — Lambda handler | `@app.route('/todos', methods=['POST'])` Flask route |
| `def list(event, context)` — Lambda handler | `@app.route('/todos', methods=['GET'])` Flask route |
| `def get(event, context)` — Lambda handler | `@app.route('/todos/<string:todo_id>', methods=['GET'])` Flask route |
| `def update(event, context)` — Lambda handler | `@app.route('/todos/<string:todo_id>', methods=['PUT'])` Flask route |
| `def delete(event, context)` — Lambda handler | `@app.route('/todos/<string:todo_id>', methods=['DELETE'])` Flask route |
| `event['body']` / `json.loads(...)` | `request.get_json(silent=True)` |
| `event['pathParameters']['id']` | `todo_id` Flask path parameter |
| `{"statusCode": 200, "body": json.dumps(...)}` dict | `jsonify(...)`, status code tuple |

### NEW: database.py

Replaces inline boto3/DynamoDB calls in every handler with a SQLite-backed
repository module.

| Old (P_n) | New (P_n+1) |
|-----------|-------------|
| `boto3.resource('dynamodb')` | `sqlite3.connect(DB_PATH)` |
| `table.put_item(Item=item)` | `INSERT INTO todos ...` |
| `table.scan()` → `result['Items']` | `SELECT * FROM todos` |
| `table.get_item(Key={'id': ...})` → `result['Item']` | `SELECT * FROM todos WHERE id = ?` |
| `table.update_item(ExpressionAttributeNames, UpdateExpression, ...)` | `UPDATE todos SET text=?, checked=?, updatedAt=? WHERE id=?` |
| `table.delete_item(Key={'id': ...})` | `DELETE FROM todos WHERE id = ?` |
| DynamoDB `Decimal` type → `DecimalEncoder` workaround | Plain Python `int`/`bool` — no encoder needed |
| `LOCALSTACK_HOSTNAME` conditional branch | Removed entirely |

### NEW: config.py

Replaces the AWS-specific `DYNAMODB_TABLE` environment variable with a
generic `DB_PATH` variable pointing to the SQLite file.

| Old (P_n) | New (P_n+1) |
|-----------|-------------|
| `os.environ['DYNAMODB_TABLE']` | `os.environ.get('DB_PATH', 'todos.db')` |

### NEW: requirements.txt

Removes `boto3`; retains only `flask` plus Python stdlib.

| Old (P_n) | New (P_n+1) |
|-----------|-------------|
| `boto3` | removed |
| (no framework) | `flask>=2.0.0` |

### REMOVED: decimalencoder.py

No longer needed — SQLite returns standard Python numeric types.

### REMOVED: serverless.yml

Replaced by running `python app.py` or any WSGI host. No AWS-specific
deployment descriptor is required.

---

## Sovereignty Violations Resolved

| # | Violation (P_n) | Resolution (P_n+1) |
|---|-----------------|-------------------|
| 1 | Direct `boto3` import in every handler | `boto3` removed from all files |
| 2 | Lambda handler signature `(event, context)` | Flask route functions with no AWS arguments |
| 3 | `event['pathParameters']['id']` (API Gateway shape) | `todo_id` Flask path parameter |
| 4 | `result['Item']`, `result['Items']`, `result['Attributes']` | Plain Python dicts from SQLite |
| 5 | `UpdateExpression` / `ExpressionAttributeNames` | Standard SQL `UPDATE` statement |
| 6 | `DecimalEncoder` (DynamoDB `Decimal` artefact) | Removed; SQLite returns native types |
| 7 | CloudFormation DynamoDB table in `serverless.yml` | Replaced by `init_db()` SQLite schema |
| 8 | AWS IAM role with DynamoDB ARN | Removed; no IAM required |
| 9 | `LOCALSTACK_HOSTNAME` conditional (boto3 in both branches) | Removed entirely |
| 10 | `DYNAMODB_TABLE` env var convention | Replaced by generic `DB_PATH` |

---

## Behavior Preserved

All rules from `spec/api_spec.md` are satisfied:

1. Every created todo has a unique UUID (`uuid.uuid1()`).
2. `checked` defaults to `False` on creation.
3. `createdAt` and `updatedAt` are set on creation.
4. `updatedAt` is refreshed on every update; `id` and `createdAt` are not touched.
5. DELETE removes the row permanently; subsequent GET returns 404.
6. LIST returns all rows via `SELECT * FROM todos`.
7. Data persists between requests via the SQLite file on disk.
