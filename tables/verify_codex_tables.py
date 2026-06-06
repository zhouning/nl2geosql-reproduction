"""Verify the v7_codex majority-vote headline numbers.

The older ``verify_tables.py`` intentionally preserves the submitted legacy
per-sample Table 4 gate. This verifier checks the revised Computers &
Geosciences manuscript's question-level majority-vote McNemar convention.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO = Path(__file__).resolve().parents[1]
BUILT = REPO / "tables" / "built" / "codex_majority_vote.json"
TOL = 0.01

EXPECTED = {
    ("focused_three_condition", "overall", "B_minus_A", "delta"): 1.60,
    ("focused_three_condition", "overall", "B_minus_A", "p"): 0.8746,
    ("focused_three_condition", "spatial", "B_minus_A", "delta"): -10.59,
    ("focused_three_condition", "spatial", "B_minus_A", "p"): 0.1360,
    ("focused_three_condition", "spatial", "B_minus_A", "b"): 19,
    ("focused_three_condition", "spatial", "B_minus_A", "c"): 10,
    ("focused_three_condition", "robust", "B_minus_A", "delta"): 27.50,
    ("focused_three_condition", "robust", "B_minus_A", "p"): 0.0010,
    ("focused_three_condition", "spatial", "C_minus_B", "delta"): 8.24,
    ("focused_three_condition", "spatial", "C_minus_B", "p"): 0.0654,
    ("focused_three_condition", "spatial", "C_minus_A", "delta"): -2.35,
    ("focused_three_condition", "spatial", "C_minus_A", "p"): 0.8388,
    ("cross_family", "gemini-3.5-flash", "spatial", "delta"): -10.59,
    ("cross_family", "gemini-3.5-flash", "spatial", "p"): 0.1360,
    ("cross_family", "deepseek-v4-flash", "spatial", "delta"): 23.53,
    ("cross_family", "deepseek-v4-flash", "spatial", "p"): 0.0008,
    ("cross_family", "gemini-3.5-flash", "robust", "delta"): 32.50,
    ("cross_family", "gemini-3.5-flash", "robust", "p"): 0.0002,
}


def nested_get(data: dict, path: tuple[str, ...]):
    current = data
    for key in path:
        current = current[key]
    return current


def main() -> int:
    if not BUILT.exists():
        subprocess.run([sys.executable, "tables/build_codex_tables.py"], cwd=REPO, check=True)

    data = json.loads(BUILT.read_text(encoding="utf-8"))
    errors: list[str] = []
    for path, expected in EXPECTED.items():
        actual = nested_get(data, path)
        if isinstance(expected, float):
            if abs(float(actual) - expected) > TOL:
                errors.append(f"{'.'.join(path)} expected {expected}, got {actual}")
        elif actual != expected:
            errors.append(f"{'.'.join(path)} expected {expected!r}, got {actual!r}")

    if errors:
        print("FAIL: codex majority-vote checks diverge:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("OK: codex majority-vote headline checks match the revised manuscript")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
