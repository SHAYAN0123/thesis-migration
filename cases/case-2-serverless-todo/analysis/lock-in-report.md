# Lock-In Analysis Report — Case 2: Serverless Todo

**System**: `cases/case-2-serverless-todo/old-system` (P_n)
**Spec**: `cases/case-2-serverless-todo/spec/api_spec.md` (S_n)
**Date**: 2026-04-24

---

## Analyzer Metrics (Deterministic)

| Metric         | Value |
|----------------|-------|
| Total files    | 8     |
| Python files   | 7     |
| Classes        | 1     |
| Functions      | 5     |
| Imports        | 24    |
| Cloud deps     | 5     |

---

## Cloud Lock-In Points

### 1. boto3 in Every Handler File (5/5 files)

| File          | boto3 Import | DynamoDB Operations Used                                          |
|---------------|-------------|-------------------------------------------------------------------|
| `create.py`   | yes         | `Table.put_item(Item=...)`                                        |
| `list.py`     | yes         | `Table.scan()`                                                    |
| `get.py`      | yes         | `Table.get_item(Key={'id': ...})`                                 |
| `update.py`   | yes         | `Table.update_item(Key, ExpressionAttributeNames, ExpressionAttributeValues, UpdateExpression, ReturnValues)` |
| `delete.py`   | yes         | `Table.delete_item(Key={'id': ...})`                              |

Every handler initialises the DynamoDB resource at module level (top-of-file `boto3.resource('dynamodb')`). There is no shared initialisation — the pattern is repeated identically in all five files.

### 2. Lambda Handler Contract (5/5 functions)

All five functions carry the signature `def <op>(event, context)` and unpack AWS API Gateway Proxy event fields directly:

- `event['body']` — raw JSON string (create, update)
- `event['pathParameters']['id']` — path parameter (get, update, delete)

This signature and these field names are dictated by the AWS API Gateway → Lambda Proxy integration. No standard HTTP framework is involved; the contract is 100% AWS-specific.

### 3. DynamoDB-Specific Response Shapes

The code depends on the DynamoDB SDK response structure in multiple places:

- `result['Item']` — `get_item` response (get.py:27)
- `result['Items']` — `scan` response (list.py:17)
- `result['Attributes']` — `update_item` response with `ReturnValues='ALL_NEW'` (update.py:49)

These keys are DynamoDB SDK conventions, not generic database abstractions.

### 4. DynamoDB Expression Syntax (update.py)

`update.py` embeds DynamoDB's proprietary update language inline in business logic:

```python
ExpressionAttributeNames={'#todo_text': 'text'},
ExpressionAttributeValues={':text': ..., ':checked': ..., ':updatedAt': ...},
UpdateExpression='SET #todo_text = :text, checked = :checked, updatedAt = :updatedAt',
ReturnValues='ALL_NEW',
```

`ExpressionAttributeNames` is required specifically because `text` is a reserved word in DynamoDB. This workaround is invisible to any non-DynamoDB database.

### 5. DecimalEncoder (decimalencoder.py)

`DecimalEncoder` exists solely because DynamoDB returns numeric attributes as Python `Decimal` objects (not `int` or `float`), which are not JSON-serialisable by default. This is a DynamoDB-specific data-type artefact — no other database or storage layer requires this workaround.

### 6. serverless.yml — Infrastructure-as-Code Lock-In

The deployment descriptor hardcodes the entire AWS stack:

| Section              | Lock-in detail                                                   |
|----------------------|------------------------------------------------------------------|
| `provider.name: aws` | Explicitly targets AWS                                           |
| `runtime: python3.8` | Lambda runtime identifier (AWS-specific)                         |
| `iamRoleStatements`  | AWS IAM policy granting DynamoDB actions (AWS RBAC model)        |
| `functions[*].events[*].http` | API Gateway HTTP event trigger (Serverless Framework / AWS) |
| `resources.Resources.TodosDynamoDbTable` | CloudFormation resource for DynamoDB table    |
| `arn:aws:dynamodb:...` | Hard-coded AWS ARN in IAM resource policy                      |
| `plugins: serverless-localstack` | LocalStack plugin for local dev (AWS emulator)       |

### 7. LOCALSTACK_HOSTNAME Escape Hatch (5/5 files)

All handlers contain:

```python
if 'LOCALSTACK_HOSTNAME' in os.environ:
    dynamodb_endpoint = 'http://%s:4566' % os.environ['LOCALSTACK_HOSTNAME']
    dynamodb = boto3.resource('dynamodb', endpoint_url=dynamodb_endpoint)
else:
    dynamodb = boto3.resource('dynamodb')
```

This is a dev-environment escape hatch pointing to LocalStack (an AWS emulator), not an abstraction. The underlying API is still boto3 / DynamoDB in both branches.

### 8. Environment Variable: DYNAMODB_TABLE

Table name is read from `os.environ['DYNAMODB_TABLE']` in every handler that touches the table (create, list, get, update, delete). The variable name itself encodes the storage technology, and the variable is injected by `serverless.yml` as `${self:service}-${opt:stage}`.

---

## Coupling Assessment: Business Logic vs. Infrastructure

There is **zero separation** between business logic and infrastructure in this codebase.

| Concern                        | Location            | Verdict                      |
|-------------------------------|---------------------|------------------------------|
| Input validation (`text` required) | `create.py:18`, `update.py:18` | Mixed in handler          |
| UUID generation                | `create.py:27`      | Mixed in handler             |
| Timestamp generation           | `create.py:22`, `update.py:23` | Mixed in handler       |
| Default `checked: false`       | `create.py:30`      | Mixed in handler             |
| Persistence (CRUD)             | All five handlers   | boto3 call inline            |
| Response formatting            | All five handlers   | AWS Lambda response dict inline |

Every handler is simultaneously responsible for: request parsing, validation, domain logic (UUID, timestamp, default values), persistence, and response serialisation. No layer in the stack is independent of AWS.

---

## Abstraction Layer Assessment

**There is no abstraction layer.**

Compare with Case 1 (Task Manager):
- Case 1 had `database.py` / `storage.py` / `notifications.py` — provider calls were isolated behind interfaces
- Case 2 has no such modules — boto3 calls appear directly at the business-logic level in every handler

The only shared utility is `decimalencoder.py`, which is itself AWS/DynamoDB-specific.

---

## Sovereignty Violation Summary

| # | Violation                                      | Scope           | Files Affected      |
|---|------------------------------------------------|-----------------|---------------------|
| 1 | Direct boto3 import and use                    | All handlers    | create, list, get, update, delete |
| 2 | AWS Lambda handler signature `(event, context)` | Compute         | All 5               |
| 3 | API Gateway event shape `event['pathParameters']` | Routing       | get, update, delete |
| 4 | DynamoDB response keys `['Item']`, `['Items']`, `['Attributes']` | Storage | list, get, update |
| 5 | DynamoDB UpdateExpression / ExpressionAttributeNames | Storage   | update              |
| 6 | DecimalEncoder (DynamoDB Decimal type)         | Serialisation   | list, get, update   |
| 7 | CloudFormation DynamoDB table definition       | IaC             | serverless.yml      |
| 8 | AWS IAM role with DynamoDB ARN                 | Security        | serverless.yml      |
| 9 | LOCALSTACK_HOSTNAME conditional (boto3 in both branches) | Dev config | All 5          |
| 10 | `DYNAMODB_TABLE` env var convention            | Config          | All 5               |

---

## Migration Requirements for P_n+1

To satisfy S_n on a cloud-agnostic stack, P_n+1 must:

1. **Replace boto3 / DynamoDB** with a portable storage backend (e.g. SQLite, PostgreSQL via SQLAlchemy, or any key-value store with a generic interface).
2. **Replace Lambda handler contract** with a standard HTTP framework (e.g. Flask, FastAPI) that parses `request.json` and `request.view_args`.
3. **Eliminate DynamoDB response key unpacking** — results should be plain Python dicts.
4. **Eliminate DynamoDB UpdateExpression syntax** — updates should be standard attribute assignments.
5. **Eliminate DecimalEncoder** — no longer needed once DynamoDB is removed.
6. **Replace serverless.yml** with a container- or process-based deployment descriptor (`Dockerfile`, `docker-compose.yml`, or similar).
7. **Introduce a storage abstraction layer** — at minimum a `TodoRepository` interface so the HTTP layer has no direct knowledge of the storage technology.

All five behavior rules and five API endpoints defined in S_n remain unchanged.
