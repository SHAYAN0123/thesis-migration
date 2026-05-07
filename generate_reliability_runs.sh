#!/bin/bash
# Generate additional reliability runs for SRQ3 evaluation.
# Uses Claude Code CLI to migrate the serverless todo app.
#
# Run structure:
#   run-1  to run-10  = Condition A (detailed prompt)
#   run-11 to run-20  = Condition B (vague prompt)
#
# Existing: runs 1-3 (original Condition A), runs 11-13 (original Condition B, renumbered)
# Generates: runs 4-10 (new Condition A) and runs 14-20 (new Condition B)

set -e
cd "$(dirname "$0")"

RUNS_DIR="cases/case-2-serverless-todo/transformation"
OLD_SYSTEM="cases/case-2-serverless-todo/old-system"
SPEC="cases/case-2-serverless-todo/spec/api_spec.md"

echo "============================================"
echo "  SRQ3 Reliability Run Generator"
echo "============================================"
echo ""

# Step 1: Reorganize existing Condition B runs (only if not already done)
echo "Step 1: Checking run organization..."
if [ -d "$RUNS_DIR/run-4" ] && [ ! -d "$RUNS_DIR/run-11" ]; then
    echo "  Moving run-4 → run-11 (Condition B)"
    mv "$RUNS_DIR/run-4" "$RUNS_DIR/run-11"
fi
if [ -d "$RUNS_DIR/run-5" ] && [ ! -d "$RUNS_DIR/run-12" ]; then
    echo "  Moving run-5 → run-12 (Condition B)"
    mv "$RUNS_DIR/run-5" "$RUNS_DIR/run-12"
fi
if [ -d "$RUNS_DIR/run-6" ] && [ ! -d "$RUNS_DIR/run-13" ]; then
    echo "  Moving run-6 → run-13 (Condition B)"
    mv "$RUNS_DIR/run-6" "$RUNS_DIR/run-13"
fi
echo "  Done."
echo ""

# Step 2: Generate Condition A runs (4-10)
echo "Step 2: Generating Condition A runs (detailed prompt)..."
for i in $(seq 4 10); do
    TARGET="$RUNS_DIR/run-$i"
    if [ -d "$TARGET" ] && [ "$(find "$TARGET" -name '*.py' | wc -l | tr -d ' ')" -gt 0 ]; then
        echo "  Run $i already has Python files, skipping."
        continue
    fi
    # Clean up empty dir if it exists
    [ -d "$TARGET" ] && rm -rf "$TARGET"
    mkdir -p "$TARGET"

    echo ""
    echo "  --- Generating Run $i (Condition A) ---"

    claude -p "You are migrating an AWS Lambda + DynamoDB serverless application to a cloud-agnostic architecture. The target system must use Flask as the web framework and SQLite as the database. Do NOT use boto3, botocore, moto, or any AWS SDK. Do NOT import any cloud-provider-specific libraries. The migrated application must expose the same REST API endpoints and maintain the same behavior as the original.

Read the source code in $OLD_SYSTEM/ and the behavioral specification in $SPEC, then produce the migrated application. Write ALL output files to $TARGET/. Make sure to actually create the files using your Write tool — do not just print them." --dangerously-skip-permissions 2>&1 | tail -5

    # Verify something was created
    PY_COUNT=$(find "$TARGET" -name "*.py" | wc -l | tr -d ' ')
    echo "  Run $i complete. Python files created: $PY_COUNT"
done
echo ""

# Step 3: Generate Condition B runs (14-20)
echo "Step 3: Generating Condition B runs (vague prompt)..."
for i in $(seq 14 20); do
    TARGET="$RUNS_DIR/run-$i"
    if [ -d "$TARGET" ] && [ "$(find "$TARGET" -name '*.py' | wc -l | tr -d ' ')" -gt 0 ]; then
        echo "  Run $i already has Python files, skipping."
        continue
    fi
    # Clean up empty dir if it exists
    [ -d "$TARGET" ] && rm -rf "$TARGET"
    mkdir -p "$TARGET"

    echo ""
    echo "  --- Generating Run $i (Condition B) ---"

    claude -p "Migrate this serverless application to be cloud-agnostic. Read the source code in $OLD_SYSTEM/ and produce a migrated version. Write ALL output files to $TARGET/. Make sure to actually create the files using your Write tool — do not just print them." --dangerously-skip-permissions 2>&1 | tail -5

    PY_COUNT=$(find "$TARGET" -name "*.py" | wc -l | tr -d ' ')
    echo "  Run $i complete. Python files created: $PY_COUNT"
done

echo ""
echo "============================================"
echo "  DONE — Run generation complete."
echo "  Now run: bash run_reliability_tests.sh"
echo "============================================"
