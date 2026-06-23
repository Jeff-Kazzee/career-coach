# Career Coach Agent Instructions

This repository is a public, reusable career-coaching agent skill. Keep private user career data out of the repo.

## Branches

- `prod` is the public stable branch.
- `dev` is active development.
- Use short-lived feature branches off `dev` only for larger blocks of work.

## Tests

Plan the verification gate before editing. For this repo, the default gate is:

```bash
python -m json.tool tests/eval_queries.json > NUL
python -m py_compile scripts/scorecard.py tests/test_scorecard.py
python -m unittest discover -s tests -v
```

Use the platform equivalent of `NUL` when not on Windows.

## Privacy

Do not commit:

- Personal career logs
- Resumes with private contact details
- Employer, client, legal, tax, immigration, medical, benefits, or compensation records
- Job applications, recruiter messages, or interview notes tied to real people
- Secrets or private links

Use examples with synthetic data only.

## Editing Principles

- Preserve the evidence-first coaching stance.
- Prefer concrete deliverables over vague advice.
- Do not weaken the legal, tax, medical, immigration, benefits, discrimination, crisis, privacy, scam, or truthfulness boundaries.
- When adding a new mode, add a reference file, update `SKILL.md`, and add at least one trigger or regression example.
