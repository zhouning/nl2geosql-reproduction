"""Build paper Table 4 (cross-family absolute EX) as JSON for CI verification.

Reads the same JSONL the paper's `cross_family_absolute_ex.py` reads, but emits
a structured JSON file `tables/built/table4.json`. The CI workflow then diffs
this against `tables/expected/table4.json` (committed) — any drift in the
underlying analysis pipeline trips a build failure.
"""
from __future__ import annotations
import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "code" / "eval"))


# Mirror of FAMILIES in code/eval/cross_family_absolute_ex.py — kept here in
# reduced form (no human-readable label) so the CI table is path-stable.
FAMILIES = [
    ("gemini-2.5-flash",
     "data/results/v7_d1d6_full_n3_2026-05-15_193934", "gemini-2.5-flash"),
    ("gemini-2.5-pro",
     "data/results/v7_d1d6_full_n3_2026-05-15_193934", "gemini-2.5-pro"),
    ("gemini-3.1-flash-lite-preview",
     "data/results/v7_d1d6_full_n3_2026-05-15_193934", "gemini-3.1-flash-lite-preview"),
    ("gemini-3.1-pro-preview",
     "data/results/v7_d1d6_full_n3_2026-05-15_193934", "gemini-3.1-pro-preview"),
    ("gemini-3.5-flash",
     "data/results/v7_gemini35_recheck_n3_2026-05-22_095253", "gemini-3.5-flash"),
    ("deepseek-v4-flash",
     "data/results/v7_d1d6_full_n3_2026-05-15_193934", "deepseek-v4-flash"),
    ("deepseek-v4-pro",
     "data/results/v7_d1d6_full_n3_2026-05-15_193934", "deepseek-v4-pro"),
    ("qwen3.6-flash",
     "data/results/v7_d1d6_full_n3_2026-05-15_193934", "qwen3.6-flash"),
    ("qwen3.6-plus",
     "data/results/v7_d1d6_full_n3_2026-05-15_193934", "qwen3.6-plus"),
    ("qwen3.7-max",
     "data/results/v7_qwen37max_n3_2026-05-22_095715", "qwen3.7-max"),
    ("gemma-4-31b-it",
     "data/results/v7_d1d6_full_n3_2026-05-15_193934", "gemma-4-31b-it-ollama"),
]

SUBSETS = [
    ("spatial",  lambda r: r.get("difficulty") != "Robustness"),
    ("robust",   lambda r: r.get("difficulty") == "Robustness"),
    ("overall",  lambda r: True),
    ("medium",   lambda r: r.get("difficulty") == "Medium"),
]


def load_samples(run_dir: Path, family: str, mode: str) -> list[list[dict]]:
    fam_dir = run_dir / family
    if not fam_dir.exists():
        return []
    out = []
    for sd in sorted(fam_dir.glob("sample_*"),
                     key=lambda p: int(p.name.split("_")[1])):
        p = sd / f"records_{mode}.jsonl"
        if not p.exists():
            continue
        recs = [json.loads(l) for l in p.open(encoding="utf-8")]
        if len(recs) == 125:
            out.append(recs)
    return out


def cell(samples: list[list[dict]], filter_fn) -> dict:
    per_sample = []
    for recs in samples:
        sub = [r for r in recs if filter_fn(r)]
        if sub:
            per_sample.append(sum(r["ex"] for r in sub) / len(sub) * 100)
    if not per_sample:
        return {"mean": None, "sd": None, "n_samples": 0}
    return {
        "mean": round(statistics.mean(per_sample), 2),
        "sd": round(statistics.stdev(per_sample) if len(per_sample) > 1 else 0.0, 2),
        "n_samples": len(per_sample),
    }


def main() -> int:
    out: dict = {"families": []}
    for tex_label, run_path, fam_dir in FAMILIES:
        run = REPO / run_path
        A = load_samples(run, fam_dir, "baseline")
        B = load_samples(run, fam_dir, "full")
        if not A or not B:
            print(f"WARN: missing data for {tex_label}: A={len(A)} B={len(B)}",
                  file=sys.stderr)
            continue
        row = {"family": tex_label}
        for sub_label, fn in SUBSETS:
            row[f"{sub_label}_A"] = cell(A, fn)
            row[f"{sub_label}_B"] = cell(B, fn)
            ca, cb = row[f"{sub_label}_A"], row[f"{sub_label}_B"]
            if ca["mean"] is not None and cb["mean"] is not None:
                row[f"{sub_label}_delta"] = round(cb["mean"] - ca["mean"], 2)
        out["families"].append(row)

    target = REPO / "tables" / "built" / "table4.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False),
                      encoding="utf-8")
    print(f"wrote {target.relative_to(REPO)} ({len(out['families'])} families)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
