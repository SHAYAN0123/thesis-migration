# Migration Changes — Run 37

**From**: P_n (AWS Lambda + DynamoDB serverless)  
**To**: P_n+1 (Flask + SQLite, cloud-agnostic)  
**Analyzer result**: 0 cloud dependencies (was 5)  
**Test result**: 43/43 pass on both P_n and P_n+1

---

## Files Removed (old-system)

| File | Reason |
|------|--------|
| `create.py` | Lambda handler replaced by Flask route in `app.py` |
| `list.py` | Lambda handler replaced by Flask route in `app.py` |
| `get.py` | Lambda handler replaced by Flask route in `app.py` |
| `update.py` | Lambda handler replaced by Flask route in `app.py` |
| `delete.py` | Lambda handler replaced by Flask route in `app.py` |
| `decimalencoder.py` | DynamoDB-specific Decimal workaround; not needed with SQLite |
| `serverless.yml` | AWS-specific IaC (Lambda, API Gateway, DynamoDB, IAM, CloudFormation) |

## Files Created (new-system)

| File | Role |
|------|------|
| `app.py` | Flask application with 5 routes; single entry point |
| `database.py` | SQLite persistence layer; abstracts all storage operations |
| `config.py` | Generic configuration; reads `DB_PATH` from environment |
| `requirements.txt` | Declares only `flask>=2.0.0`; no cloud SDKs |

---

## Change-by-Change Detail

### 1. boto3 / DynamoDB → sqlite3 (Pattern 1: Database)

Every handler directly called `boto3.resource('dynamodb')` and used DynamoDB's
Table API. All five handlers are replaced by a single `database.py` module that
uses stdlib `sqlite3` with a plain `todos` table.

Old (repeated in all 5 files):
```python
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
table.put_item(Item=item)
```

New (`database.py`):
```python
import sqlite3
conn = sqlite3.connect(config.DB_PATH)
conn.execute("INSERT INTO todos (...) VALUES (?,...)", (...))
```

### 2. Lambda handler contract → Flask routes

Old signature dictated by API Gateway Proxy integration:
```python
def create(event, context):
    data = json.loads(event['body'])
    todo_id = event['pathParameters']['id']
```

New standard HTTP handler via Flask:
```python
@app.route('/todos', methods=['POST'])
def create():
    data = request.get_json()

@app.route('/todos/<todo_id>', methods=['GET'])
def get_todo(todo_id):
```

### 3. DynamoDB response key unpacking → plain dicts

Old code depended on DynamoDB SDK response shapes:
```python
result['Item']        # get_item response
result['Items']       # scan response
result['Attributes']  # update_item with ReturnValues='ALL_NEW'
```

New code returns plain Python dicts directly from `database.py` functions
(`get_todo`, `list_todos`, `update_todo`). No SDK wrapper shapes involved.

### 4. DynamoDB UpdateExpression → standard SQL UPDATE

Old proprietary update language (with reserved-word workaround for `text`):
```python
ExpressionAttributeNames={'#todo_text': 'text'},
ExpressionAttributeValues={':text': ..., ':checked': ..., ':updatedAt': ...},
UpdateExpression='SET #todo_text = :text, checked = :checked, updatedAt = :updatedAt',
ReturnValues='ALL_NEW',
```

New standard SQL:
```sql
UPDATE todos SET text = ?, checked = ?, updatedAt = ? WHERE id = ?
```

### 5. DecimalEncoder removed

`decimalencoder.py` existed only because DynamoDB returns numeric types as
Python `Decimal`, which `json.dumps` cannot serialise. SQLite returns native
Python `int`/`float`/`str`, so no custom encoder is needed. `jsonify` (Flask)
handles serialisation directly.

### 6. LOCALSTACK_HOSTNAME escape hatch removed

All handlers contained a conditional:
```python
if 'LOCALSTACK_HOSTNAME' in os.environ:
    dynamodb = boto3.resource('dynamodb', endpoint_url=...)
else:
    dynamodb = boto3.resource('dynamodb')
```

Both branches are boto3. Removed entirely; local dev now uses SQLite via
`DB_PATH=./todos.db`.

### 7. DYNAMODB_TABLE → DB_PATH (Pattern 4: Config)

Old env var encoded the storage technology in its name and was injected by
`serverless.yml` as `${self:service}-${opt:stage}`.

New env var is technology-neutral:
```python
DB_PATH = os.environ.get('DB_PATH', 'todos.db')
```

### 8. serverless.yml → requirements.txt

Removed the entire AWS serverless deployment descriptor (Lambda functions,
API Gateway events, DynamoDB CloudFormation resource, IAM role with AWS ARN,
LocalStack plugin). Replaced by a plain `requirements.txt` listing only Flask.

### 9. Abstraction layer introduced

Old system had zero separation between HTTP handling and persistence. New
system separates concerns:

- `app.py` — HTTP routing only; calls `database.*` functions
- `database.py` — all persistence; no Flask imports
- `config.py` — all configuration; no Flask or sqlite3 imports

### 10. Decimal → bool for `checked` field

SQLite stores booleans as `INTEGER` (0/1). `_row_to_dict` converts the raw
integer back to a Python `bool` so the JSON response returns `true`/`false`
as specified, not `0`/`1`.
