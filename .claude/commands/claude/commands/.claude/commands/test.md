# Generate tests for the old system (Evidence — E)

Read these files first:
1. /spec/api_spec.md — the specification (S_n)
2. All code in /old-system/

Generate a test suite in /evidence/ that:

1. Tests every endpoint defined in the spec
2. Tests the behavior rules from the spec
3. Uses pytest and mocks for AWS services (moto)
4. Tests ONLY against the spec — not against implementation details

Save to /evidence/test_api.py, /evidence/conftest.py, /evidence/requirements.txt.

Critical rule: these tests must pass on BOTH P_n and P_n+1.
They test the SPECIFICATION, not the implementation.
That is the proof of semantic equivalence.

After generating, run:

python3 -m pytest evidence/ -v

All tests must pass on P_n before we proceed.

Stochastic: you generate the tests from the spec.
Deterministic: pytest runs them — pass or fail, no ambiguity.