# Inter-Rater Validation Package — Gate 3 Sovereignty Assessment

## Purpose

This package enables independent assessors to evaluate whether a migrated system satisfies EU digital sovereignty requirements, using the same rubric the researcher used. By comparing assessments, we can measure inter-rater reliability (Cohen's kappa) and strengthen the validity of Gate 3.

## What You Need

1. **The rubric** (`sovereignty_rubric.md`) — read this first
2. **The system to assess** (`case-2-system/`) — a Flask+SQLite Todo API migrated from AWS Lambda+DynamoDB
3. **The assessment form** (`assessment_form.md`) — fill this out independently
4. **The original system** (`old-system-reference/`) — for context only (optional)

## Instructions

1. Read `sovereignty_rubric.md` carefully (10 min)
2. Examine the migrated system in `case-2-system/` — read the Python source files
3. Optionally, look at the analyzer output in `analyzer_output.txt`
4. For each of the 7 sovereignty themes, fill in the assessment form:
   - Record what evidence you observed
   - Assign a verdict (PASS / PARTIAL / FAIL) using the decision rules
5. Do NOT discuss your assessment with other assessors until all forms are submitted
6. Return your completed form to Shayan (mshayan@schubergphilis.com)

## Important

- Assess the **migrated system only** (not the original)
- Use **only the rubric criteria** — don't invent additional requirements
- If uncertain, note your uncertainty in the evidence column
- Time estimate: 20-30 minutes

## Assessors

- [ ] Ilja (industry supervisor)
- [ ] Bernard
- [ ] Raymond
- [ ] Leo
- [ ] Shayan (researcher — completed separately)
