"""Compare the rules' ratings with the expected ratings in samples/.

Usage:  python scripts/check_samples.py
Rules only; no AI calls, no cost. Exit code 1 if any rating differs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gac.check import run_check  # noqa: E402
from gac.models import CHECKS, AssessmentInput  # noqa: E402
from gac.rules import load  # noqa: E402


def main() -> int:
    ruleset = load()
    total = agree = 0
    for path in sorted((ROOT / "samples").glob("*.yaml")):
        sample = yaml.safe_load(path.read_text(encoding="utf-8"))
        result = run_check(AssessmentInput.from_dict(sample["input"]), ruleset, client=None)
        expected = sample.get("expected", {})
        diffs = []
        for check in CHECKS:
            if check not in expected:
                continue
            total += 1
            if expected[check] == result.ratings[check]:
                agree += 1
            else:
                diffs.append(f"{check}: expected {expected[check]}, got {result.ratings[check]}")
        status = "OK  " if not diffs else "DIFF"
        print(f"{status} {path.stem}")
        for d in diffs:
            print(f"       {d}")
    pct = 100 * agree / total if total else 0
    print(f"\n{agree}/{total} ratings match ({pct:.0f}%). Rules version: {ruleset.version}")
    return 0 if agree == total else 1


if __name__ == "__main__":
    sys.exit(main())
