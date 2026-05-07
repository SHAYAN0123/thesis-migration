#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# Knowledge Source Experiment — Generate runs for Condition F (no spec)
# ═══════════════════════════════════════════════════════════════════════════
#
# Purpose: Test whether the behavioral specification is a critical
#          knowledge source by removing it from the prompt.
#
# Condition F is identical to Condition B (vague) except it does NOT
# reference the spec file. This isolates the spec's contribution.
#
# Run structure:
#   Runs 36-40 = Condition F (no spec)
#
# Usage:
#   bash generate_knowledge_source_runs.sh
# ═══════════════════════════════════════════════════════════════════════════

set -e
cd "$(dirname "$0")"

RUNS_DIR="cases/case-2-serverless-todo/transformation"
OLD_SYSTEM="cases/case-2-serverless-todo/old-system"
# NOTE: Spec is intentionally NOT passed to the LLM in this condition

echo "═══════════════════════════════════════════════════════════════"
echo "  KNOWLEDGE SOURCE EXPERIMENT — Condition F (no spec)"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  This condition removes the behavioral specification from the"
echo "  prompt to test whether the LLM can extract behavior from the"
echo "  old source code alone."
echo ""

for i in $(seq 36 40); do
    TARGET="$RUNS_DIR/run-$i"
    if [ -d "$TARGET" ] && [ "$(find "$TARGET" -name '*.py' | wc -l | tr -d ' ')" -gt 0 ]; then
        echo "  Run $i already has Python files, skipping."
        continue
    fi
    [ -d "$TARGET" ] && rm -rf "$TARGET"
    mkdir -p "$TARGET"

    echo ""
    echo "  --- Generating Run $i (Condition F: no spec) ---"

    claude -p "Migrate this serverless application to be cloud-agnostic. Read the source code in $OLD_SYSTEM/ and produce a migrated version. Write ALL output files to $TARGET/. Make sure to actually create the files using your Write tool — do not just print them." --dangerously-skip-permissions 2>&1 | tail -5

    PY_COUNT=$(find "$TARGET" -name "*.py" | wc -l | tr -d ' ')
    echo "  Run $i complete. Python files created: $PY_COUNT"
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  DONE — Condition F runs generated."
echo "  Now run the tests:"
echo ""
echo "  for i in \$(seq 36 40); do"
echo "    dir=\"cases/case-2-serverless-todo/transformation/run-\$i\""
echo "    result=\$(TEST_SYSTEM_PATH=\"\$dir\" python3 -m pytest cases/case-2-serverless-todo/evidence/ -q --tb=no 2>&1 | tail -1)"
echo "    echo \"run-\$i | Condition F | \$result\""
echo "  done"
echo "═══════════════════════════════════════════════════════════════"
