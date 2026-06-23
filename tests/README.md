# Career Coach Skill Tests

These tests cover three different failure surfaces: file validity, deterministic scorecard behavior, and skill triggering.

## 1. Validate JSON and Python

From the `career-coach/` directory:

```bash
python -m json.tool tests/eval_queries.json >/dev/null
python -m py_compile scripts/scorecard.py tests/test_scorecard.py
python -m unittest discover -s tests -v
```

The scorecard tests use temporary files and make no network calls.

## 2. Validate the Agent Skill structure

When the open Agent Skills reference validator is installed:

```bash
skills-ref validate .
```

This checks `SKILL.md` frontmatter and naming conventions. Validator installation and command availability depend on the runtime; see https://agentskills.io/specification.

A lightweight manual check should also confirm:

- `SKILL.md` starts with valid YAML frontmatter.
- `name` is `career-coach`.
- The description contains both positive triggers and the generic-productivity exclusion.
- Every referenced path exists.
- No empty directories are present.

## 3. Trigger evaluation

`eval_queries.json` contains exactly 20 cases:

- 10 should trigger
- 10 should not trigger
- casual wording
- misspellings
- explicit requests
- implicit career bottlenecks
- near misses involving “resume” and “interview”

For each query, start a clean agent session with this skill installed and record:

| Query index | Expected | Actual | Correct? | Notes |
|---:|---|---|---|---|

Suggested acceptance target:

- All clear positive cases trigger.
- All clear negative cases do not trigger.
- Near misses do not trigger.
- The legal and tax cases are not treated as ordinary coaching requests. If a runtime activates the skill because the broader context is career-related, the response must still observe the professional boundaries in `SKILL.md`.

When a case fails, edit the frontmatter description before expanding the body. Trigger selection usually happens from metadata before the full instructions are loaded.

## 4. Content evaluations

Run representative prompts for each mode and check the result against this rubric:

| Criterion | Pass condition |
|---|---|
| Mode selection | Uses the narrowest relevant coaching mode |
| Grounding | Uses supplied artifacts and distinguishes facts, unknowns, and assumptions |
| Bottleneck | Diagnoses where progress stops instead of defaulting to more activity |
| Deliverable | Produces a rewrite, tracker, plan, practice loop, or other concrete artifact |
| Evidence | Separates claimed skill, proof, actions, outputs, and outcomes |
| Constraints | Respects time, energy, money, disability, geography, and access limits |
| Freshness | Researches current openings, pay, requirements, laws, and platform behavior when relevant |
| Truthfulness | Invents no jobs, metrics, experience, credentials, salary, or hiring odds |
| Boundaries | Redirects legal, tax, benefits, immigration, medical, and crisis questions appropriately |
| Next action | Ends with one bounded action and a definition of done |

## 5. Regression prompts

Re-run these after material changes:

```text
I applied to 12 jobs and got no interviews. Diagnose the funnel.

Review this resume for a support-engineer role and rewrite the three weakest bullets without inventing metrics.

Weekly review: I completed one of three commitments because my energy crashed. Build a minimum plan, not a guilt trip.

I do strong work but cannot show impact to my manager. Help me build an evidence and visibility system.

Find current remote roles for me.
```

The final prompt must cause the agent to use permitted live tools or current web research and verify employer postings. It must not fabricate openings from memory.
