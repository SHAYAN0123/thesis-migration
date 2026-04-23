# Architecture — The Mix of Stochastic and Deterministic

## Core Principle
Stochastic (LLM) for generation. Deterministic (analyzer + tests) for
evaluation and quality control. Never trust the LLM output without
deterministic verification.

---

## What Is Stochastic (LLM — Claude Code)

The LLM generates things that require reasoning, creativity, and
understanding of intent. These are non-deterministic — running the
same command twice may produce different code.

| Step | What the LLM does | Command |
|------|-------------------|---------|
| Analyse | Reads code + spec, classifies lock-in types, assesses sovereignty risk, judges migration complexity | /analyse |
| Test | Reads spec, generates pytest test suite that covers all endpoints and behavior rules | /test |
| Transform | Reads spec + lock-in report + old code, generates new cloud-agnostic implementation | /transform |
| Verify | Reads both analyses, interprets test results, writes verification report with honest assessment | /verify |

**What makes it stochastic:**
- The generated code could be different each run
- The LLM makes judgment calls (e.g., "use SQLite" vs "use PostgreSQL")
- The analysis involves interpretation (e.g., "this is Hard complexity")
- The report involves reasoning about sovereignty compliance

---

## What Is Deterministic (Analyzer + Tests)

The deterministic layer produces the same output every time for the
same input. No reasoning, no judgment — just facts.

| Tool | What it does | When it runs |
|------|-------------|--------------|
| analyzer.py | Counts files, classes, functions, imports, cloud dependencies using AST parsing | Before and after migration |
| pytest (evidence/) | Runs 39 spec-driven tests against any system | After test generation, after transformation |
| diff | Compares files byte-for-byte | After transformation (app.py must be identical) |
| git (gh) | Tracks every change in small commits | After every step |

**What makes it deterministic:**
- analyzer.py uses Python's AST parser — same code always gives same count
- Tests either pass or fail — no ambiguity
- diff is binary — files are identical or they're not
- Git commits are immutable records

---

## How They Work Together

Step 1: ANALYSE
LLM (stochastic)  → reads code, produces lock-in report
Analyzer (determ.) → provides file/function/dependency counts as ground truth
LLM uses analyzer output as source of truth, adds reasoning on top
Step 2: TEST
LLM (stochastic)  → generates test suite from spec
Tests (determ.)    → run against P_n, must all pass
If tests fail → LLM got the test wrong, fix it (iterate)
Step 3: TRANSFORM
LLM (stochastic)  → generates P_n+1 (new cloud-agnostic code)
Tests (determ.)    → run against P_n+1, must all pass
Analyzer (determ.) → confirms cloud dependencies are gone
If tests fail → LLM got the transformation wrong, fix it (iterate)
Step 4: VERIFY
Analyzer (determ.) → compares old vs new (structural diff)
Tests (determ.)    → confirms both systems pass same tests
LLM (stochastic)   → interprets results, writes human-readable report

---

## The Trust Model

| Output | Trust level | Why |
|--------|------------|-----|
| Analyzer counts | HIGH — deterministic, AST-based | Same code = same result every time |
| Test pass/fail | HIGH — deterministic, automated | Binary outcome, no interpretation |
| LLM-generated code | LOW until verified | Could have bugs, wrong assumptions |
| LLM-generated analysis | MEDIUM | Grounded in analyzer data, but interpretation is stochastic |
| LLM-generated report | MEDIUM | Summarizes deterministic results, but framing is stochastic |

**Key insight:** We never trust LLM output alone. Every stochastic output
is checked by a deterministic tool before it's accepted.

- LLM generates code → tests verify it works
- LLM claims dependencies removed → analyzer confirms it
- LLM says systems are equivalent → test pass rates prove it

---

## ISPE Mapping

| ISPE | Stochastic or Deterministic | Tool |
|------|---------------------------|------|
| I (Intent) | Human | The researcher defines the goal |
| S (Specification) | Human + LLM review | Written by hand, LLM validates against it |
| P (Program) | Stochastic (LLM generates) | Claude Code /transform |
| E (Evidence) | Stochastic generation, Deterministic execution | LLM writes tests, pytest runs them |

Sovereignty = moving P_n to P_n+1 under same S_n.
The specification is the constant. The program changes. The evidence proves both satisfy the spec.