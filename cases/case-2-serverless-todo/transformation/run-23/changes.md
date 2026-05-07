# Migration Changes — run-23

**Source**: `old-system/` (AWS Lambda + DynamoDB)
**Target**: `run-23/` (Flask + SQLite)
**Spec**: `spec/api_spec.md`

## Files Produced

| File | Role |
|------|------|
| `app.py` | Flask WSGI app — defines all five REST routes |
| `database.py` | SQLite persistence layer — CRUD operations |
| `config.py` | Configuration — reads `DB_PATH` from environment |
| `requirements.txt` | Dependencies — `flask>=3.0.0` only |

## Cloud Dependencies Eliminated

| # | Old (P_n) | New (P_n+1) |
|---|-----------|-------------|
| 1 | `boto3` + DynamoDB in every handler | `sqlite3` stdlib in `database.py` |
| 2 | Lambda handler signature `(event, context)` | Flask route functions with `request` context |
| 3 | API Gateway event shape (`event['body']`, `event['pathParameters']`) | `request.get_json()`, `<todo_id>` path param |
| 4 | DynamoDB response keys (`result['Item']`, `result['Items']`, `result['Attributes']`) | Plain Python dicts |
| 5 | DynamoDB `UpdateExpression` / `ExpressionAttributeNames` syntax | Standard SQL `UPDATE` statement |
| 6 | `DecimalEncoder` (DynamoDB returns `Decimal` objects) | Not needed — SQLite returns native Python types |
| 7 | `serverless.yml` (CloudFormation, IAM, API Gateway) | Not present — standard WSGI deployment |
| 8 | `LOCALSTACK_HOSTNAME` escape hatch | Not present |
| 9 | `DYNAMODB_TABLE` environment variable | `DB_PATH` environment variable (generic path) |

## Transformation Decisions

**Database**: Each handler file had identical boto3 initialisation boilerplate. All DynamoDB calls are replaced by a single `database.py` module using `sqlite3` (stdlib). The table is created on first import via `_init()`.

**Routing**: The five Lambda handlers (`create`, `list`, `get`, `update`, `delete`) become five Flask route functions in `app.py`. Request parsing moves from `json.loads(event['body'])` and `event['pathParameters']['id']` to Flask's `request.get_json()` and URL converter `<todo_id>`.

**Data types**: `checked` is stored as `INTEGER` (0/1) in SQLite and converted to `bool` in `_to_dict()`, matching the spec's boolean type. Timestamps use UTC ISO-8601 strings.

**404 handling**: `get.py` raised `KeyError` when `result['Item']` was absent; replaced with an explicit `None` check returning HTTP 404.

**UUID**: `uuid.uuid4()` (random) replaces `uuid.uuid1()` (time-based MAC address) — both satisfy the spec's "unique UUID" requirement.

**No abstraction drift**: `serverless.yml` and `decimalencoder.py` are not ported — they were AWS-specific artefacts with no equivalent in the cloud-agnostic stack.
