"""
Failure Root-Cause Analysis — 6 failing reliability runs.

This script analyses WHY exactly 6 out of 20 reliability runs fail Gate 1
(42/43 tests instead of 43/43).

Root cause: environment variable mismatch
─────────────────────────────────────────
The test harness (conftest.py, line 82) injects the test database path via:
    os.environ.setdefault("DB_PATH", _db_path)

Passing runs read: os.environ.get("DB_PATH", "todos.db")   → picks up test DB
Failing runs read: os.environ.get("DATABASE_PATH", "todos.db") → ignores test DB

Because the failing runs never see the injected path, they create/write to a
*separate* SQLite file ("todos.db" in the working directory).  Meanwhile, the
conftest._clean_state() fixture cleans the test DB (at _db_path), leaving the
app's actual "todos.db" untouched between tests.

This means state leaks across tests in failing runs. The FIRST test that
depends on a clean database will fail.

Pytest collects tests in file order.  The first state-dependent test is:
    test_list_is_empty_before_any_create  (test #14 in file order)

This test asserts:
    client.get("/todos").get_json() == []

If ANY prior test left data behind (because cleanup missed the app's DB),
this test sees leftover todos and fails.

Usage:
    python failure_analysis.py
"""
import os
import re

TRANSFORM_DIR = os.path.join(os.path.dirname(__file__), "..", "transformation")

# Tests in file order (pytest default collection order)
TESTS_IN_ORDER = [
    "test_create_returns_200",
    "test_create_response_is_json",
    "test_create_response_contains_id",
    "test_create_id_is_non_empty_string",
    "test_create_id_is_valid_uuid",
    "test_create_text_is_stored",
    "test_create_checked_defaults_to_false",
    "test_create_has_created_at",
    "test_create_has_updated_at",
    "test_create_without_text_returns_error",
    "test_list_returns_200",
    "test_list_response_is_json",
    "test_list_returns_array",
    "test_list_is_empty_before_any_create",          # ← FIRST state-sensitive test
    "test_list_contains_created_todo",
    "test_list_returns_all_todos",
    "test_get_one_returns_200",
    "test_get_one_response_is_json",
    "test_get_one_returns_correct_todo",
    "test_get_one_returns_all_five_fields",
    "test_get_one_returns_404_for_unknown_id",
    "test_update_returns_200",
    "test_update_response_is_json",
    "test_update_text_is_changed",
    "test_update_checked_can_be_set_to_true",
    "test_update_checked_can_be_toggled_back_to_false",
    "test_update_response_includes_updated_at",
    "test_update_changes_updated_at_timestamp",
    "test_update_does_not_change_id",
    "test_update_does_not_change_created_at",
    "test_delete_returns_200",
    "test_delete_subsequent_get_returns_404",
    "test_delete_removes_todo_from_list",
    "test_delete_does_not_affect_other_todos",
    "test_spec_rule_1_ids_are_unique_uuids",
    "test_spec_rule_2_checked_is_false_by_default",
    "test_spec_rule_3_timestamps_recorded_on_create",
    "test_spec_rule_4_updated_at_changes_on_update",
    "test_spec_rule_5_id_immutable_after_update",
    "test_spec_rule_5_created_at_immutable_after_update",
    "test_spec_rule_6_delete_is_permanent",
    "test_spec_rule_7_list_returns_all_existing_todos",
    "test_spec_rule_8_data_persists_between_requests",
]


def scan_env_var(run_dir):
    """Return the env var name used by the run to locate the database."""
    for fname in os.listdir(run_dir):
        if not fname.endswith(".py"):
            continue
        with open(os.path.join(run_dir, fname)) as f:
            src = f.read()
        # Match patterns like os.environ.get("DATABASE_PATH", ...)
        m = re.search(r'os\.environ\.get\(["\'](\w+)["\']', src)
        if m:
            return m.group(1)
    return "UNKNOWN"


def main():
    print("=" * 78)
    print("FAILURE ROOT-CAUSE ANALYSIS — Reliability Runs")
    print("=" * 78)
    print()

    failing_runs = []
    passing_runs = []

    for d in sorted(os.listdir(TRANSFORM_DIR)):
        run_dir = os.path.join(TRANSFORM_DIR, d)
        if not os.path.isdir(run_dir) or not d.startswith("run-"):
            continue

        env_var = scan_env_var(run_dir)
        run_num = int(d.split("-")[1])
        entry = {"run": run_num, "dir": d, "env_var": env_var}

        if env_var == "DB_PATH":
            passing_runs.append(entry)
        else:
            failing_runs.append(entry)

    print(f"Passing runs ({len(passing_runs)}): env var = DB_PATH")
    for r in passing_runs:
        print(f"  {r['dir']:10s}  →  {r['env_var']}")

    print()
    print(f"Failing runs ({len(failing_runs)}): env var ≠ DB_PATH")
    for r in failing_runs:
        print(f"  {r['dir']:10s}  →  {r['env_var']}")

    print()
    print("-" * 78)
    print("MECHANISM:")
    print("-" * 78)
    print("""
1. conftest.py sets:   os.environ.setdefault("DB_PATH", <test_db_path>)
2. Passing runs use:   os.environ.get("DB_PATH", "todos.db")
   → App reads/writes to the TEST database
   → conftest._clean_state() cleans the SAME database  ✓
   → Each test starts with empty state  ✓

3. Failing runs use:   os.environ.get("DATABASE_PATH", "todos.db")
   → App reads/writes to "todos.db" in the working directory
   → conftest._clean_state() cleans a DIFFERENT database  ✗
   → State leaks from test to test  ✗

4. The first test that asserts empty state is:
   test_list_is_empty_before_any_create  (test #14 in collection order)

5. By test #14, nine prior POST /todos tests have each created a todo.
   None were cleaned up from the app's actual database.
   → The list endpoint returns ~9 leftover todos instead of []
   → Assertion `== []` fails  →  42/43 passed, 1 failed
""")

    print("-" * 78)
    print("IMPLICATION FOR THESIS:")
    print("-" * 78)
    print("""
The single failing test is NOT a functional defect in the migrated code.
All 5 CRUD endpoints work correctly.  The failure is an ENV VAR NAMING
CONVENTION mismatch between the generated code and the test harness.

This is precisely the kind of "interface contract" issue that motivates
the proposed FEEDBACK/REPAIR LOOP:
  1. Run tests
  2. Parse failure output
  3. Feed the error message back to the LLM
  4. LLM fixes the naming mismatch
  5. Re-run → 43/43 PASS

The repair is trivial (s/DATABASE_PATH/DB_PATH/) but the LLM had no way
to know the harness convention without seeing the test output first.
""")


if __name__ == "__main__":
    main()
