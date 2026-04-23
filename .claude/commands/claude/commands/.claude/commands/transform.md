# Transform P_n to P_n+1 (cloud-native to cloud-agnostic)

Read these files first:
1. /spec/api_spec.md — the specification (S_n) that must not change
2. /analysis/lock-in-report.md — what cloud dependencies exist
3. /transformation/patterns.md — the formal transformation patterns to follow
4. All code in /old-system/

For each cloud dependency found in the lock-in report, apply the matching
pattern from patterns.md:

- Pattern 1 (Database): boto3 DynamoDB → SQLite
- Pattern 2 (Storage): boto3 S3 → local filesystem
- Pattern 3 (Queue): boto3 SQS → JSONL file queue
- Pattern 4 (Config): cloud-specific env vars → generic paths

Rules:
- Function signatures MUST NOT change (Interface Preservation Principle)
- app.py MUST remain identical — copy it, do not modify it
- Only infrastructure modules change (database.py, storage.py, notifications.py, config.py)
- requirements.txt: remove boto3, keep only stdlib + flask
- Use stdlib only for replacements (sqlite3, os, shutil, json)

Generate all files in /new-system/.

After generating, run:
- python3 analyzer.py new-system --json (confirm 0 cloud dependencies)
- python3 -m pytest evidence/ -v (confirm all tests pass on old-system)
- TEST_SYSTEM_PATH=new-system python3 -m pytest evidence/ -v (confirm all tests pass on new-system)

Document every change in /transformation/changes.md.

Stochastic: you generate the code.
Deterministic: the analyzer and tests verify it.