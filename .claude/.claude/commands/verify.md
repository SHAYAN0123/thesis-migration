# Verify semantic equivalence (S_n satisfied by both P_n and P_n+1)

Run the deterministic analyzer on both systems:

python3 analyzer.py old-system --json
python3 analyzer.py new-system --json

Then produce a verification report in /analysis/verification-report.md:

1. **Structural comparison** — files, functions, classes in old vs new
2. **Cloud dependencies removed** — what was removed, what replaced it
3. **Cloud dependencies remaining** — any lock-in still present in new-system?
4. **Test results** — run tests against both systems, report pass/fail rates
5. **Sovereignty compliance** — check new-system against the 7 themes:
   - Jurisdiction: no dependency on non-EU cloud provider APIs?
   - Localisation: data stays local?
   - Autonomy: can operate independently?
   - Lock-in Avoidance: no vendor-specific APIs?
   - Supply-Chain Control: no single vendor dependency?
   - Openness: uses open standards?
   - Sustainability: portable and maintainable?
6. **Semantic equivalence verdict** — same spec, same tests, same behavior?

Be honest about what passes and what doesn't.