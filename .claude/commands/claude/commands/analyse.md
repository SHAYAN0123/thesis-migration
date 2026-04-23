# Analyse the old system (P_n)

Read these files first:
1. /spec/api_spec.md — the specification
2. /spec/sovereignty_themes.md — the 7 EU sovereignty themes
3. /transformation/patterns.md — known transformation patterns

Run the deterministic analyzer:

python3 analyzer.py old-system --json

Using the analyzer output (deterministic — source of truth) AND your own
reading of the code (stochastic — reasoning), produce a report in
/analysis/lock-in-report.md that contains:

1. **Cloud dependencies found** — from analyzer output (deterministic)
2. **Lock-in classification** — your assessment: API-level, service-level, data-level (stochastic)
3. **Sovereignty risk** — check against the 7 themes (deterministic checklist)
4. **Pattern match** — does each dependency match a known pattern from patterns.md? (deterministic lookup)
5. **Migration complexity** — your judgment: easy/medium/hard (stochastic)
6. **Summary** — total lock-in points, overall risk

The analyzer provides the facts. You provide the interpretation.
Stochastic for analysis. Deterministic for ground truth.