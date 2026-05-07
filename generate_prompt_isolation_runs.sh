#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# Prompt Isolation Experiment — Generate runs for Conditions C, D, E
# ═══════════════════════════════════════════════════════════════════════════
#
# Purpose: Isolate which prompt element causes the Gate 1 performance
#          difference between detailed (50%) and vague (90%) prompts.
#
# Run structure:
#   Runs 21-25 = Condition C (positive constraints only, no "Do NOT")
#   Runs 26-30 = Condition D (negative constraints only, no target tech)
#   Runs 31-35 = Condition E (context only, mentions AWS but no constraints)
#
# Usage:
#   bash generate_prompt_isolation_runs.sh
#
# Prerequisites:
#   - Claude Code CLI (`claude` command available)
# ═══════════════════════════════════════════════════════════════════════════

set -e
cd "$(dirname "$0")"

RUNS_DIR="cases/case-2-serverless-todo/transformation"
OLD_SYSTEM="cases/case-2-serverless-todo/old-system"
SPEC="cases/case-2-serverless-todo/spec/api_spec.md"

COMMON_SUFFIX="Read the source code in $OLD_SYSTEM/ and the behavioral specification in $SPEC, then produce the migrated application. Write ALL output files to \$TARGET/. Make sure to actually create the files using your Write tool — do not just print them."

echo "═══════════════════════════════════════════════════════════════"
echo "  PROMPT ISOLATION EXPERIMENT — Run Generator"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ── Condition C: Positive constraints only (runs 21-25) ─────────────────

echo "Condition C: Positive constraints only (no negative constraints)"
echo "────────────────────────────────────────────────────────────────"
for i in $(seq 21 25); do
    TARGET="$RUNS_DIR/run-$i"
    if [ -d "$TARGET" ] && [ "$(find "$TARGET" -name '*.py' | wc -l | tr -d ' ')" -gt 0 ]; then
        echo "  Run $i already has Python files, skipping."
        continue
    fi
    [ -d "$TARGET" ] && rm -rf "$TARGET"
    mkdir -p "$TARGET"

    echo ""
    echo "  --- Generating Run $i (Condition C) ---"

    claude -p "Migrate this serverless application to a cloud-agnostic architecture. The target system must use Flask as the web framework and SQLite as the database. The migrated application must expose the same REST API endpoints and maintain the same behavior as the original.

Read the source code in $OLD_SYSTEM/ and the behavioral specification in $SPEC, then produce the migrated application. Write ALL output files to $TARGET/. Make sure to actually create the files using your Write tool — do not just print them." --dangerously-skip-permissions 2>&1 | tail -5

    PY_COUNT=$(find "$TARGET" -name "*.py" | wc -l | tr -d ' ')
    echo "  Run $i complete. Python files created: $PY_COUNT"
done

echo ""

# ── Condition D: Negative constraints only (runs 26-30) ─────────────────

echo "Condition D: Negative constraints only (no target technology)"
echo "────────────────────────────────────────────────────────────────"
for i in $(seq 26 30); do
    TARGET="$RUNS_DIR/run-$i"
    if [ -d "$TARGET" ] && [ "$(find "$TARGET" -name '*.py' | wc -l | tr -d ' ')" -gt 0 ]; then
        echo "  Run $i already has Python files, skipping."
        continue
    fi
    [ -d "$TARGET" ] && rm -rf "$TARGET"
    mkdir -p "$TARGET"

    echo ""
    echo "  --- Generating Run $i (Condition D) ---"

    claude -p "Migrate this serverless application to a cloud-agnostic architecture. Do NOT use boto3, botocore, moto, or any AWS SDK. Do NOT import any cloud-provider-specific libraries.

Read the source code in $OLD_SYSTEM/ and the behavioral specification in $SPEC, then produce the migrated application. Write ALL output files to $TARGET/. Make sure to actually create the files using your Write tool — do not just print them." --dangerously-skip-permissions 2>&1 | tail -5

    PY_COUNT=$(find "$TARGET" -name "*.py" | wc -l | tr -d ' ')
    echo "  Run $i complete. Python files created: $PY_COUNT"
done

echo ""

# ── Condition E: Context only (runs 31-35) ──────────────────────────────

echo "Condition E: Context only (mentions AWS, no constraints)"
echo "────────────────────────────────────────────────────────────────"
for i in $(seq 31 35); do
    TARGET="$RUNS_DIR/run-$i"
    if [ -d "$TARGET" ] && [ "$(find "$TARGET" -name '*.py' | wc -l | tr -d ' ')" -gt 0 ]; then
        echo "  Run $i already has Python files, skipping."
        continue
    fi
    [ -d "$TARGET" ] && rm -rf "$TARGET"
    mkdir -p "$TARGET"

    echo ""
    echo "  --- Generating Run $i (Condition E) ---"

    claude -p "You are migrating an AWS Lambda + DynamoDB serverless application to a cloud-agnostic architecture. Migrate the application to be cloud-agnostic.

Read the source code in $OLD_SYSTEM/ and the behavioral specification in $SPEC, then produce the migrated application. Write ALL output files to $TARGET/. Make sure to actually create the files using your Write tool — do not just print them." --dangerously-skip-permissions 2>&1 | tail -5

    PY_COUNT=$(find "$TARGET" -name "*.py" | wc -l | tr -d ' ')
    echo "  Run $i complete. Python files created: $PY_COUNT"
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  DONE — All prompt isolation runs generated."
echo "  Now run: bash run_reliability_tests.sh"
echo "═══════════════════════════════════════════════════════════════"
