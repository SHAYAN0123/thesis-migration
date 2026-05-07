# Transformation: P_n → P_n+1

Cloud-specific (AWS Lambda + DynamoDB) → Cloud-agnostic (Flask + SQLite)

---

## Files removed

| File | Reason |
|---|---|
| `create.py` | Lambda handler replaced by Flask route in `app.py` |
| `list.py` | Lambda handler replaced by Flask route in `app.py` |
| `get.py` | Lambda handler replaced by Flask route in `app.py` |
| `update.py` | Lambda handler replaced by Flask route in `app.py` |
| `delete.py` | Lambda handler replaced by Flask route in `app.py` |
| `decimalencoder.py` | DynamoDB-specific workaround; SQLite returns native Python types |
| `__init__.py` | Packaging artefact for Lambda module layout; not required |
| `serverless.yml` | AWS-specific IaC; replaced by standard Python execution |

---

## Files created

| File | Purpose |
|---|---|
| `app.py` | Flask HTTP application — routes map 1-to-1 with old Lambda functions |
| `database.py` | SQLite persistence layer — stdlib only, no vendor SDK |
| `config.py` | Environment-variable configuration; generic names (`DB_PATH`) |
| `requirements.txt` | Declares `Flask>=3.0.0`; no cloud-vendor packages |

---

## Sovereignty violations resolved

| # | Old pattern | New pattern |
|---|---|---|
| 1 | `import boto3` | Removed — no vendor SDK |
| 2 | `boto3.resource('dynamodb')` | `sqlite3.connect(DB_PATH)` — stdlib |
| 3 | `LOCALSTACK_HOSTNAME` conditional for local dev | Not needed; SQLite runs locally without emulation |
| 4 | `dynamodb.Table(os.environ['DYNAMODB_TABLE'])` | `DB_PATH` env var points to a plain file |
| 5 | `table.put_item(Item=item)` | `INSERT INTO todos …` parameterized SQL |
| 6 | `table.scan()` | `SELECT * FROM todos` |
| 7 | `table.get_item(Key={'id': …})` | `SELECT * FROM todos WHERE id = ?` |
| 8 | DynamoDB `UpdateExpression` with `ExpressionAttributeNames` (`#todo_text`) | `UPDATE todos SET text = ?, …` — standard SQL, no reserved-word workarounds |
| 9 | `result['Item']` / `result['Items']` / `result['Attributes']` response shapes | Plain Python dicts from `database.py` |
| 10 | `DecimalEncoder` — DynamoDB returns `Decimal` for numbers | Removed; SQLite returns native `int`/`float` |
| 11 | Lambda handler signature `(event, context)` | Standard Flask route functions |
| 12 | `event['body']` / `event['pathParameters']` | `request.get_json()` / route parameter `<todo_id>` |
| 13 | `serverless.yml` with `provider: aws` | Removed; app is a plain WSGI process |
| 14 | `arn:aws:dynamodb:…` IAM resource ARN | Removed; no cloud IAM required |

---

## Design decisions

**SQLite as the default store** — zero-dependency, file-based, works identically on any OS or cloud VM. Swap `database.py` for a PostgreSQL or MySQL implementation without touching `app.py`.

**Repository pattern** — `app.py` imports only `database`; `database.py` imports only `config` and stdlib. No bidirectional coupling.

**ISO 8601 UTC timestamps** — `datetime.now(timezone.utc).isoformat()` replaces `str(time.time())` (UNIX float string). Spec-compliant and readable without a secondary conversion step.

**`uuid.uuid4()`** — replaces `uuid.uuid1()` (which encodes the host MAC address, a mild privacy leak).

**404 on missing item** — `get` and `update` return HTTP 404 when the item does not exist, replacing the implicit `KeyError` that would have propagated as an unhandled exception in the Lambda handlers.
