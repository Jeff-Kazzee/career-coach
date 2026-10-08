# Weekly Career Review

## What this reference is for

Run a repeatable, evidence-based check-in that distinguishes effort from results, detects avoidance without shaming, and produces a realistic next week.

## When the agent should read it

Read this for Weekly Review Mode, monthly reviews, accountability requests, progress updates, or when the user supplies a career log or scorecard.

## Source links used

- NACE career-readiness competencies: https://www.naceweb.org/career-readiness/competencies/career-readiness-defined/
- CareerOneStop job-search planning: https://www.careeronestop.org/JobSearch/Plan/create-a-job-search-plan.aspx
- Agent Skills best practices, validation loops: https://agentskills.io/skill-creation/best-practices

Accessed 2026-06-23.

## The concrete process

### 1. Establish the review window

Use exact dates. Default to the last seven calendar days only when the user clearly means a weekly review. Compare against commitments made for that same window.

### 2. Capture facts before interpretation

Use `assets/weekly-career-log-template.md`. Collect:

- Wins
- Work shipped
- Applications sent
- Conversations started
- Interviews completed
- Skills practiced and practice outputs
- Portfolio or profile improvements
- Feedback received
- Commitments planned and completed
- Blockers
- Avoidance patterns
- Energy level and capacity changes
- Evidence of improvement

Do not treat “watched videos” as equivalent to practiced skill or shipped proof. It may still be useful input, but label it correctly.

### 3. Separate four kinds of signal

- **Inputs:** time, practice sessions, applications, outreach.
- **Outputs:** resume version, demo, article, work update, interview story bank.
- **Outcomes:** screens, interviews, paid work, expanded scope, positive feedback, offer.
- **Conditions:** health, energy, caregiving, platform outage, transportation, manager behavior, market changes.

Outcomes can lag. Do not punish good execution because an external result did not arrive in one week.

### 4. Compare commitments with completion

For every missed commitment, classify the cause:

- Too large or vague
- Lower priority than claimed
- Missing prerequisite
- External block
- Capacity mismatch
- Anxiety, perfectionism, or avoidance
- No longer strategically useful

Then change the system. Do not merely repeat the same commitment with stronger language.

### 5. Detect the active bottleneck

Use the current funnel stage:

- Search volume low because suitable roles are scarce: revisit target and market.
- Suitable roles found but applications stall: reduce tailoring burden or repair materials.
- Applications produce no screens: inspect fit, proof, resume, timing, and channel.
- Screens do not advance: practice pitch, requirements, logistics, and recruiter questions.
- Interviews do not convert: review stories, technical gaps, role fit, and questions.
- Work is strong but invisible: improve expectation alignment and visibility.

Avoid universal response-rate claims. Compare similar roles, channels, seniority, and time periods.

### 6. Update the scorecard carefully

Update a weekly score only when new evidence supports movement. Otherwise keep it unchanged. Unchanged is not a weakness, and a week of low output from a capacity change is not evidence that a score dropped.

For each changed dimension, record:

- Previous score
- Current score
- Evidence
- Confidence in the change: low, medium, or high

Run `scripts/scorecard.py` when the user has structured weekly JSON or CSV and trend analysis would reduce manual work.

### 7. Set next week's commitments

Default to three outcome-linked commitments. Plan more when the user asks, ranked so the lowest drop first in a short week. Plan at the capacity the user states. Each needs:

- Deliverable
- Definition of done
- Scheduled or bounded work session
- Dependency
- Measurement
- Minimum version for a low-capacity week

Capacity tiers:

- **Minimum:** protects continuity and produces one useful artifact.
- **Standard:** expected sustainable plan.
- **Stretch:** extra work for users who want more. Use it as the plan when the user asks for an intensive pace.

### 8. Give calibrated feedback

Include one hard truth only when the evidence shows a controllable mismatch or weak assumption. If there is none, say so in one line. Skip the section when the user opts out. It must never insult the user or blame them for a capacity change.

Good:

> You logged six hours of courses but produced no work sample. Learning is currently functioning as a substitute for proof.

Bad:

> You are not trying hard enough.

Encouragement must be tied to evidence:

> You completed two uncomfortable outreach conversations and captured what employers asked for. That is real market feedback you did not have last week.

## Weekly review output format

```markdown
# Review: YYYY-MM-DD to YYYY-MM-DD

## Progress summary
[What moved, stalled, or changed]

## Evidence of improvement
- [Evidence]

## Scorecard changes
| Dimension | Before | Now | Evidence | Confidence |
|---|---:|---:|---|---|

## Blockers and avoidance
[Cause classification and system change]

## Next commitments
1. [Deliverable, done condition, minimum version]
2. ...

## One hard truth
[Direct, evidence-based]

## One encouragement
[Grounded in demonstrated progress]
```
