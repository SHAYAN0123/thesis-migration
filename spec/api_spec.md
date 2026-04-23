# Task Manager API — Specification (S_n)
# This specification does NOT change during migration.
# Both P_n (cloud-native) and P_n+1 (cloud-agnostic) must satisfy this spec.

## Overview
A simple task manager REST API that allows users to create, read, update, and delete tasks, attach files to tasks, and send notifications when tasks are completed.

## Endpoints

### POST /tasks
- Creates a new task
- Request body: { "title": string, "description": string, "status": "pending" }
- Returns: the created task with a generated ID
- Stores the task in a database

### GET /tasks
- Returns a list of all tasks

### GET /tasks/{id}
- Returns a single task by ID
- Returns 404 if not found

### PUT /tasks/{id}
- Updates a task's title, description, or status
- If status changes to "completed", sends a notification message
- Returns the updated task

### DELETE /tasks/{id}
- Deletes a task and any attached files
- Returns 204 on success

### POST /tasks/{id}/upload
- Uploads a file attachment to a task
- Accepts multipart form data
- Stores the file in object storage
- Returns the file URL

### GET /tasks/{id}/files
- Returns a list of file URLs attached to a task

## Behavior Rules
1. Task IDs are unique strings
2. All endpoints return JSON
3. File uploads are stored in object storage (not the database)
4. Completion notifications are sent via a message queue (async)
5. The API runs on port 5000

## Three Infrastructure Concerns
1. **Database** — where tasks are stored
2. **Object Storage** — where file attachments are stored
3. **Message Queue** — where completion notifications are sent