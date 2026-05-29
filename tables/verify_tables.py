"""Verify built tables match the frozen expected values.

Exits with non-zero status if any cell drifts beyond tolerance, so this script
is suitable as a CI gate. Prints a unified-diff-like summary of any divergences.
"""
from __future__ import annotations
import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOL = 0.01  # absolute tolerance in pp; mean/sd values are stored to 2 dp


def diff_cells(name: str, expected: dict, built: dict, errors: list[str]) -> None:
    if expected.keys() != built.keys():
        errors.append(f"{name}: key set differs "
                      f"(expected={sorted(expected)}, built={sorted(built)})")
        return
    for k in expected:
        ev, bv = expected[k], built[k]
        if isinstance(ev, dict) and isinstance(bv, dict):
            for sub in ev:
                e_, b_ = ev[sub], bv.get(sub)
                if isinstance(e_, (int, float)) and isinstance(b_, (int, float)):
                    if abs(e_ - b_) > TOL:
                        errors.append(f"{name} {k}.{sub}: expected {e_}, got {b_}")
                elif e_ != b_:
                    errors.append(f"{name} {k}.{sub}: expected {e_!r}, got {b_!r}")
        elif isinstance(ev, (int, float)) and isinstance(bv, (int, float)):
            if abs(ev - bv) > TOL:
                errors.append(f"{name} {k}: expected {ev}, got {bv}")
        elif ev != bv:
            errors.append(f"{name} {k}: expected {ev!r}, got {bv!r}")


def main() -> int:
    expected = json.loads((REPO / "tables/expected/table4.json").read_text(
        encoding="utf-8"))
    built_path = REPO / "tables/built/table4.json"
    if not built_path.exists():
        print(f"FAIL: {built_path.relative_to(REPO)} does not exist; "
              f"run `python tables/build_tables.py` first", file=sys.stderr)
        return 2
    built = json.loads(built_path.read_text(encoding="utf-8"))

    errors: list[str] = []
    exp_fams = {r["family"]: r for r in expected["families"]}
    bui_fams = {r["family"]: r for r in built["families"]}
    if set(exp_fams) != set(bui_fams):
        only_exp = sorted(set(exp_fams) - set(bui_fams))
        only_bui = sorted(set(bui_fams) - set(exp_fams))
        if only_exp:
            errors.append(f"families missing from built: {only_exp}")
        if only_bui:
            errors.append(f"families unexpected in built: {only_bui}")

    for fam in sorted(set(exp_fams) & set(bui_fams)):
        diff_cells(fam, exp_fams[fam], bui_fams[fam], errors)

    if errors:
        print("FAIL: built tables diverge from expected:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"OK: tables/built/table4.json matches tables/expected/table4.json "
          f"({len(bui_fams)} families)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
