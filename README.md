# Career Coach

Career Coach is an evidence-first agent skill and Obsidian-friendly career operating system.

It is built for people who want practical career help without motivational fog: diagnose the bottleneck, produce the artifact, track evidence, and adjust the plan when reality answers back.

## What It Helps With

- Career baselines and direction changes
- Job-search funnel diagnosis
- Resume, LinkedIn, GitHub, portfolio, and personal-site review
- Interview preparation and practice loops
- Work performance, visibility, promotion, and raise planning
- Skill-gap and proof-gap analysis
- Freelance, consulting, creator, apprenticeship, and open-source paths
- Weekly career reviews with evidence and next actions

## What Is Inside

- `SKILL.md` - the main agent skill instructions
- `references/` - mode-specific coaching playbooks
- `assets/` - reusable Markdown and CSV templates
- `scripts/scorecard.py` - standard-library scorecard trend summary tool
- `tests/` - deterministic checks for the scorecard script and trigger cases
- `docs/obsidian-workflow.md` - a private-vault workflow for using this as a career cockpit

## Quick Start

### Use It As An Agent Skill

Copy or symlink this folder into the skills directory for your agent runtime, then ask for career-specific help:

```text
Use the career-coach skill. I applied to 12 jobs and got no interviews. Diagnose the funnel and give me one next action.
```

Different runtimes install skills differently. The important part is that the runtime can see `SKILL.md`, `references/`, and `assets/` together.

### Use It With Obsidian

Create a private Career Coach folder inside your Obsidian vault and copy the templates you want from `assets/`.

Suggested private structure:

```text
Career Coach/
  README.md
  Career Intake.md
  Career Scorecard.md
  Weekly Logs/
  Applications/
  Interviews/
  Proof Inventory.md
  Performance Evidence.md
```

Keep personal logs, resumes, applications, employer notes, health details, salary notes, and private tracking data in your vault. Do not commit them to this public repo.

See [docs/obsidian-workflow.md](docs/obsidian-workflow.md) for the recommended loop.

## Run The Scorecard Tool

The scorecard script accepts JSON or CSV logs and prints a Markdown trend summary.

```bash
python scripts/scorecard.py examples/career-log.example.json
python scripts/scorecard.py examples/career-log.example.csv --output examples/scorecard-summary.example.md
```

It uses only the Python standard library. It makes no network calls and writes nothing unless `--output` is supplied.

## Test

```bash
python -m json.tool tests/eval_queries.json > NUL
python -m py_compile scripts/scorecard.py tests/test_scorecard.py
python -m unittest discover -s tests -v
```

On macOS or Linux, replace `> NUL` with `> /dev/null`.

## Privacy And Safety

Career work can involve sensitive information. This project is designed around a clean split:

- Public repo: reusable prompts, playbooks, scripts, examples, and templates
- Private vault: personal career records, applications, resumes, interview notes, employer details, and score logs

The skill tells agents not to invent credentials, experience, salaries, job openings, legal outcomes, or hiring odds. It also tells agents to redirect legal, tax, benefits, immigration, medical, and severe mental-health questions to qualified professionals while helping organize facts and questions.

## License

MIT. Use it, adapt it, and make it useful.
