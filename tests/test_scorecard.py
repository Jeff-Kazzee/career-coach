from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "scorecard.py"


class ScorecardScriptTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_valid_csv_produces_markdown_summary(self) -> None:
        csv_text = """date,skill_strength,proof_portfolio_strength,resume_clarity,search_consistency,interview_readiness,network_reach,market_alignment,professional_communication,execution_consistency,confidence_resilience,applications_sent,work_shipped
2026-06-01,2,1,2,1,2,1,2,3,1,2,2,0
2026-06-08,2.5,2,2.5,2,2,1.5,2.5,3,2,2.5,4,1
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "career-log.csv"
            path.write_text(csv_text, encoding="utf-8")
            result = self.run_script(str(path))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Career Scorecard Trend", result.stdout)
        self.assertIn("Skill strength", result.stdout)
        self.assertIn("Applications sent", result.stdout)
        self.assertIn("## Suggested focus", result.stdout)

    def test_valid_json_can_write_output_file(self) -> None:
        payload = {
            "entries": [
                {
                    "date": "2026-06-01",
                    "scores": {"resume_clarity": 1, "execution_consistency": 2},
                    "metrics": {"commitments_planned": 2, "commitments_completed": 1},
                },
                {
                    "date": "2026-06-08",
                    "scores": {"resume_clarity": 2, "execution_consistency": 2.5},
                    "metrics": {"commitments_planned": 2, "commitments_completed": 2},
                },
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "career-log.json"
            output_path = Path(temp_dir) / "summary.md"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.run_script(str(input_path), "--output", str(output_path))
            summary = output_path.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Wrote Markdown summary", result.stdout)
        self.assertIn("Resume clarity", summary)
        self.assertIn("Commitment completion", summary)

    def test_invalid_score_fails_safely(self) -> None:
        payload = {
            "entries": [
                {"date": "2026-06-01", "scores": {"skill_strength": 7}}
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.run_script(str(path))

        self.assertEqual(result.returncode, 2)
        self.assertIn("between 0 and 5", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_duplicate_dates_fail_safely(self) -> None:
        payload = {
            "entries": [
                {"date": "2026-06-01", "scores": {"skill_strength": 2}},
                {"date": "2026-06-01", "scores": {"skill_strength": 3}},
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "duplicate.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.run_script(str(path))

        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate dates", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
