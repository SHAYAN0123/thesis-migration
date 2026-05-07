# Gate 3 Sovereignty Assessment Form

**Assessor name:** ___________________
**Date:** ___________________
**System assessed:** Case Study 2 — Todo API (Flask + SQLite)

---

## Instructions

For each theme, examine the migrated system's source code and record:
1. What evidence you found
2. Your verdict (PASS / PARTIAL / FAIL) based on the decision rules in the rubric

---

## Theme 1: Jurisdiction

**Criterion:** No dependencies on services governed by non-EU law.

| Question | Your Finding |
|----------|-------------|
| Does the code make any runtime network calls to external services? | |
| Are there any hard-coded API endpoints pointing to non-EU providers? | |
| If external endpoints exist, are they configurable? | |

**Verdict:** [ ] PASS  [ ] PARTIAL  [ ] FAIL

**Notes/Uncertainty:**


---

## Theme 2: Data Localisation

**Criterion:** All data storable within EU borders.

| Question | Your Finding |
|----------|-------------|
| What data persistence mechanisms are used? | |
| Are there hard-coded cloud regions or storage endpoints? | |
| Is storage location environment-configurable? | |

**Verdict:** [ ] PASS  [ ] PARTIAL  [ ] FAIL

**Notes/Uncertainty:**


---

## Theme 3: Operational Autonomy

**Criterion:** Operable without a single cloud vendor's control plane.

| Question | Your Finding |
|----------|-------------|
| Can the system start without connecting to any cloud provider API? | |
| Does deployment require a vendor-specific CLI or control plane? | |
| What are the runtime dependencies? Are any vendor-operated? | |

**Verdict:** [ ] PASS  [ ] PARTIAL  [ ] FAIL

**Notes/Uncertainty:**


---

## Theme 4: Lock-in Avoidance

**Criterion:** No vendor-specific APIs, no proprietary data formats.

| Question | Your Finding |
|----------|-------------|
| Does the analyzer report 0 cloud dependencies? (see analyzer_output.txt) | |
| What data storage format is used? Is it standard? | |
| What API interface is used? Is it standard HTTP/REST? | |

**Verdict:** [ ] PASS  [ ] PARTIAL  [ ] FAIL

**Notes/Uncertainty:**


---

## Theme 5: Supply-Chain Control

**Criterion:** No single vendor controls the stack. Dependencies are replaceable.

| Question | Your Finding |
|----------|-------------|
| List all runtime dependencies (from requirements.txt or imports): | |
| Are they all open-source? | |
| Does any single vendor control 3+ of these dependencies? | |
| Is there an alternative for each dependency? | |

**Verdict:** [ ] PASS  [ ] PARTIAL  [ ] FAIL

**Notes/Uncertainty:**


---

## Theme 6: Openness & Standards

**Criterion:** Open standards and protocols throughout.

| Question | Your Finding |
|----------|-------------|
| Communication protocols used: | |
| Data exchange formats used: | |
| Database interfaces used: | |
| Are all of the above open standards? | |

**Verdict:** [ ] PASS  [ ] PARTIAL  [ ] FAIL

**Notes/Uncertainty:**


---

## Theme 7: Sustainability

**Criterion:** Maintainable and portable long-term without vendor cooperation.

| Question | Your Finding |
|----------|-------------|
| Can the system be built from source with standard tools? | |
| Are all dependencies on public package registries (PyPI)? | |
| Is there a risk of vendor-controlled deprecation for any dependency? | |
| Could a different team maintain this without vendor support? | |

**Verdict:** [ ] PASS  [ ] PARTIAL  [ ] FAIL

**Notes/Uncertainty:**


---

## Summary

| Theme | Verdict |
|-------|---------|
| 1. Jurisdiction | |
| 2. Data Localisation | |
| 3. Operational Autonomy | |
| 4. Lock-in Avoidance | |
| 5. Supply-Chain Control | |
| 6. Openness & Standards | |
| 7. Sustainability | |

**Overall Gate 3 Verdict:** [ ] PASS  [ ] FAIL

**Additional comments:**


