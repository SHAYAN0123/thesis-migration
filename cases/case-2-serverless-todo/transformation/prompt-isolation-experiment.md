# Prompt Isolation Experiment — SRQ3 Extension

**Date:** 2026-05-07
**Purpose:** Isolate which specific prompt element causes the performance difference between Condition A (50% Gate 1 pass) and Condition B (90% Gate 1 pass).
**Motivation:** Industry supervisor feedback — "define it, isolate it"

---

## Background

The initial reliability evaluation (20 runs, 2 conditions) found that vague prompts outperform detailed prompts on Gate 1. The researcher's hypothesis: detailed prompts over-constrain the LLM, overriding its implicit knowledge of standard conventions.

Root-cause analysis confirmed that all 6 failures share one cause: the LLM chose `DATABASE_PATH` instead of `DB_PATH`, causing a test harness mismatch. The question is: **which element of the detailed prompt triggers this naming shift?**

---

## Prompt Decomposition

The detailed prompt (Condition A) contains 5 elements absent from the vague prompt (Condition B):

| # | Element | Type | Text |
|---|---------|------|------|
| 1 | Context statement | Informational | "You are migrating an AWS Lambda + DynamoDB serverless application" |
| 2 | Positive target constraint | Prescriptive | "must use Flask as the web framework and SQLite as the database" |
| 3 | Negative constraint #1 | Prohibitive | "Do NOT use boto3, botocore, moto, or any AWS SDK" |
| 4 | Negative constraint #2 | Prohibitive | "Do NOT import any cloud-provider-specific libraries" |
| 5 | Behavior preservation | Prescriptive | "must expose the same REST API endpoints and maintain the same behavior" |

---

## Existing Conditions (20 runs complete)

### Condition A — Detailed (runs 1-10)
```
You are migrating an AWS Lambda + DynamoDB serverless application to a cloud-agnostic architecture. The target system must use Flask as the web framework and SQLite as the database. Do NOT use boto3, botocore, moto, or any AWS SDK. Do NOT import any cloud-provider-specific libraries. The migrated application must expose the same REST API endpoints and maintain the same behavior as the original.

Read the source code in $OLD_SYSTEM/ and the behavioral specification in $SPEC, then produce the migrated application. Write ALL output files to $TARGET/. Make sure to actually create the files using your Write tool — do not just print them.
```
**Result:** 5/10 Gate 1 pass (50%)

### Condition B — Vague (runs 11-20)
```
Migrate this serverless application to be cloud-agnostic. Read the source code in $OLD_SYSTEM/ and produce a migrated version. Write ALL output files to $TARGET/. Make sure to actually create the files using your Write tool — do not just print them.
```
**Result:** 9/10 Gate 1 pass (90%)

---

## New Conditions (5 runs each, to be generated)

### Condition C — Positive constraints only (no negative constraints)
**Tests:** Does removing the "Do NOT" lines fix the failure rate?
**Elements included:** 2 (positive target), 5 (behavior preservation)
**Elements excluded:** 1 (context), 3 (negative #1), 4 (negative #2)
```
Migrate this serverless application to a cloud-agnostic architecture. The target system must use Flask as the web framework and SQLite as the database. The migrated application must expose the same REST API endpoints and maintain the same behavior as the original.

Read the source code in $OLD_SYSTEM/ and the behavioral specification in $SPEC, then produce the migrated application. Write ALL output files to $TARGET/. Make sure to actually create the files using your Write tool — do not just print them.
```

### Condition D — Negative constraints only (no target technology)
**Tests:** Do the "Do NOT" lines alone cause the naming shift?
**Elements included:** 3 (negative #1), 4 (negative #2)
**Elements excluded:** 1 (context), 2 (positive target), 5 (behavior preservation)
```
Migrate this serverless application to a cloud-agnostic architecture. Do NOT use boto3, botocore, moto, or any AWS SDK. Do NOT import any cloud-provider-specific libraries.

Read the source code in $OLD_SYSTEM/ and the behavioral specification in $SPEC, then produce the migrated application. Write ALL output files to $TARGET/. Make sure to actually create the files using your Write tool — do not just print them.
```

### Condition E — Context only (mentions source tech, no constraints)
**Tests:** Does mentioning "AWS Lambda + DynamoDB" alone change behavior?
**Elements included:** 1 (context)
**Elements excluded:** 2 (positive target), 3 (negative #1), 4 (negative #2), 5 (behavior preservation)
```
You are migrating an AWS Lambda + DynamoDB serverless application to a cloud-agnostic architecture. Migrate the application to be cloud-agnostic.

Read the source code in $OLD_SYSTEM/ and the behavioral specification in $SPEC, then produce the migrated application. Write ALL output files to $TARGET/. Make sure to actually create the files using your Write tool — do not just print them.
```

---

## Expected Outcomes (Predictions)

| Condition | Prediction | Reasoning |
|-----------|------------|-----------|
| C (positive only) | ~80-90% pass | Without negative constraints, LLM defaults to standard naming |
| D (negative only) | ~40-60% pass | Negative constraints trigger generic naming (DATABASE_PATH) |
| E (context only) | ~80-90% pass | Context alone shouldn't override naming conventions |

If C passes high and D fails low → **negative constraints are the isolated cause**.
If C also fails → positive constraints (prescribing Flask/SQLite) also contribute.
If E fails → merely mentioning AWS triggers avoidance behavior.

---

## Run Structure

| Runs | Condition | Description |
|------|-----------|-------------|
| 1-10 | A (detailed) | Already complete |
| 11-20 | B (vague) | Already complete |
| 21-25 | C (positive only) | To be generated |
| 26-30 | D (negative only) | To be generated |
| 31-35 | E (context only) | To be generated |

**Total:** 35 runs across 5 conditions

---

## Results

### Test Results (all 35 runs)

| Run | Condition | Tests Passed | Tests Failed | Gate 1 | Env Var Used |
|-----|-----------|-------------|-------------|--------|-------------|
| 1-10 | A (detailed) | see reliability-results.md | | 5/10 (50%) | 5x DB_PATH, 5x DATABASE_PATH |
| 11-20 | B (vague) | see reliability-results.md | | 9/10 (90%) | 9x DB_PATH, 1x DATABASE_PATH |
| 21 | C (positive only) | 43 | 0 | PASS | DB_PATH |
| 22 | C (positive only) | 43 | 0 | PASS | DB_PATH |
| 23 | C (positive only) | 43 | 0 | PASS | DB_PATH |
| 24 | C (positive only) | 42 | 1 | FAIL | DATABASE |
| 25 | C (positive only) | 43 | 0 | PASS | DB_PATH |
| 26 | D (negative only) | 43 | 0 | PASS | DB_PATH |
| 27 | D (negative only) | 43 | 0 | PASS | DB_PATH |
| 28 | D (negative only) | 43 | 0 | PASS | DB_PATH |
| 29 | D (negative only) | 43 | 0 | PASS | DB_PATH |
| 30 | D (negative only) | 43 | 0 | PASS | DB_PATH |
| 31 | E (context only) | 43 | 0 | PASS | DB_PATH |
| 32 | E (context only) | 43 | 0 | PASS | DB_PATH |
| 33 | E (context only) | 43 | 0 | PASS | DB_PATH |
| 34 | E (context only) | 43 | 0 | PASS | DB_PATH |
| 35 | E (context only) | 43 | 0 | PASS | DB_PATH |

### Aggregate Pass Rates

| Condition | Description | Gate 1 Pass Rate |
|-----------|-------------|-----------------|
| A (detailed) | All elements combined | 5/10 (50%) |
| B (vague) | Minimal prompt | 9/10 (90%) |
| C (positive only) | "Use Flask/SQLite" — no "Do NOT" | 4/5 (80%) |
| D (negative only) | "Do NOT use boto3/AWS" — no target tech | 5/5 (100%) |
| E (context only) | Mentions AWS Lambda+DynamoDB | 5/5 (100%) |

### Predictions vs Actuals

| Condition | Predicted | Actual | Match? |
|-----------|-----------|--------|--------|
| C | ~80-90% pass | 80% (4/5) | Yes |
| D | ~40-60% pass | 100% (5/5) | No — better than expected |
| E | ~80-90% pass | 100% (5/5) | Yes — at high end |

---

## Key Finding

**No single prompt element causes the failure.** The negative constraints alone (D: 100%), positive constraints alone (C: 80%), and context alone (E: 100%) all perform well. Only when all elements are combined (A: 50%) does the failure rate spike.

This is a **prompt complexity interaction effect**: stacking multiple constraint types (positive + negative + context + behavioral) in a single prompt causes the LLM to deviate from its default conventions. The deviation manifests as non-standard naming choices (DATABASE_PATH instead of DB_PATH) that break compatibility with the test harness.

### Implications

1. **Prompt complexity, not prompt content, drives failure.** No individual constraint is harmful — it's the accumulation that overrides the LLM's implicit knowledge of standard conventions.
2. **Simpler prompts produce more convention-conforming code.** The LLM's training-data knowledge of Flask/SQLite conventions (DB_PATH, modular structure, sqlite3.Row) is more reliable than explicit instruction.
3. **Negative constraints are not the sole cause** (D refutes this), but they contribute when combined with other elements.
4. **The feedback/repair loop compensates for prompt complexity effects** — when the LLM deviates, test feedback corrects the mismatch.

---

## Status

- [x] Generate Condition C runs (21-25)
- [x] Generate Condition D runs (26-30)
- [x] Generate Condition E runs (31-35)
- [x] Run tests on all 15 new runs
- [x] Analyze results
- [x] Document findings
