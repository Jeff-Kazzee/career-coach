from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "scorecard.py"
DIMS = ["skill_strength", "proof_portfolio_strength", "resume_clarity", "search_consistency",
        "interview_readiness", "network_reach", "market_alignment", "professional_communication",
        "execution_consistency", "confidence_resilience"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_script(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), *args], text=True,
                              capture_output=True, check=False, cwd=cwd)

    def write(self, name: str, content: str | bytes) -> Path:
        path = self.dir / name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def log(self, entries: list, name: str = "log.json") -> Path:
        return self.write(name, json.dumps({"entries": entries}))

    def ok(self, path: Path) -> str:
        result = self.run_script(str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def fails(self, path: Path, text: str = "") -> subprocess.CompletedProcess:
        result = self.run_script(str(path))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        if text:
            self.assertIn(text, result.stderr)
        return result


class OriginalTests(Base):
    def test_valid_csv_produces_markdown_summary(self) -> None:
        header = "date," + ",".join(DIMS) + ",applications_sent,work_shipped\n"
        path = self.write("career-log.csv", header + "2026-06-01,2,1,2,1,2,1,2,3,1,2,2,0\n2026-06-08,2.5,2,2.5,2,2,1.5,2.5,3,2,2.5,4,1\n")
        out = self.ok(path)
        for text in ("# Career Scorecard Summary", "Skill strength", "Applications sent", "## Choosing a focus"):
            self.assertIn(text, out)

    def test_valid_json_can_write_output_file(self) -> None:
        path = self.log([{"date": "2026-06-01", "scores": {"resume_clarity": 1}, "metrics": {"commitments_planned": 2, "commitments_completed": 1}}])
        out = self.dir / "summary.md"
        result = self.run_script(str(path), "--output", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Commitment completion", out.read_text(encoding="utf-8"))

    def test_invalid_score_fails_safely(self) -> None:
        self.fails(self.log([{"date": "2026-06-01", "scores": {"skill_strength": 7}}]), "between 0 and 5")

    def test_duplicate_dates_fail_safely(self) -> None:
        self.fails(self.log([{"date": "2026-06-01", "scores": {"skill_strength": 2}},
                             {"date": "2026-06-01", "scores": {"skill_strength": 3}}]), "duplicate dates")

    def test_examples_run(self) -> None:
        self.ok(ROOT / "examples" / "career-log.example.json")
        self.ok(ROOT / "examples" / "career-log.example.csv")


class OutputSafety(Base):
    def assert_protected(self, src: Path, *args: str, cwd: Path | None = None) -> None:
        before = sha(src)
        result = self.run_script(*args, cwd=cwd)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(sha(src), before)

    def test_same_path_relative_dotdot(self) -> None:
        src = self.log([{"date": "2026-06-01", "scores": {"skill_strength": 2}}], "log.md")
        (self.dir / "sub").mkdir()
        self.assert_protected(src, str(src), "--output", str(src))
        self.assert_protected(src, "log.md", "--output", "./log.md", cwd=self.dir)
        self.assert_protected(src, str(src), "--output", str(self.dir / "sub" / ".." / "log.md"))

    def test_symlink_and_hardlink(self) -> None:
        src = self.log([{"date": "2026-06-01", "scores": {"skill_strength": 2}}])
        link, hard = self.dir / "link.md", self.dir / "hard.md"
        try:
            os.symlink(src, link)
            self.assert_protected(src, str(src), "--output", str(link))
        except (OSError, NotImplementedError):
            pass
        os.link(src, hard)
        self.assert_protected(src, str(src), "--output", str(hard))

    def test_output_must_be_markdown(self) -> None:
        src = self.log([{"date": "2026-06-01", "scores": {"skill_strength": 2}}])
        self.assert_protected(src, str(src), "--output", str(self.dir / "other.json"))

    def test_failed_run_keeps_previous_output(self) -> None:
        bad = self.log([{"date": "2026-06-01", "scores": {"skill_strength": 9}}])
        out = self.write("summary.md", "PRIOR")
        result = self.run_script(str(bad), "--output", str(out))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(out.read_text(), "PRIOR")


class ScoreStates(Base):
    def test_unknown_and_na_not_averaged(self) -> None:
        path = self.log([{"date": "2026-06-01", "scores": {"skill_strength": 4, "resume_clarity": "N/A",
                                                            "network_reach": "unknown", "market_alignment": None}}])
        out = self.ok(path)
        self.assertIn("4.0 / 5 across 1 of 10 assessed (1 n/a, 8 unknown)", out)

    def test_zero_is_assessed(self) -> None:
        scores = {d: (0 if i < 5 else 4) for i, d in enumerate(DIMS)}
        self.assertIn("2.0 / 5 across 10 of 10 assessed", self.ok(self.log([{"date": "2026-06-01", "scores": scores}])))
        scores = {d: 4 for d in DIMS[5:]}
        self.assertIn("4.0 / 5 across 5 of 10 assessed", self.ok(self.log([{"date": "2026-06-01", "scores": scores}])))

    def test_assessed_zero_is_a_signal_and_unknowns_are_review(self) -> None:
        out = self.ok(self.log([{"date": "2026-06-01", "scores": {"resume_clarity": 0}}]))
        signals = out.split("## Signals")[1].split("## Latest logged activity")[0]
        review = out.split("## Evidence review")[1].split("## Signals")[0]
        self.assertIn("Resume clarity", signals)
        self.assertIn("Confidence and resilience", review)
        self.assertNotIn("Confidence and resilience", signals)
        self.assertNotIn("Suggested focus", out)

    def test_unchanged_is_not_weak_or_stale(self) -> None:
        entries = [{"date": "2026-06-01", "scores": {d: 4 for d in DIMS}}] + \
                  [{"date": f"2026-06-{8 + 7 * i:02d}", "scores": {"resume_clarity": 4}} for i in range(3)]
        out = self.ok(self.log(entries))
        self.assertIn("## Signals", out)
        self.assertIn("- None.", out.split("## Signals")[1])
        self.assertIn("- Nothing to review.", out)

    def test_old_evidence_is_stale_not_signal(self) -> None:
        out = self.ok(self.log([{"date": "2025-01-01", "scores": {"skill_strength": 1}},
                                {"date": "2026-06-01", "scores": {"resume_clarity": 3}}]))
        self.assertIn("Older than 45 days: Skill strength", out)
        self.assertNotIn("Skill strength:", out.split("## Signals")[1])

    def test_order_independent(self) -> None:
        a = {d: i % 5 for i, d in enumerate(DIMS)}
        b = dict(reversed(list(a.items())))
        out_a = self.ok(self.log([{"date": "2026-06-01", "scores": a}], "a.json"))
        out_b = self.ok(self.log([{"date": "2026-06-01", "scores": b}], "b.json"))
        self.assertEqual(out_a.replace("a.json", "x"), out_b.replace("b.json", "x"))


class MalformedInput(Base):
    def test_csv_surplus_and_blank_surplus(self) -> None:
        self.fails(self.write("a.csv", "date,skill_strength\n2026-06-01,2,999\n"), "row 2")
        self.fails(self.write("b.csv", "date,skill_strength\n,,999\n"), "row 2")

    def test_invalid_utf8(self) -> None:
        self.fails(self.write("a.json", b'{"entries":[{"date":"2026-06-01","scores":{"skill_strength":2}}],"x":"\xff"}'), "UTF-8")
        self.fails(self.write("a.csv", b"date,skill_strength\n2026-06-01,\xff\n"), "UTF-8")

    def test_huge_numbers_and_deep_nesting(self) -> None:
        self.fails(self.write("a.json", '{"entries":[{"date":"2026-06-01","scores":{"skill_strength":1%s}}]}' % ("0" * 400)))
        self.fails(self.write("b.json", "[" * 100000 + "]" * 100000))

    def test_unknown_field_warns(self) -> None:
        path = self.log([{"date": "2026-06-01", "scores": {"skil_strength": 2, "resume_clarity": 3}}])
        result = self.run_script(str(path))
        self.assertEqual(result.returncode, 0)
        self.assertIn("skil_strength", result.stderr)

    def test_semicolon_csv_hint(self) -> None:
        self.fails(self.write("a.csv", "date;skill_strength\n2026-06-01;2\n"), "semicolons")


class Metrics(Base):
    def entry(self, **metrics) -> Path:
        return self.log([{"date": "2026-06-01", "scores": {"resume_clarity": 2}, "metrics": metrics}])

    def test_bad_counts_rejected(self) -> None:
        for value in (-8, 2.7, True):
            self.fails(self.entry(applications_sent=value))
        self.fails(self.write("nan.json", '{"entries":[{"date":"2026-06-01","metrics":{"wins":NaN}}]}'))
        self.fails(self.write("inf.json", '{"entries":[{"date":"2026-06-01","metrics":{"wins":Infinity}}]}'))

    def test_conflicts_and_duplicate_keys(self) -> None:
        self.fails(self.log([{"date": "2026-06-01", "metrics": {"applications_sent": 3}, "applications_sent": 9}]), "nested")
        self.fails(self.write("dup.json", '{"entries":[{"date":"2026-06-01","scores":{"resume_clarity":1,"resume_clarity":4}}]}'), "duplicate")

    def test_over_100_percent_and_text(self) -> None:
        out = self.ok(self.entry(commitments_planned=2, commitments_completed=5, wins="recruiter replied"))
        self.assertIn("250% (more than planned)", out)
        self.assertIn("recruiter replied", out)


if __name__ == "__main__":
    unittest.main()
