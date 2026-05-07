#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# Feedback / Repair Loop — SRQ3 extension
# ═══════════════════════════════════════════════════════════════════════════
#
# Purpose:
#   After the initial 20 reliability runs, some runs fail Gate 1 (tests).
#   This script implements an iterative repair loop:
#     1. Run the test suite against a failing run
#     2. Capture the pytest failure output
#     3. Feed the failure output back to the LLM with the failing code
#     4. LLM produces a patched version
#     5. Re-run tests to verify the fix
#     6. Repeat up to MAX_ATTEMPTS times
#
# This demonstrates a key thesis contribution: LLM-assisted migration is
# more effective as a LOOP (generate → verify → repair) than as a single
# shot (generate only).
#
# Usage:
#   bash repair_loop.sh                     # repair all failing runs
#   bash repair_loop.sh 5                   # repair only run-5
#   bash repair_loop.sh 4 5 6 7 8 17       # repair specific runs
#
# Prerequisites:
#   - Python 3.9+ with pytest, flask, moto, boto3
#   - Claude Code CLI (`claude` command available)
#   - pip install -r cases/case-2-serverless-todo/evidence/requirements.txt
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail
cd "$(dirname "$0")"

MAX_ATTEMPTS=3
CASE_DIR="cases/case-2-serverless-todo"
EVIDENCE_DIR="$CASE_DIR/evidence"
TRANSFORM_DIR="$CASE_DIR/transformation"
SPEC="$CASE_DIR/spec/api_spec.md"
OLD_SYSTEM="$CASE_DIR/old-system"
RESULTS_FILE="$TRANSFORM_DIR/repair-results.md"

# ── Colour helpers ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

# ── Determine which runs to repair ──────────────────────────────────────────
if [ $# -gt 0 ]; then
    RUNS=("$@")
else
    # Auto-detect failing runs: test each, collect those with <43 passed
    echo "Auto-detecting failing runs..."
    RUNS=()
    for d in "$TRANSFORM_DIR"/run-*; do
        [ -d "$d" ] || continue
        RUN_NUM=$(basename "$d" | sed 's/run-//')
        PY_COUNT=$(find "$d" -maxdepth 1 -name "*.py" | wc -l | tr -d ' ')
        [ "$PY_COUNT" -eq 0 ] && continue

        RESULT=$(TEST_SYSTEM_PATH="$d" python -m pytest "$EVIDENCE_DIR/" -q --tb=no 2>&1 | tail -1)
        PASSED=$(echo "$RESULT" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
        if [ "$PASSED" -lt 43 ]; then
            RUNS+=("$RUN_NUM")
            echo "  run-$RUN_NUM: $PASSED/43 → needs repair"
        fi
    done
    echo ""
    if [ ${#RUNS[@]} -eq 0 ]; then
        echo -e "${GREEN}All runs pass! Nothing to repair.${NC}"
        exit 0
    fi
fi

echo "═══════════════════════════════════════════════════════════════"
echo "  FEEDBACK / REPAIR LOOP"
echo "  Runs to repair: ${RUNS[*]}"
echo "  Max attempts per run: $MAX_ATTEMPTS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ── Initialize results file ────────────────────────────────────────────────
cat > "$RESULTS_FILE" << 'HEADER'
# Repair Loop Results — SRQ3 Extension

**Date:** $(date +%Y-%m-%d)
**Max repair attempts:** 3
**Test suite:** 43 spec-driven tests

---

| Run | Attempt | Tests Passed | Tests Failed | Gate 1 | Repair Action |
|-----|---------|-------------|-------------|--------|---------------|
HEADER
# Fix the date in the header
sed -i "s/\$(date +%Y-%m-%d)/$(date +%Y-%m-%d)/" "$RESULTS_FILE"

# ── Repair function ────────────────────────────────────────────────────────

repair_run() {
    local RUN_NUM=$1
    local RUN_DIR="$TRANSFORM_DIR/run-$RUN_NUM"

    echo -e "${YELLOW}── Run $RUN_NUM ──${NC}"

    # Back up the original (pre-repair) code
    local BACKUP_DIR="$RUN_DIR/.original-backup"
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        cp "$RUN_DIR"/*.py "$BACKUP_DIR/" 2>/dev/null || true
        echo "  Backed up original code to $BACKUP_DIR/"
    fi

    for ATTEMPT in $(seq 1 $MAX_ATTEMPTS); do
        echo ""
        echo "  Attempt $ATTEMPT/$MAX_ATTEMPTS"

        # ── Step 1: Run tests, capture verbose output ──────────────────
        echo "  [1/4] Running tests..."
        local TEST_OUTPUT
        TEST_OUTPUT=$(TEST_SYSTEM_PATH="$RUN_DIR" python -m pytest "$EVIDENCE_DIR/" -v --tb=short 2>&1) || true

        local SUMMARY_LINE
        SUMMARY_LINE=$(echo "$TEST_OUTPUT" | tail -1)
        local PASSED
        PASSED=$(echo "$SUMMARY_LINE" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
        local FAILED
        FAILED=$(echo "$SUMMARY_LINE" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")

        echo "  Result: $PASSED passed, $FAILED failed"

        # ── Step 2: Check if already passing ───────────────────────────
        if [ "$PASSED" -eq 43 ] && [ "$FAILED" -eq 0 ]; then
            echo -e "  ${GREEN}✓ All 43 tests pass! Run $RUN_NUM is repaired.${NC}"
            echo "| $RUN_NUM | $ATTEMPT | $PASSED | $FAILED | PASS | $([ $ATTEMPT -eq 1 ] && echo 'Already passing' || echo 'Fix applied') |" >> "$RESULTS_FILE"
            return 0
        fi

        # Record pre-repair state
        echo "| $RUN_NUM | $ATTEMPT | $PASSED | $FAILED | FAIL | Feeding errors to LLM... |" >> "$RESULTS_FILE"

        # ── Step 3: Extract failure details ────────────────────────────
        echo "  [2/4] Extracting failure details..."
        local FAILURES
        FAILURES=$(echo "$TEST_OUTPUT" | grep -A 20 "FAILED\|ERRORS\|AssertionError" | head -60)

        # Collect current source code
        local SOURCE_CODE=""
        for pyfile in "$RUN_DIR"/*.py; do
            [ -f "$pyfile" ] || continue
            SOURCE_CODE="$SOURCE_CODE
--- $(basename "$pyfile") ---
$(cat "$pyfile")
"
        done

        # ── Step 4: Feed to LLM for repair ─────────────────────────────
        echo "  [3/4] Sending failure output to LLM for repair..."

        local REPAIR_PROMPT="You are repairing a Flask + SQLite application that was migrated from AWS Lambda + DynamoDB. The application lives in $RUN_DIR/.

The test suite ran 43 tests. $FAILED test(s) failed. Here is the pytest output:

\`\`\`
$FAILURES
\`\`\`

Here is the full test summary:
\`\`\`
$SUMMARY_LINE
\`\`\`

Here is the current source code of the application:
\`\`\`
$SOURCE_CODE
\`\`\`

IMPORTANT CONTEXT:
- The test harness injects the database path via: os.environ.setdefault(\"DB_PATH\", <test_db_path>)
- Your application MUST read the database path from os.environ.get(\"DB_PATH\", \"todos.db\")
- Do NOT use DATABASE_PATH or any other env var name for the database path
- The spec is at $SPEC — read it if you need to understand the expected behavior

Fix the failing test(s) by modifying the source files in $RUN_DIR/. Write the corrected files using your Write tool. Do NOT create new files outside $RUN_DIR/. Keep the same architecture (Flask + SQLite). Make the MINIMAL change needed to fix the failure."

        claude -p "$REPAIR_PROMPT" --dangerously-skip-permissions 2>&1 | tail -5

        # ── Step 5: Verify the fix ─────────────────────────────────────
        echo "  [4/4] Verifying repair..."
        local VERIFY_OUTPUT
        VERIFY_OUTPUT=$(TEST_SYSTEM_PATH="$RUN_DIR" python -m pytest "$EVIDENCE_DIR/" -q --tb=no 2>&1) || true

        local VERIFY_LINE
        VERIFY_LINE=$(echo "$VERIFY_OUTPUT" | tail -1)
        local V_PASSED
        V_PASSED=$(echo "$VERIFY_LINE" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
        local V_FAILED
        V_FAILED=$(echo "$VERIFY_LINE" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")

        echo "  Post-repair: $V_PASSED passed, $V_FAILED failed"

        if [ "$V_PASSED" -eq 43 ] && [ "$V_FAILED" -eq 0 ]; then
            echo -e "  ${GREEN}✓ REPAIRED after attempt $ATTEMPT!${NC}"
            # Update the last line to show success
            echo "| $RUN_NUM | ${ATTEMPT}+ | $V_PASSED | $V_FAILED | PASS | Repair successful |" >> "$RESULTS_FILE"
            return 0
        fi
    done

    echo -e "  ${RED}✗ Run $RUN_NUM still failing after $MAX_ATTEMPTS attempts.${NC}"
    echo "| $RUN_NUM | FINAL | $V_PASSED | $V_FAILED | FAIL | Max attempts exhausted |" >> "$RESULTS_FILE"
    return 1
}

# ── Main loop ──────────────────────────────────────────────────────────────

TOTAL_REPAIRED=0
TOTAL_FAILED=0

for RUN_NUM in "${RUNS[@]}"; do
    if repair_run "$RUN_NUM"; then
        ((TOTAL_REPAIRED++))
    else
        ((TOTAL_FAILED++))
    fi
    echo ""
done

# ── Summary ────────────────────────────────────────────────────────────────
cat >> "$RESULTS_FILE" << EOF

---

## Summary

- **Runs attempted:** ${#RUNS[@]}
- **Successfully repaired:** $TOTAL_REPAIRED
- **Still failing:** $TOTAL_FAILED
- **Repair rate:** $(( TOTAL_REPAIRED * 100 / ${#RUNS[@]} ))%

## Interpretation

The feedback/repair loop demonstrates that LLM-generated migrations that
fail on first attempt can often be fixed by feeding test output back to the
LLM. The most common failure mode (env var naming mismatch) is trivially
fixable once the LLM sees the test error, supporting the thesis claim that
spec-driven verification gates enable iterative improvement.
EOF

echo "═══════════════════════════════════════════════════════════════"
echo "  REPAIR LOOP COMPLETE"
echo "  Repaired: $TOTAL_REPAIRED / ${#RUNS[@]}"
echo "  Failed:   $TOTAL_FAILED / ${#RUNS[@]}"
echo "  Results:  $RESULTS_FILE"
echo "═══════════════════════════════════════════════════════════════"
