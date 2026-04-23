# Transform P_n to P_n+1 (cloud-native to cloud-agnostic)

Read the specification in /spec/api_spec.md.
Read the lock-in report in /analysis/lock-in-report.md.
Read all code in /old-system/.

Generate a cloud-agnostic version in /new-system/ that:

1. Satisfies the SAME specification (S_n does not change)
2. Replaces DynamoDB with SQLite (portable, no vendor lock-in)
3. Replaces S3 with local filesystem storage (portable)
4. Replaces SQS with a simple in-memory queue or file-based queue (portable)
5. Keeps app.py as close to the original as possible
6. Keeps the same function signatures in database.py, storage.py, notifications.py

The API must behave identically. Only the infrastructure layer changes.
The tests in /evidence/ must pass on this new version.

Document every change you make in /transformation/changes.md.