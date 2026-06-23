#!/usr/bin/env python3
"""Create a Markdown career-scorecard trend summary from local JSON or CSV.

Standard library only; no network calls. Nothing is stored unless --output is
supplied.

Usage:
  python scripts/scorecard.py career-log.json
  python scripts/scorecard.py career-log.csv --output summary.md
  python scripts/scorecard.py --example json
  python scripts/scorecard.py --example csv

JSON may be a list or {"entries": [...]}. Each entry needs an ISO date and may
use nested "scores" / "metrics" objects or top-level fields. CSV needs a date
column. Scores range from 0 to 5; partial score updates are allowed.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


DIMENSIONS = {
    "skill_strength": "Skill strength",
    "proof_portfolio_strength": "Proof/portfolio strength",
    "resume_clarity": "Resume clarity",
    "search_consistency": "Search consistency",
    "interview_readiness": "Interview readiness",
    "network_reach": "Network/reach",
    "market_alignment": "Market alignment",
    "professional_communication": "Professional communication",
    "execution_consistency": "Execution consistency",
    "confidence_resilience": "Confidence and resilience",
}
METRICS = {
    "wins": "Wins",
    "work_shipped": "Work shipped",
    "applications_sent": "Applications sent",
    "conversations_started": "Conversations started",
    "interviews_completed": "Interviews completed",
    "skills_practiced": "Skills practiced",
    "portfolio_improvements": "Portfolio improvements",
    "feedback_items": "Feedback items",
    "commitments_completed": "Commitments completed",
    "commitments_planned": "Commitments planned",
    "energy_level": "Energy level",
}
ALIASES = {
    "proof_strength": "proof_portfolio_strength",
    "portfolio_strength": "proof_portfolio_strength",
    "proof_and_portfolio_strength": "proof_portfolio_strength",
    "network": "network_reach",
    "network_and_reach": "network_reach",
    "confidence_and_resilience": "confidence_resilience",
    "communication": "professional_communication",
    "week": "date",
}

EXAMPLE_JSON = {
    "entries": [
        {
            "date": "2026-06-02",
            "scores": {
                "skill_strength": 2,
                "proof_portfolio_strength": 1.5,
                "resume_clarity": 2,
                "search_consistency": 1,
                "interview_readiness": 2,
                "network_reach": 1,
                "market_alignment": 2,
                "professional_communication": 3,
                "execution_consistency": 1.5,
                "confidence_resilience": 2,
            },
            "metrics": {
                "applications_sent": 2,
                "work_shipped": 0,
                "commitments_planned": 3,
                "commitments_completed": 1,
                "energy_level": 2,
            },
        },
        {
            "date": "2026-06-09",
            "scores": {
                "proof_portfolio_strength": 2,
                "resume_clarity": 2.5,
                "search_consistency": 2,
                "execution_consistency": 2,
                "confidence_resilience": 2.5,
            },
            "metrics": {
                "applications_sent": 4,
                "work_shipped": 1,
                "commitments_planned": 3,
                "commitments_completed": 3,
                "energy_level": 3,
            },
        },
    ]
}
EXAMPLE_CSV = """date,skill_strength,proof_portfolio_strength,resume_clarity,search_consistency,interview_readiness,network_reach,market_alignment,professional_communication,execution_consistency,confidence_resilience,applications_sent,work_shipped,commitments_planned,commitments_completed,energy_level
2026-06-02,2,1.5,2,1,2,1,2,3,1.5,2,2,0,3,1,2
2026-06-09,,2,2.5,2,,,,,2,2.5,4,1,3,3,3
"""


class InputError(ValueError):
    pass


def key_name(raw: str) -> str:
    value = raw.strip().lower().replace("&", " and ")
    value = re.sub(r"[/\-]+", "_", value)
    value = re.sub(r"[^a-z0-9_ ]+", "", value)
    value = re.sub(r"[\s_]+", "_", value).strip("_")
    return ALIASES.get(value, value)


def parse_date(raw: Any, context: str) -> date:
    if not isinstance(raw, str) or not raw.strip():
        raise InputError(f"{context}: date is required in YYYY-MM-DD format")
    try:
        return date.fromisoformat(raw.strip())
    except ValueError as exc:
        raise InputError(f"{context}: invalid date {raw!r}; expected YYYY-MM-DD") from exc


def parse_score(raw: Any, name: str, context: str) -> float:
    if isinstance(raw, bool) or raw is None or (isinstance(raw, str) and not raw.strip()):
        raise InputError(f"{context}: score for {name} must be numeric")
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise InputError(f"{context}: score for {name} is not numeric: {raw!r}") from exc
    if not math.isfinite(value) or not 0 <= value <= 5:
        raise InputError(f"{context}: score for {name} must be between 0 and 5; got {raw!r}")
    return value


def parse_metric(raw: Any) -> Any:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    if isinstance(raw, bool):
        return str(raw)
    if isinstance(raw, (int, float)):
        return raw
    value = str(raw).strip()
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


def selected(mapping: Mapping[str, Any], allowed: Mapping[str, str], context: str) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for raw_key, raw_value in mapping.items():
        name = key_name(str(raw_key))
        if name not in allowed or raw_value in (None, ""):
            continue
        if name in output:
            raise InputError(f"{context}: duplicate field for {name}")
        output[name] = parse_score(raw_value, name, context) if allowed is DIMENSIONS else parse_metric(raw_value)
    return output


def make_entry(raw: Mapping[str, Any], context: str) -> dict[str, Any]:
    day = parse_date(raw.get("date"), context)
    nested_scores = raw.get("scores", {})
    nested_metrics = raw.get("metrics", {})
    if not isinstance(nested_scores, Mapping):
        raise InputError(f'{context}: "scores" must be an object')
    if not isinstance(nested_metrics, Mapping):
        raise InputError(f'{context}: "metrics" must be an object')

    scores = selected(nested_scores, DIMENSIONS, context)
    top_scores = selected(raw, DIMENSIONS, context)
    duplicate_scores = set(scores) & set(top_scores)
    if duplicate_scores:
        raise InputError(f"{context}: duplicate nested/top-level scores: {', '.join(sorted(duplicate_scores))}")
    scores.update(top_scores)

    metrics = selected(nested_metrics, METRICS, context)
    for name, value in selected(raw, METRICS, context).items():
        metrics.setdefault(name, value)
    if not scores and not metrics:
        raise InputError(f"{context}: no recognized scores or metrics")
    return {"date": day, "scores": scores, "metrics": metrics}


def load_json(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    raw_entries = payload.get("entries") if isinstance(payload, dict) else payload
    if not isinstance(raw_entries, list):
        raise InputError('JSON must be a list or an object with an "entries" list')
    return [make_entry(raw, f"JSON entry {index}") if isinstance(raw, Mapping) else _bad_entry(index)
            for index, raw in enumerate(raw_entries, 1)]


def _bad_entry(index: int) -> dict[str, Any]:
    raise InputError(f"JSON entry {index}: expected an object")


def load_csv(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise InputError("CSV has no header row")
            headers = [key_name(name or "") for name in reader.fieldnames]
            if "date" not in headers:
                raise InputError("CSV must contain a date column")
            if len(headers) != len(set(headers)):
                raise InputError("CSV contains duplicate normalized headers")
            entries = []
            for row_number, row in enumerate(reader, 2):
                if not any((value or "").strip() for value in row.values()):
                    continue
                normalized = {key_name(name or ""): value for name, value in row.items()}
                entries.append(make_entry(normalized, f"CSV row {row_number}"))
            return entries
    except UnicodeDecodeError as exc:
        raise InputError("CSV is not valid UTF-8 text") from exc


def load(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise InputError(f"input file does not exist or is not a file: {path}")
    if path.suffix.lower() == ".json":
        entries = load_json(path)
    elif path.suffix.lower() == ".csv":
        entries = load_csv(path)
    else:
        raise InputError("input file must end in .json or .csv")
    if not entries:
        raise InputError("input contains no entries")
    entries.sort(key=lambda entry: entry["date"])
    dates = [entry["date"] for entry in entries]
    duplicates = sorted({day.isoformat() for day in dates if dates.count(day) > 1})
    if duplicates:
        raise InputError("duplicate dates are not allowed: " + ", ".join(duplicates))
    if not any(entry["scores"] for entry in entries):
        raise InputError("input contains metrics but no recognized scores")
    return entries


def mean(values: Iterable[float]) -> float | None:
    data = list(values)
    return sum(data) / len(data) if data else None


def observations(entries: Sequence[dict[str, Any]], name: str) -> list[tuple[date, float]]:
    return [(entry["date"], entry["scores"][name]) for entry in entries if name in entry["scores"]]


def latest_pair(entries: Sequence[dict[str, Any]], name: str) -> tuple[float | None, float | None, date | None]:
    values = observations(entries, name)
    if not values:
        return None, None, None
    return values[-1][1], values[-2][1] if len(values) > 1 else None, values[-1][0]


def fmt_score(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f}"


def fmt_delta(value: float | None) -> str:
    if value is None:
        return "—"
    return "0.0" if abs(value) < 0.05 else f"{value:+.1f}"


def clean(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def neglected(entries: Sequence[dict[str, Any]], threshold: float, window: int) -> tuple[list[str], list[str]]:
    flags: list[str] = []
    priorities: list[tuple[float, str]] = []
    recent = entries[-window:]
    for name, label in DIMENSIONS.items():
        values = observations(entries, name)
        if not values:
            flags.append(f"**{label}:** never scored; establish a baseline.")
            priorities.append((10, label))
            continue
        last_day, latest = values[-1]
        reasons: list[str] = []
        weight = 0.0
        if latest <= threshold:
            reasons.append(f"low at {latest:.1f}")
            weight += 3 + threshold - latest
        if not any(name in entry["scores"] for entry in recent):
            reasons.append(f"not updated in the last {window} logged periods")
            weight += 2
        recent_values = [value for _, value in values[-window:]]
        if len(recent_values) >= min(3, window) and max(recent_values) - min(recent_values) < .25 and latest <= threshold + .5:
            reasons.append("flat while still weak")
            weight += 1.5
        if len(values) > 1 and latest - values[-2][1] < -.25:
            reasons.append(f"declined {values[-2][1] - latest:.1f}")
            weight += values[-2][1] - latest + 1
        if reasons:
            flags.append(f"**{label}:** " + "; ".join(reasons) + ".")
            priorities.append((weight, label))
    focus = [label for _, label in sorted(priorities, key=lambda item: (-item[0], item[1]))[:3]]
    return flags, focus


def summary(entries: Sequence[dict[str, Any]], source: str, threshold: float, window: int) -> str:
    current = {name: latest_pair(entries, name)[0] for name in DIMENSIONS}
    current = {name: value for name, value in current.items() if value is not None}
    comparable = [(latest, prior) for name in DIMENSIONS
                  if (latest := latest_pair(entries, name)[0]) is not None
                  and (prior := latest_pair(entries, name)[1]) is not None]
    overall = mean(current.values())
    overall_change = mean(latest for latest, _ in comparable) - mean(prior for _, prior in comparable) if comparable else None

    lines = [
        "# Career Scorecard Trend", "",
        f"- **Source:** `{clean(source)}`",
        f"- **Entries:** {len(entries)}",
        f"- **Date range:** {entries[0]['date'].isoformat()} to {entries[-1]['date'].isoformat()}",
        f"- **Latest known overall score:** {fmt_score(overall)} / 5 across {len(current)} dimensions",
    ]
    if overall_change is not None:
        lines.append(f"- **Change versus prior comparable observations:** {fmt_delta(overall_change)}")
    lines += ["", "> Scores organize logged evidence; they are not a judgment, hiring prediction, or clinical assessment.",
              "", "## Latest score changes", "",
              "| Dimension | Latest | Prior observation | Change | Latest evidence date |",
              "|---|---:|---:|---:|---|"]

    changes: list[tuple[float, str]] = []
    for name, label in DIMENSIONS.items():
        latest, prior, day = latest_pair(entries, name)
        delta = latest - prior if latest is not None and prior is not None else None
        if delta is not None:
            changes.append((delta, label))
        lines.append(f"| {label} | {fmt_score(latest)} | {fmt_score(prior)} | {fmt_delta(delta)} | {day.isoformat() if day else '—'} |")

    gains = [f"{label} ({change:+.1f})" for change, label in sorted(changes, reverse=True) if change >= .25][:3]
    drops = [f"{label} ({change:+.1f})" for change, label in sorted(changes) if change <= -.25][:3]
    lines += ["", "## Change summary", "",
              "- **Largest gains:** " + (", ".join(gains) if gains else "No material gains logged yet."),
              "- **Largest declines:** " + (", ".join(drops) if drops else "No material declines logged.")]

    metric_entry = next((entry for entry in reversed(entries) if entry["metrics"]), None)
    lines += ["", "## Latest logged activity", ""]
    if metric_entry:
        lines += [f"**Entry date:** {metric_entry['date'].isoformat()}", ""]
        for name, label in METRICS.items():
            if name in metric_entry["metrics"]:
                lines.append(f"- **{label}:** {clean(metric_entry['metrics'][name])}")
        planned = metric_entry["metrics"].get("commitments_planned")
        done = metric_entry["metrics"].get("commitments_completed")
        if isinstance(planned, (int, float)) and planned > 0 and isinstance(done, (int, float)):
            lines.append(f"- **Commitment completion:** {done / planned * 100:.0f}%")
    else:
        lines.append("No recognized activity metrics were logged.")

    flags, focus = neglected(entries, threshold, window)
    lines += ["", "## Neglected or vulnerable areas", ""]
    lines += [f"- {flag}" for flag in flags] if flags else ["No area met the configured low, stale, flat, or declining criteria."]
    lines += ["", "## Suggested focus", ""]
    if focus:
        lines += [f"{index}. **{label}:** define one evidence-producing action and its done condition."
                  for index, label in enumerate(focus, 1)]
    else:
        lines.append("Choose the dimension closest to the current career-funnel bottleneck; scores alone do not determine strategy.")
    lines += ["", "## Review questions", "",
              "1. Which change is supported by concrete evidence rather than mood?",
              "2. Where does progress stop: opportunity finding, execution, screening, interviewing, offers, or advancement?",
              "3. What one action next period would create the strongest new evidence?",
              "4. Does the plan fit actual time, energy, access, and money constraints?", ""]
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Summarize career score trends from JSON or CSV.")
    result.add_argument("input", nargs="?", type=Path)
    result.add_argument("--output", type=Path, help="Write Markdown to this path")
    result.add_argument("--low-threshold", type=float, default=2.0)
    result.add_argument("--recent-window", type=int, default=3)
    result.add_argument("--example", choices=("json", "csv"))
    return result


def run(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.example:
        if args.input or args.output:
            parser().error("--example cannot be combined with input or --output")
        print(json.dumps(EXAMPLE_JSON, indent=2) if args.example == "json" else EXAMPLE_CSV, end="\n" if args.example == "json" else "")
        return 0
    if not args.input:
        parser().error("provide an input .json or .csv file, or use --example")
    if not 0 <= args.low_threshold <= 5:
        parser().error("--low-threshold must be between 0 and 5")
    if args.recent_window < 1:
        parser().error("--recent-window must be at least 1")
    try:
        text = summary(load(args.input), args.input.name, args.low_threshold, args.recent_window)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
            print(f"Wrote Markdown summary to {args.output}")
        else:
            print(text)
        return 0
    except (InputError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
