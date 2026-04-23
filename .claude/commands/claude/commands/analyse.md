# Analyse the old system (P_n)

Read the specification in /spec/api_spec.md.
Then analyse every file in /old-system/.

Run the deterministic analyzer first:

python3 analyzer.py old-system --json

Using the analyzer output AND your own reading of the code, produce a report in /analysis/lock-in-report.md that contains:

1. **Cloud dependencies found** — which files, which imports, which AWS service
2. **Lock-in classification** — for each dependency, what type of lock-in (API-level, service-level, data-level)
3. **Sovereignty risk** — which of the 7 sovereignty themes each dependency violates
4. **Migration complexity** — easy/medium/hard for each dependency to replace
5. **Summary** — total lock-in points, overall risk assessment

Be precise. Use the deterministic analyzer output as the source of truth for what exists in the code.