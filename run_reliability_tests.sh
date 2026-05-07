#!/bin/bash
# Run the 43 spec-driven tests and v2 analyzer against all reliability runs.
# Auto-detects run-{N} directories. Produces reliability-results.md
#
# Run structure:
#   run-1  to run-10  = Condition A (detailed prompt)
#   run-11 to run-20  = Condition B (vague prompt)
#
# Backward compatible: if only run-1..6 exist, uses original 1-3=A, 4-6=B split.

set -e
cd "$(dirname "$0")"

EVIDENCE="cases/case-2-serverless-todo/evidence"
RUNS_DIR="cases/case-2-serverless-todo/transformation"
OUTPUT="cases/case-2-serverless-todo/transformation/reliability-results.md"

# Auto-detect available runs
RUNS=()
for d in "$RUNS_DIR"/run-*/; do
    if [ -d "$d" ]; then
        num=$(basename "$d" | sed 's/run-//')
        RUNS+=("$num")
    fi
done

# Sort numerically
IFS=$'\n' RUNS=($(sort -n <<<"${RUNS[*]}")); unset IFS

TOTAL_RUNS=${#RUNS[@]}

# Determine condition split
if [ "$TOTAL_RUNS" -le 6 ]; then
    # Legacy: 1-3 = A, 4-6 = B
    SPLIT=3
    COND_A_LABEL="Runs 1–3"
    COND_B_LABEL="Runs 4–6"
else
    # New: 1-10 = A, 11-20 = B
    SPLIT=10
    COND_A_LABEL="Runs 1–10"
    COND_B_LABEL="Runs 11–20"
fi

get_condition() {
    local run_num=$1
    if [ "$TOTAL_RUNS" -le 6 ]; then
        if [ "$run_num" -le 3 ]; then echo "A (detailed)"; else echo "B (vague)"; fi
    else
        if [ "$run_num" -le 10 ]; then echo "A (detailed)"; else echo "B (vague)"; fi
    fi
}

get_cond_short() {
    local run_num=$1
    if [ "$TOTAL_RUNS" -le 6 ]; then
        if [ "$run_num" -le 3 ]; then echo "A"; else echo "B"; fi
    else
        if [ "$run_num" -le 10 ]; then echo "A"; else echo "B"; fi
    fi
}

echo "Found $TOTAL_RUNS reliability runs."
echo ""

# --- Write report header ---
cat > "$OUTPUT" <<EOF
# Reliability Evaluation Results — SRQ3

**Date:** $(date +%Y-%m-%d)
**Application:** Case Study 2 — Serverless Todo API
**Runs:** $TOTAL_RUNS (${COND_A_LABEL} = Condition A, ${COND_B_LABEL} = Condition B)
**Test suite:** 43 spec-driven tests from \`$EVIDENCE/test_api.py\`
**Analyzer:** \`analyzer.py\` v2 (4-layer detection: imports, manifests, config, source strings)

---

## Condition A: Detailed Prompt (${COND_A_LABEL})

Prompt specifies: SQLite, Flask, explicit constraints (no boto3, no AWS).

## Condition B: Vague Prompt (${COND_B_LABEL})

Prompt specifies only: "migrate this to be cloud-agnostic."

---

## Summary Table

| Run | Condition | Py Files | Functions | Cloud Deps (4-layer) | Config Scanned | Tests Passed | Tests Failed | Gate 1 | Gate 2 |
|-----|-----------|----------|-----------|----------------------|----------------|-------------|-------------|--------|--------|
EOF

# Counters for aggregate stats
A_PASS_G1=0; A_TOTAL=0; A_PASS_G2=0
B_PASS_G1=0; B_TOTAL=0; B_PASS_G2=0

for i in "${RUNS[@]}"; do
    RUN_PATH="$RUNS_DIR/run-$i"
    COND=$(get_condition "$i")

    echo ""
    echo "========================================="
    echo "  Running tests for Run $i ($COND)"
    echo "========================================="

    # Analyzer (v2 — 4 detection layers)
    ANALYZER_JSON=$(python3 analyzer.py "$RUN_PATH" --json)
    PY_FILES=$(echo "$ANALYZER_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['python_files'])")
    FUNCTIONS=$(echo "$ANALYZER_JSON" | python3 -c "import json,sys; print(len(json.load(sys.stdin)['functions']))")
    CLOUD_DEPS=$(echo "$ANALYZER_JSON" | python3 -c "import json,sys; print(len(json.load(sys.stdin)['cloud_dependencies']))")
    CONFIG_SCANNED=$(echo "$ANALYZER_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin).get('config_files_scanned',0))")
    LAYERS=$(echo "$ANALYZER_JSON" | python3 -c "
import json,sys
d=json.load(sys.stdin)['cloud_dependencies_by_layer']
parts = []
for k,v in d.items():
    parts.append(f'{k}={len(v)}')
print(', '.join(parts))
")

    # Gate 2
    if [ "$CLOUD_DEPS" = "0" ]; then
        GATE2="PASS"
    else
        GATE2="FAIL"
    fi

    # Tests
    TEST_OUTPUT=$(TEST_SYSTEM_PATH="$RUN_PATH" python3 -m pytest "$EVIDENCE" -v --tb=short 2>&1) || true

    PASSED=$(echo "$TEST_OUTPUT" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
    FAILED=$(echo "$TEST_OUTPUT" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")

    # Gate 1
    if [ "$FAILED" = "0" ] && [ "$PASSED" != "0" ]; then
        GATE1="PASS"
    else
        GATE1="FAIL"
    fi

    echo "  Files: $PY_FILES | Functions: $FUNCTIONS | Cloud deps: $CLOUD_DEPS ($LAYERS) | Passed: $PASSED | Failed: $FAILED | Gate1: $GATE1 | Gate2: $GATE2"

    echo "| $i | $COND | $PY_FILES | $FUNCTIONS | $CLOUD_DEPS | $CONFIG_SCANNED | $PASSED | $FAILED | $GATE1 | $GATE2 |" >> "$OUTPUT"

    # Aggregate
    COND_SHORT=$(get_cond_short "$i")
    if [ "$COND_SHORT" = "A" ]; then
        A_TOTAL=$((A_TOTAL + 1))
        [ "$GATE1" = "PASS" ] && A_PASS_G1=$((A_PASS_G1 + 1))
        [ "$GATE2" = "PASS" ] && A_PASS_G2=$((A_PASS_G2 + 1))
    else
        B_TOTAL=$((B_TOTAL + 1))
        [ "$GATE1" = "PASS" ] && B_PASS_G1=$((B_PASS_G1 + 1))
        [ "$GATE2" = "PASS" ] && B_PASS_G2=$((B_PASS_G2 + 1))
    fi
done

# --- Aggregate Statistics ---
cat >> "$OUTPUT" <<EOF

---

## Aggregate Statistics

| Condition | Runs | Gate 1 Pass Rate | Gate 2 Pass Rate |
|-----------|------|-----------------|-----------------|
| A (detailed) | $A_TOTAL | $A_PASS_G1/$A_TOTAL ($(( A_TOTAL > 0 ? A_PASS_G1 * 100 / A_TOTAL : 0 ))%) | $A_PASS_G2/$A_TOTAL ($(( A_TOTAL > 0 ? A_PASS_G2 * 100 / A_TOTAL : 0 ))%) |
| B (vague) | $B_TOTAL | $B_PASS_G1/$B_TOTAL ($(( B_TOTAL > 0 ? B_PASS_G1 * 100 / B_TOTAL : 0 ))%) | $B_PASS_G2/$B_TOTAL ($(( B_TOTAL > 0 ? B_PASS_G2 * 100 / B_TOTAL : 0 ))%) |
| **Total** | **$TOTAL_RUNS** | **$((A_PASS_G1 + B_PASS_G1))/$TOTAL_RUNS** | **$((A_PASS_G2 + B_PASS_G2))/$TOTAL_RUNS** |

---

## Architectural Variation

| Run | Condition | Structure | Timestamp Method | DB Helper Pattern |
|-----|-----------|-----------|-----------------|-------------------|
EOF

for i in "${RUNS[@]}"; do
    RUN_PATH="$RUNS_DIR/run-$i"
    COND_SHORT=$(get_cond_short "$i")

    # Structure
    FILE_COUNT=$(find "$RUN_PATH" -name "*.py" | wc -l | tr -d ' ')
    if [ "$FILE_COUNT" = "1" ]; then
        STRUCTURE="Monolithic (1 file)"
    else
        STRUCTURE="Modular ($FILE_COUNT files)"
    fi

    # Timestamp method — search all .py files recursively
    ALL_PY=$(find "$RUN_PATH" -name "*.py" -print0 | xargs -0 cat 2>/dev/null)
    if echo "$ALL_PY" | grep -q "datetime"; then
        TS="datetime"
    elif echo "$ALL_PY" | grep -q "time\.time"; then
        TS="time.time()"
    elif echo "$ALL_PY" | grep -q "isoformat"; then
        TS="isoformat"
    else
        TS="unknown"
    fi

    # DB helper
    if echo "$ALL_PY" | grep -q "def _get_conn\|def _connect\|def get_db\|def init_db\|def get_connection"; then
        DB="Connection helper function"
    else
        DB="Inline connection"
    fi

    echo "| $i | $COND_SHORT | $STRUCTURE | $TS | $DB |" >> "$OUTPUT"
done

cat >> "$OUTPUT" <<EOF

---

## Interpretation

*To be completed after reviewing results.*
EOF

echo ""
echo "========================================="
echo "  DONE — Results written to: $OUTPUT"
echo "  Runs evaluated: $TOTAL_RUNS"
echo "========================================="
echo ""
cat "$OUTPUT"
