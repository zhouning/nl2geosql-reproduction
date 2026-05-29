# Reproduction package — Grounding-induced spatial regression in NL2GeoSQL on CQ-125

> Anonymous reproduction repository for the IJGIS submission.
> Code, prompts, benchmark questions, and frozen LLM evaluation outputs needed
> to reproduce every number in the paper's headline tables.

## What this repository contains

| Path | Contents |
|---|---|
| `code/eval/` | Four offline analysis scripts (no LLM API needed) |
| `code/prompts/` | The five prompt families used in the paper (`gemini`, `gemini-3.5-flash`, `deepseek`, `qwen`, `gemma`) plus shared `domain_facts.md` |
| `data/benchmark/` | The 125-question CQ-125 benchmark (questions + gold SQL + metadata), the 40-question robustness split, and a `schema.sql` structure-only dump of the 11 PostGIS tables referenced by gold SQL (no row data — reproduction does not require a database) |
| `data/results/` | Frozen `records_baseline.jsonl` and `records_full.jsonl` for every (family × sample) cell — 11 families × N=3 samples × 2 modes = 66 JSONL files |
| `tables/build_tables.py` | Regenerates Table 4 (cross-family absolute EX) as JSON |
| `tables/expected/` | Frozen ground truth — every published table cell, committed |
| `tables/verify_tables.py` | Diffs `built/` against `expected/`; CI gate |

## One-command reproduction

```bash
pip install -r requirements.txt   # ~5 packages, no LLM API, no PostgreSQL
python tables/build_tables.py
python tables/verify_tables.py    # exits 0 iff everything matches the paper
```

Expected last line: `OK: tables/built/table4.json matches tables/expected/table4.json (11 families)`.

## Reproducing each paper table

**Table 4 (cross-family absolute EX, 11 families):**
```bash
python code/eval/cross_family_absolute_ex.py
```
The `# TeX-ready rows` block at the bottom is the verbatim `tabular` body
used in the paper.

**Table 5 (cross-family paired Δ + McNemar):**
```bash
python code/eval/cross_family_grounding_effect.py
```

**Tables 2–3 (gemini-3.5-flash three-condition cells + paired Δ):**
```bash
python code/eval/three_factor_analysis.py
```

**Per-family deep-dive (failure-bin transitions, top categories, etc.):**
```bash
python code/eval/post_analysis.py \
  --run-dir data/results/v7_d1d6_full_n3_2026-05-15_193934 \
  --family deepseek-v4-flash
```

## Method summary (anchored to this code)

The paper studies the **grounding effect** on PostGIS NL2SQL: paired comparison
of `records_baseline.jsonl` (no schema-aware grounding context, "cell A") against
`records_full.jsonl` (with grounding context, "cell B") on the same 125
questions. The headline finding is that on `gemini-3.5-flash`, grounding
*degrades* spatial-subset execution accuracy by 12.16 pp (paired McNemar
$p{=}0.001$) while concurrently lifting robustness-subset accuracy by 30.83 pp.
Cross-family evaluation across 11 LLMs (the JSONL in `data/results/`) shows
this pathology is unique to `gemini-3.5-flash`; the other 10 families gain on
both subsets.

For the analysis tools cited in the paper:
* `cross_family_absolute_ex.py` — Table 4 (the new addition: per-family A/B
  absolute EX with sd, plus paired Δ).
* `cross_family_grounding_effect.py` — paired McNemar across all 11 families
  for every (subset × difficulty) cell.
* `three_factor_analysis.py` — A/B/C three-condition decomposition for
  `gemini-3.5-flash` (no grounding / grounding only / grounding + mini-mod).
* `post_analysis.py` — full per-family report including failure-bin
  transitions, top-category Δ, and unknown-bin sub-classification.

## Data layout (read by all scripts)

```
data/results/<run-dir>/<family>/sample_<N>/records_<mode>.jsonl
                                                   └── baseline | full
```

Each JSONL line is one (qid, family, sample, mode) evaluation, with fields
documented in `docs/REPRODUCE.md`. `mode == "baseline"` is the no-grounding
condition (cell A); `mode == "full"` is the grounding condition (cell B). The
analysis pipeline never re-invokes any LLM — all reduction is from these
frozen outputs.

## Why no LLM API is needed

The 11 LLMs were sampled at evaluation time and their outputs frozen in the
JSONL files committed here. Every paper number is a deterministic reduction
over these JSONL — `verify_tables.py` exits non-zero if any reduction drifts.
This makes the published claim falsifiable in the strict sense: if a reviewer
re-runs `verify_tables.py` and it reports anything other than `OK`, the paper
is wrong. Re-evaluating the LLMs themselves (i.e. drawing fresh samples) is
out of scope for reproduction.

## License

Code: MIT (`LICENSE`).
Data and benchmark: CC-BY 4.0.

## Citation

Will be added on acceptance. For now, please cite the IJGIS submission DOI
(in the abstract metadata of the submission system).

## Anonymity statement

This repository is published anonymously for double-blind peer review. The
authors will append their identities, ORCIDs, and institutional affiliations
on acceptance. Please do not de-anonymize via repository ownership inspection
during review.

> **Note on LLM-hallucinated absolute paths.** A small number of `pred_sql`
> fields in `data/results/` contain LLM-generated absolute filesystem paths
> (e.g. `D:/adk/...` references inside `pg_read_file(...)` calls). These are
> faithful records of model output during evaluation and reflect the
> evaluator's filesystem at evaluation time. They do not affect any reduction
> in the analysis pipeline (the queries fail with `permission denied`
> regardless of path), and are preserved verbatim rather than scrubbed,
> because the integrity of frozen LLM outputs is a stronger reproducibility
> guarantee than aesthetic anonymisation. The path string contains no author
> or institutional identifiers.
