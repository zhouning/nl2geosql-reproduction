"""Build the v7_codex majority-vote tables from frozen JSONL records.

This script mirrors the statistical convention used in the revised IJGIS
manuscript:

* cap each condition/family to N=3 samples;
* reduce repeated stochastic samples to one question-level majority vote;
* run one exact two-sided McNemar test on the per-question table.

It writes ``tables/built/codex_majority_vote.json``. No LLM API, PostgreSQL
server, GPU, or row-level operational data are required.
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "data" / "results"

FOCUSED_FAMILY = "gemini-3.5-flash"
FOCUSED_A_RUN = RESULTS / "v7_gemini35_minimod_n3_20260524"
FOCUSED_B_RUN = RESULTS / "v7_gemini35_recheck_n3_2026-05-22_095253"
FOCUSED_C_RUN = FOCUSED_A_RUN

FAMILIES = [
    ("gemini-2.5-flash", "v7_d1d6_full_n3_2026-05-15_193934", "gemini-2.5-flash"),
    ("gemini-2.5-pro", "v7_d1d6_full_n3_2026-05-15_193934", "gemini-2.5-pro"),
    ("gemini-3.1-flash-lite-preview", "v7_d1d6_full_n3_2026-05-15_193934", "gemini-3.1-flash-lite-preview"),
    ("gemini-3.1-pro-preview", "v7_d1d6_full_n3_2026-05-15_193934", "gemini-3.1-pro-preview"),
    ("gemini-3.5-flash", "v7_gemini35_recheck_n3_2026-05-22_095253", "gemini-3.5-flash"),
    ("deepseek-v4-flash", "v7_d1d6_full_n3_2026-05-15_193934", "deepseek-v4-flash"),
    ("deepseek-v4-pro", "v7_d1d6_full_n3_2026-05-15_193934", "deepseek-v4-pro"),
    ("qwen3.6-flash", "v7_d1d6_full_n3_2026-05-15_193934", "qwen3.6-flash"),
    ("qwen3.6-plus", "v7_d1d6_full_n3_2026-05-15_193934", "qwen3.6-plus"),
    ("qwen3.7-max", "v7_qwen37max_n3_2026-05-22_095715", "qwen3.7-max"),
    ("gemma-4-31b-it", "v7_d1d6_full_n3_2026-05-15_193934", "gemma-4-31b-it-ollama"),
]

SUBSETS = [
    ("overall", "Overall (125q)", lambda r: True),
    ("robust", "Robustness (40q)", lambda r: r.get("difficulty") == "Robustness"),
    ("spatial", "Spatial (85q)", lambda r: r.get("difficulty") != "Robustness"),
    ("easy", "Easy (24q)", lambda r: r.get("difficulty") == "Easy"),
    ("medium", "Medium (36q)", lambda r: r.get("difficulty") == "Medium"),
    ("hard", "Hard (25q)", lambda r: r.get("difficulty") == "Hard"),
]


def load_samples(run_dir: Path, family: str, mode: str, cap: int = 3) -> list[list[dict]]:
    fam_dir = run_dir / family
    out: list[list[dict]] = []
    for sample_dir in sorted(fam_dir.glob("sample_*"), key=lambda p: int(p.name.split("_")[1])):
        path = sample_dir / f"records_{mode}.jsonl"
        if not path.exists():
            continue
        records = [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]
        if len(records) == 125:
            out.append(records)
        if len(out) >= cap:
            break
    return out


def majority_vote(samples: list[list[dict]]) -> dict[str, dict]:
    votes: dict[str, list[int]] = defaultdict(list)
    meta: dict[str, dict] = {}
    for records in samples:
        for record in records:
            qid = record["qid"]
            votes[qid].append(int(record["ex"]))
            meta[qid] = record
    return {
        qid: {
            "ex": 1 if sum(sample_votes) > len(sample_votes) / 2 else 0,
            "difficulty": meta[qid].get("difficulty", "?"),
            "category": meta[qid].get("category", "?"),
        }
        for qid, sample_votes in votes.items()
    }


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) * (0.5**n)
    return min(1.0, 2 * tail)


def mv_rate(mv_table: dict[str, dict], filter_fn) -> tuple[float, int]:
    rows = [value["ex"] for value in mv_table.values() if filter_fn(value)]
    return round(sum(rows) / len(rows) * 100, 2), len(rows)


def paired_mv(mv_a: dict[str, dict], mv_b: dict[str, dict], filter_fn) -> dict:
    qids = [qid for qid in sorted(set(mv_a) & set(mv_b)) if filter_fn(mv_a[qid])]
    b = sum(1 for qid in qids if mv_a[qid]["ex"] == 1 and mv_b[qid]["ex"] == 0)
    c = sum(1 for qid in qids if mv_a[qid]["ex"] == 0 and mv_b[qid]["ex"] == 1)
    a_pass = sum(mv_a[qid]["ex"] for qid in qids)
    b_pass = sum(mv_b[qid]["ex"] for qid in qids)
    return {
        "delta": round((b_pass - a_pass) / len(qids) * 100, 2),
        "p": round(mcnemar_exact(b, c), 4),
        "b": b,
        "c": c,
        "n_questions": len(qids),
    }


def focused_three_condition() -> dict:
    mv_a = majority_vote(load_samples(FOCUSED_A_RUN, FOCUSED_FAMILY, "baseline"))
    mv_b = majority_vote(load_samples(FOCUSED_B_RUN, FOCUSED_FAMILY, "full"))
    mv_c = majority_vote(load_samples(FOCUSED_C_RUN, FOCUSED_FAMILY, "full"))

    out = {}
    for key, label, filter_fn in SUBSETS:
        a_rate, n = mv_rate(mv_a, filter_fn)
        b_rate, _ = mv_rate(mv_b, filter_fn)
        c_rate, _ = mv_rate(mv_c, filter_fn)
        out[key] = {
            "label": label,
            "n_questions": n,
            "A_no_grounding": a_rate,
            "B_grounding_only": b_rate,
            "C_grounding_minimod": c_rate,
            "B_minus_A": paired_mv(mv_a, mv_b, filter_fn),
            "C_minus_B": paired_mv(mv_b, mv_c, filter_fn),
            "C_minus_A": paired_mv(mv_a, mv_c, filter_fn),
        }
    return out


def cross_family() -> dict:
    out = {}
    for family_label, run_name, family_dir in FAMILIES:
        mv_a = majority_vote(load_samples(RESULTS / run_name, family_dir, "baseline"))
        mv_b = majority_vote(load_samples(RESULTS / run_name, family_dir, "full"))
        row = {}
        for key, label, filter_fn in SUBSETS:
            if key not in {"spatial", "robust", "medium"}:
                continue
            row[key] = {
                "label": label,
                **paired_mv(mv_a, mv_b, filter_fn),
            }
        out[family_label] = row
    return out


def main() -> int:
    out = {
        "convention": "N=3 question-level majority vote followed by one exact two-sided McNemar test per subset",
        "focused_three_condition": focused_three_condition(),
        "cross_family": cross_family(),
    }
    target = REPO / "tables" / "built" / "codex_majority_vote.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {target.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
