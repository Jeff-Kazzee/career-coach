#!/usr/bin/env python3
"""Create a Markdown career-scorecard summary from a local JSON or CSV log.

Standard library only. No network calls. Nothing is written unless --output
is supplied, and the output must be a new .md file, never the input log.

Usage:
  python scripts/scorecard.py career-log.json
  python scripts/scorecard.py career-log.csv --output summary.md
  python scripts/scorecard.py --example json
  python scripts/scorecard.py --example csv

JSON may be a list or {"entries": [...]}. Each entry needs an ISO date
(YYYY-MM-DD) and may use nested "scores" / "metrics" objects or top-level
fields. CSV needs a date column.

Score values:
  0-5        assessed score (0 = assessed: absent or not started)
  blank/null/"unknown"  not assessed yet (never averaged)
  "n/a"      does not apply to the current goal (never averaged)

Exit codes: 0 success, 2 input or usage error.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

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
SCALE_METRICS = {"energy_level"}
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
IGNORED_FIELDS = {"date", "scores", "metrics", "notes", "note", "comments", "comment"}
UNKNOWN_WORDS = {"", "unknown", "?", "not assessed"}
NA_WORDS = {"n/a", "na", "not applicable"}
NA = "n/a"
MAX_ABS_INPUT = 10 ** 6

EXAMPLE_JSON = {
    "entries": [
        {
            "date": "2026-06-02",
            "scores": {
                "skill_strength": 2,
                "proof_portfolio_strength": 1.5,
                "resume_clarity": 2,
                "search_consistency": 1,
                "interview_readiness": "unknown",
                "network_reach": 1,
                "market_alignment": 2,
                "professional_communication": 3,
                "execution_consistency": 1.5,
                "confidence_resilience": "unknown",
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
2026-06-02,2,1.5,2,1,unknown,1,2,3,1.5,unknown,2,0,3,1,2
2026-06-09,,2,2.5,2,,,,,2,,4,1,3,3,3
"""


class InputError(ValueError):
    pass


WARNINGS: List[str] = []


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


def to_number(raw: Any, name: str, context: str) -> Optional[float]:
    """Return a finite number, or None when raw is not numeric text."""
    if isinstance(raw, bool):
        raise InputError(f"{context}: {name} must be a number, not true/false")
    if isinstance(raw, int):
        if abs(raw) > MAX_ABS_INPUT:
            raise InputError(f"{context}: {name} is out of range: {raw}")
        return float(raw)
    if isinstance(raw, float):
        value = raw
    elif isinstance(raw, str):
        text = raw.strip()
        if not re.fullmatch(r"[+-]?(\d+(\.\d*)?|\.\d+)", text):
            return None
        if len(text) > 12:
            raise InputError(f"{context}: {name} is out of range: {text}")
        value = float(text)
    else:
        raise InputError(f"{context}: {name} has an unsupported value: {raw!r}")
    if not math.isfinite(value) or abs(value) > MAX_ABS_INPUT:
        raise InputError(f"{context}: {name} must be a finite number; got {raw!r}")
    return value


def parse_score(raw: Any, name: str, context: str) -> Any:
    """Return a float 0-5, NA, or None for unknown."""
    if raw is None:
        return None
    if isinstance(raw, str):
        word = raw.strip().lower()
        if word in UNKNOWN_WORDS:
            return None
        if word in NA_WORDS:
            return NA
    value = to_number(raw, f"score for {name}", context)
    if value is None:
        raise InputError(f"{context}: score for {name} must be 0-5, unknown, or n/a; got {raw!r}")
    if not 0 <= value <= 5:
        raise InputError(f"{context}: score for {name} must be between 0 and 5; got {raw!r}")
    return value


def parse_metric(raw: Any, name: str, context: str) -> Any:
    """Counts: non-negative whole numbers or free text. Energy: 0-5."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    value = to_number(raw, name, context)
    if value is None:
        if name in SCALE_METRICS:
            raise InputError(f"{context}: {name} must be a number from 0 to 5; got {raw!r}")
        return str(raw).strip()
    if name in SCALE_METRICS:
        if not 0 <= value <= 5:
            raise InputError(f"{context}: {name} must be between 0 and 5; got {raw!r}")
        return value
    if value < 0:
        raise InputError(f"{context}: {name} cannot be negative; got {raw!r}")
    if value != int(value):
        raise InputError(f"{context}: {name} must be a whole number; got {raw!r}")
    return int(value)


def selected(mapping: Mapping[str, Any], allowed: Mapping[str, str], context: str, scores: bool) -> Dict[str, Any]:
    output: Dict[str, Any] = {}
    for raw_key, raw_value in mapping.items():
        name = key_name(str(raw_key))
        if name not in allowed:
            continue
        value = parse_score(raw_value, name, context) if scores else parse_metric(raw_value, name, context)
        if value is None:
            continue
        if name in output:
            raise InputError(f"{context}: duplicate field for {name}")
        output[name] = value
    return output


def note_unknown_fields(mapping: Mapping[str, Any], context: str) -> None:
    known = set(DIMENSIONS) | set(METRICS) | IGNORED_FIELDS
    extra = sorted({str(k) for k in mapping if key_name(str(k)) not in known})
    if extra:
        WARNINGS.append(f"{context}: ignored unrecognized field(s): {', '.join(extra)}")


def merge(nested: Dict[str, Any], top: Dict[str, Any], kind: str, context: str) -> Dict[str, Any]:
    clash = sorted(set(nested) & set(top))
    if clash:
        raise InputError(f"{context}: {kind} given both nested and at top level: {', '.join(clash)}")
    merged = dict(nested)
    merged.update(top)
    return merged


def make_entry(raw: Mapping[str, Any], context: str) -> Dict[str, Any]:
    day = parse_date(raw.get("date"), context)
    nested_scores = raw.get("scores", {}) or {}
    nested_metrics = raw.get("metrics", {}) or {}
    if not isinstance(nested_scores, Mapping):
        raise InputError(f'{context}: "scores" must be an object')
    if not isinstance(nested_metrics, Mapping):
        raise InputError(f'{context}: "metrics" must be an object')
    note_unknown_fields(raw, context)
    note_unknown_fields(nested_scores, context + " scores")
    note_unknown_fields(nested_metrics, context + " metrics")
    scores = merge(selected(nested_scores, DIMENSIONS, context, True), selected(raw, DIMENSIONS, context, True), "scores", context)
    metrics = merge(selected(nested_metrics, METRICS, context, False), selected(raw, METRICS, context, False), "metrics", context)
    return {"date": day, "scores": scores, "metrics": metrics}


def _no_duplicate_keys(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"JSON has a duplicate key: {key!r}")
        result[key] = value
    return result


def _reject_constant(name: str) -> Any:
    raise InputError(f"JSON contains {name}; use a finite number")


def read_text(path: Path, kind: str) -> str:
    try:
        return path.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InputError(f"{kind} is not valid UTF-8 text (byte {exc.start})") from exc


def load_json(path: Path) -> List[Dict[str, Any]]:
    text = read_text(path, "JSON")
    try:
        payload = json.loads(text, object_pairs_hook=_no_duplicate_keys, parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    except RecursionError as exc:
        raise InputError("JSON is nested too deeply") from exc
    except InputError:
        raise
    except ValueError as exc:
        raise InputError(f"JSON could not be read: {exc}") from exc
    raw_entries = payload.get("entries") if isinstance(payload, dict) else payload
    if not isinstance(raw_entries, list):
        raise InputError('JSON must be a list or an object with an "entries" list')
    entries = []
    for index, raw in enumerate(raw_entries, 1):
        if not isinstance(raw, Mapping):
            raise InputError(f"JSON entry {index}: expected an object")
        entries.append(make_entry(raw, f"JSON entry {index}"))
    return entries


def load_csv(path: Path) -> List[Dict[str, Any]]:
    text = read_text(path, "CSV")
    lines = text.splitlines()
    if not lines or not lines[0].strip():
        raise InputError("CSV has no header row")
    try:
        reader = csv.DictReader(lines, restkey="__extra__")
        fieldnames = reader.fieldnames or []
        headers = [key_name(name or "") for name in fieldnames]
        if "date" not in headers:
            hint = " The header uses semicolons; save the file with commas." if ";" in lines[0] and "," not in lines[0] else ""
            raise InputError("CSV must contain a date column." + hint)
        if len(headers) != len(set(headers)):
            raise InputError("CSV contains duplicate normalized headers")
        entries = []
        for row_number, row in enumerate(reader, 2):
            extra = row.pop("__extra__", None)
            if extra is not None:
                raise InputError(f"CSV row {row_number}: has {len(fieldnames) + len(extra)} values but the header has {len(fieldnames)}")
            if not any((value or "").strip() for value in row.values()):
                continue
            normalized = {key_name(name or ""): value for name, value in row.items()}
            entries.append(make_entry(normalized, f"CSV row {row_number}"))
        return entries
    except csv.Error as exc:
        raise InputError(f"CSV could not be parsed: {exc}") from exc


def load(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        raise InputError(f"input file does not exist or is not a file: {path}")
    suffix = path.suffix.lower()
    if suffix == ".json":
        entries = load_json(path)
    elif suffix == ".csv":
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
    if not any(entry["scores"] or entry["metrics"] for entry in entries):
        raise InputError("input contains no recognized scores or metrics")
    return entries


def observations(entries: Sequence[Dict[str, Any]], name: str) -> List[Tuple[date, Any]]:
    return [(entry["date"], entry["scores"][name]) for entry in entries if name in entry["scores"]]


def mean(values: Iterable[float]) -> Optional[float]:
    data = list(values)
    return sum(data) / len(data) if data else None


def fmt(value: Any) -> str:
    if value is None:
        return "unknown"
    if value == NA:
        return "n/a"
    return f"{value:.1f}"


def clean(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("<", "&lt;").replace("\n", " ").strip()


def summary(entries: Sequence[Dict[str, Any]], source: str, threshold: float, stale_days: int) -> str:
    as_of = entries[-1]["date"]
    rows = []
    assessed: Dict[str, float] = {}
    na: List[str] = []
    unknown: List[str] = []
    stale: List[str] = []
    signals: List[str] = []
    for name, label in DIMENSIONS.items():
        obs = observations(entries, name)
        if not obs:
            unknown.append(label)
            rows.append((label, None, None, None, None, None))
            continue
        day, latest = obs[-1]
        numeric = [(d, v) for d, v in obs if v != NA]
        prior = numeric[-2][1] if latest != NA and len(numeric) > 1 else None
        age = (as_of - day).days
        delta = latest - prior if latest != NA and prior is not None else None
        rows.append((label, latest, prior, delta, day, age))
        if latest == NA:
            na.append(label)
            continue
        assessed[label] = latest
        if age > stale_days:
            stale.append(f"{label} (last evidence {day.isoformat()}, {age} days before the latest entry)")
            continue
        reasons = []
        if latest <= threshold:
            reasons.append(f"assessed at {latest:.1f}")
        if delta is not None and delta < -0.25:
            reasons.append(f"down {abs(delta):.1f} since the prior observation")
        if reasons:
            signals.append(f"{label}: " + "; ".join(reasons))

    average = mean(assessed.values())
    coverage = f"{len(assessed)} of {len(DIMENSIONS)} assessed ({len(na)} n/a, {len(unknown)} unknown)"
    lines = [
        "# Career Scorecard Summary", "",
        f"- Source: `{clean(source)}`",
        f"- Entries: {len(entries)}, from {entries[0]['date'].isoformat()} to {as_of.isoformat()}",
        f"- Coverage: {coverage}",
        "- Average of assessed scores: " + (f"{average:.1f} / 5 across {coverage}" if average is not None else "none yet (no dimension assessed)"),
        "",
        "> Scores organize logged evidence. They are not a judgment of the person, a hiring prediction, or a clinical assessment. Unknown and n/a dimensions are never averaged.",
        "", "## Latest scores", "",
        "| Dimension | Latest | Prior | Change | Evidence date | Age (days) |",
        "|---|---:|---:|---:|---|---:|",
    ]
    for label, latest, prior, delta, day, age in rows:
        change = "" if delta is None else ("0.0" if abs(delta) < 0.05 else f"{delta:+.1f}")
        lines.append(f"| {label} | {fmt(latest)} | {'' if prior is None else fmt(prior)} | {change} | {day.isoformat() if day else ''} | {'' if age is None else age} |")

    lines += ["", "## Evidence review", "",
              "Housekeeping, not weaknesses. Assess, refresh, or mark n/a when useful.", ""]
    review = ([f"- Not assessed yet: {', '.join(unknown)}"] if unknown else []) + \
             ([f"- Older than {stale_days} days: {'; '.join(stale)}"] if stale else []) + \
             ([f"- Marked n/a for this goal: {', '.join(na)}"] if na else [])
    lines += review or ["- Nothing to review."]

    lines += ["", "## Signals", "",
              f"Assessed scores at or below {threshold:.1f}, or down more than 0.25. Listed in fixed order, not ranked.", ""]
    lines += [f"- {s}" for s in signals] or ["- None."]

    metric_entry = next((entry for entry in reversed(entries) if entry["metrics"]), None)
    lines += ["", "## Latest logged activity", ""]
    if metric_entry:
        lines += [f"Entry date: {metric_entry['date'].isoformat()}", ""]
        for name, label in METRICS.items():
            if name in metric_entry["metrics"]:
                lines.append(f"- {label}: {clean(metric_entry['metrics'][name])}")
        planned = metric_entry["metrics"].get("commitments_planned")
        done = metric_entry["metrics"].get("commitments_completed")
        if isinstance(planned, int) and planned > 0 and isinstance(done, int):
            pct = done / planned * 100
            lines.append(f"- Commitment completion: {pct:.0f}%" + (" (more than planned)" if pct > 100 else ""))
    else:
        lines.append("No recognized activity metrics were logged.")

    lines += ["", "## Choosing a focus", "",
              "Pick the focus from your goal and the stage where progress stops. Signals above are inputs, not a ranking. The lowest score is not automatically the priority.",
              "", "## Review questions", "",
              "1. Which change is supported by concrete evidence rather than mood?",
              "2. Where does progress stop: finding opportunities, execution, screening, interviewing, offers, or advancement?",
              "3. What one action next period would create the strongest new evidence?",
              "4. Does the plan fit the time, energy, access, and money you actually have?", ""]
    return "\n".join(lines)


def check_output(input_path: Path, output: Path) -> None:
    if output.suffix.lower() != ".md":
        raise InputError("--output must be a .md file")
    if output.exists():
        try:
            if os.path.samefile(input_path, output):
                raise InputError("--output points to the input log; choose a different .md file")
        except OSError as exc:
            raise InputError(f"cannot check --output: {exc}") from exc
    if output.is_dir():
        raise InputError("--output is a directory")


def atomic_write(output: Path, text: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".scorecard-", suffix=".md", dir=str(output.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp, output)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Summarize career scores from a JSON or CSV log.")
    result.add_argument("input", nargs="?", type=Path)
    result.add_argument("--output", type=Path, help="Write Markdown to this new .md path")
    result.add_argument("--low-threshold", type=float, default=2.0)
    result.add_argument("--stale-days", type=int, default=45)
    result.add_argument("--example", choices=("json", "csv"))
    return result


def run(argv: Optional[Sequence[str]] = None) -> int:
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
    if args.stale_days < 1:
        parser().error("--stale-days must be at least 1")
    WARNINGS.clear()
    try:
        if args.output:
            check_output(args.input, args.output)
        text = summary(load(args.input), args.input.name, args.low_threshold, args.stale_days)
        for warning in WARNINGS:
            print(f"Warning: {warning}", file=sys.stderr)
        if args.output:
            atomic_write(args.output, text)
            print(f"Wrote Markdown summary to {args.output}")
        else:
            print(text)
        return 0
    except (InputError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
