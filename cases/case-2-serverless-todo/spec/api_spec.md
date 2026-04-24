# Todo API Specification (S_n)

This specification defines the REQUIRED behavior of the Todo service.
Any correct implementation (P_n or P_n+1) MUST satisfy ALL of these rules.
The specification is INDEPENDENT of infrastructure — it does not mention
DynamoDB, Lambda, AWS, or any specific technology.

## Data Model

A Todo item has the following fields:

| Field       | Type    | Required | Description                        |
|-------------|---------|----------|------------------------------------|
| id          | string  | yes      | Unique identifier (UUID)           |
| text        | string  | yes      | The todo content                   |
| checked     | boolean | yes      | Completion status (default: false) |
| createdAt   | string  | yes      | Timestamp when created             |
| updatedAt   | string  | yes      | Timestamp when last updated        |

## API Endpoints

### POST /todos — Create a Todo

- Request body: JSON with `text` field (required)
- Creates a new todo with a generated UUID, `checked: false`, and timestamps
- Returns: the created todo as JSON
- Status: 200

### GET /todos — List All Todos

- No request body
- Returns: JSON array of all todos
- Status: 200

### GET /todos/{id} — Get a Single Todo

- Path parameter: `id` (required)
- Returns: the todo matching the given ID as JSON
- Status: 200
- If not found: returns error (status 404 or equivalent)

### PUT /todos/{id} — Update a Todo

- Path parameter: `id` (required)
- Request body: JSON with `text` (string) and `checked` (boolean)
- Updates the todo's text, checked status, and updatedAt timestamp
- Returns: the updated todo attributes as JSON
- Status: 200

### DELETE /todos/{id} — Delete a Todo

- Path parameter: `id` (required)
- Deletes the todo matching the given ID
- Returns: empty response
- Status: 200

## Behavior Rules

1. Every created todo MUST have a unique UUID as its `id`
2. Every created todo MUST have `checked` set to `false` by default
3. Every created todo MUST record `createdAt` and `updatedAt` timestamps
4. Updating a todo MUST change the `updatedAt` timestamp
5. Updating a todo MUST NOT change the `id` or `createdAt`
6. Deleting a todo MUST remove it permanently — subsequent GET returns not found
7. Listing todos MUST return ALL existing todos
8. The service MUST persist data between requests (not in-memory only)

## Infrastructure Concerns (to be replaced during migration)

The current implementation (P_n) uses:

1. **Database**: AWS DynamoDB via boto3 — inline in every handler file
2. **Compute**: AWS Lambda functions — one handler per CRUD operation
3. **Routing**: AWS API Gateway — defined in serverless.yml
4. **Config**: Environment variable `DYNAMODB_TABLE` for table name

The migrated implementation (P_n+1) MUST satisfy the same spec using
cloud-agnostic alternatives while preserving ALL behavior rules above.

## Key Differences from Case 1 (Task Manager)

- No clean abstraction layer — boto3 is called DIRECTLY in handler code
- Serverless architecture — Lambda handlers, not Flask routes
- No separate database.py/storage.py/notifications.py modules
- Only one AWS service (DynamoDB), not three
- Business logic and infrastructure logic are MIXED in the same files