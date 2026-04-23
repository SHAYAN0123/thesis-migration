# Verify semantic equivalence (S_n satisfied by both P_n and P_n+1)

Run the deterministic tools first:

python3 analyzer.py old-system --json
python3 analyzer.py new-system --json
python3 -m pytest evidence/ -v
TEST_SYSTEM_PATH=new-system python3 -m pytest evidence/ -v

These four commands give you the facts. Now interpret them.

Produce a verification report in /analysis/verification-report.md:

1. **Structural comparison** — from analyzer (deterministic): files, functions, classes in old vs new
2. **Cloud dependencies removed** — from analyzer (deterministic): what was removed, what replaced it
3. **Cloud dependencies remaining** — from analyzer (deterministic): any lock-in left?
4. **Test results** — from pytest (deterministic): pass/fail rates on both systems
5. **Sovereignty compliance** — check new-system against the 7 themes:
   - Jurisdiction, Localisation, Autonomy, Lock-in Avoidance, Supply-Chain Control, Openness, Sustainability
6. **Pattern compliance** — were the patterns from /transformation/patterns.md followed correctly?
7. **Semantic equivalence verdict** — same spec, same tests, same behavior?
8. **Honest limitations** — what doesn't this prove? What could still be wrong?

The deterministic tools provide the evidence.
You provide the verdict and honest assessment.
Stochastic for interpretation. Deterministic for proof.