# Generate tests for the old system (Evidence — E)

Read the specification in /spec/api_spec.md.
Read all code in /old-system/.

Generate a test suite in /evidence/ that:

1. Tests every endpoint defined in the spec (POST, GET, PUT, DELETE /tasks, file upload, file list)
2. Tests the behavior rules from the spec (unique IDs, JSON responses, completion notifications)
3. Uses pytest and mocks for AWS services (mock boto3 calls)
4. Tests ONLY against the spec — not against implementation details

Save tests to /evidence/test_api.py and /evidence/conftest.py.

These tests must pass on BOTH P_n (old-system) and P_n+1 (new-system).
That is the proof of semantic equivalence.