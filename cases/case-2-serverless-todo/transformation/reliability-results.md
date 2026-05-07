# Reliability Evaluation Results — SRQ3

**Date:** 2026-05-06
**Application:** Case Study 2 — Serverless Todo API
**Runs:** 20 (Runs 1–10 = Condition A, Runs 11–20 = Condition B)
**Test suite:** 43 spec-driven tests from `cases/case-2-serverless-todo/evidence/test_api.py`
**Analyzer:** `analyzer.py` v2 (4-layer detection: imports, manifests, config, source strings)

---

## Condition A: Detailed Prompt (Runs 1–10)

Prompt specifies: SQLite, Flask, explicit constraints (no boto3, no AWS).

## Condition B: Vague Prompt (Runs 11–20)

Prompt specifies only: "migrate this to be cloud-agnostic."

---

## Summary Table

| Run | Condition | Py Files | Functions | Cloud Deps (4-layer) | Config Scanned | Tests Passed | Tests Failed | Gate 1 | Gate 2 |
|-----|-----------|----------|-----------|----------------------|----------------|-------------|-------------|--------|--------|
| 1 | A (detailed) | 1 | 7 | 0 | 0 | 43 | 0 | PASS | PASS |
| 2 | A (detailed) | 1 | 9 | 0 | 1 | 43 | 0 | PASS | PASS |
| 3 | A (detailed) | 1 | 8 | 0 | 0 | 43 | 0 | PASS | PASS |
| 4 | A (detailed) | 3 | 13 | 0 | 0 | 42 | 1 | FAIL | PASS |
| 5 | A (detailed) | 2 | 9 | 0 | 0 | 42 | 1 | FAIL | PASS |
| 6 | A (detailed) | 2 | 9 | 0 | 0 | 42 | 1 | FAIL | PASS |
| 7 | A (detailed) | 2 | 14 | 0 | 0 | 42 | 1 | FAIL | PASS |
| 8 | A (detailed) | 2 | 9 | 0 | 0 | 42 | 1 | FAIL | PASS |
| 9 | A (detailed) | 2 | 9 | 0 | 0 | 43 | 0 | PASS | PASS |
| 10 | A (detailed) | 2 | 13 | 0 | 0 | 43 | 0 | PASS | PASS |
| 11 | B (vague) | 3 | 14 | 0 | 0 | 43 | 0 | PASS | PASS |
| 12 | B (vague) | 3 | 14 | 0 | 0 | 43 | 0 | PASS | PASS |
| 13 | B (vague) | 3 | 14 | 0 | 0 | 43 | 0 | PASS | PASS |
| 14 | B (vague) | 3 | 13 | 0 | 0 | 43 | 0 | PASS | PASS |
| 15 | B (vague) | 3 | 13 | 0 | 0 | 43 | 0 | PASS | PASS |
| 16 | B (vague) | 3 | 14 | 0 | 0 | 43 | 0 | PASS | PASS |
| 17 | B (vague) | 3 | 13 | 0 | 0 | 42 | 1 | FAIL | PASS |
| 18 | B (vague) | 3 | 13 | 0 | 0 | 43 | 0 | PASS | PASS |
| 19 | B (vague) | 3 | 14 | 0 | 0 | 43 | 0 | PASS | PASS |
| 20 | B (vague) | 3 | 13 | 0 | 0 | 43 | 0 | PASS | PASS |

---

## Aggregate Statistics

| Condition | Runs | Gate 1 Pass Rate | Gate 2 Pass Rate |
|-----------|------|-----------------|-----------------|
| A (detailed) | 10 | 5/10 (50%) | 10/10 (100%) |
| B (vague) | 10 | 9/10 (90%) | 10/10 (100%) |
| **Total** | **20** | **14/20** | **20/20** |

---

## Architectural Variation

| Run | Condition | Structure | Timestamp Method | DB Helper Pattern |
|-----|-----------|-----------|-----------------|-------------------|
| 1 | A | Monolithic (1 file) | time.time() | Connection helper function |
| 2 | A | Monolithic (1 file) | datetime | Connection helper function |
| 3 | A | Monolithic (1 file) | time.time() | Connection helper function |
| 4 | A | Modular (3 files) | time.time() | Connection helper function |
| 5 | A | Modular (2 files) | time.time() | Connection helper function |
| 6 | A | Modular (2 files) | time.time() | Connection helper function |
| 7 | A | Modular (2 files) | time.time() | Connection helper function |
| 8 | A | Modular (2 files) | time.time() | Connection helper function |
| 9 | A | Modular (2 files) | time.time() | Connection helper function |
| 10 | A | Modular (2 files) | time.time() | Connection helper function |
| 11 | B | Modular (3 files) | time.time() | Connection helper function |
| 12 | B | Modular (3 files) | time.time() | Connection helper function |
| 13 | B | Modular (3 files) | datetime | Connection helper function |
| 14 | B | Modular (3 files) | time.time() | Connection helper function |
| 15 | B | Modular (3 files) | time.time() | Connection helper function |
| 16 | B | Modular (3 files) | datetime | Connection helper function |
| 17 | B | Modular (3 files) | time.time() | Connection helper function |
| 18 | B | Modular (3 files) | time.time() | Connection helper function |
| 19 | B | Modular (3 files) | datetime | Connection helper function |
| 20 | B | Modular (3 files) | time.time() | Connection helper function |

---

## Interpretation

*To be completed after reviewing results.*
