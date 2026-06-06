# Reproduction package — subset-decomposed grounding effects in NL2GeoSQL on CQ-125

> Reproduction repository for the Computers & Geosciences submission.
> Code, prompts, benchmark questions, and frozen LLM evaluation outputs needed
> to reproduce the paper's subset-decomposed grounding analyses.

## What this repository contains

| Path | Contents |
|---|---|
| `code/eval/` | Offline analysis scripts (no LLM API needed) |
| `code/prompts/` | The five prompt families used in the paper (`gemini`, `gemini-3.5-flash`, `deepseek`, `qwen`, `gemma`) plus shared `domain_facts.md` |
| `data/benchmark/` | The 125-question CQ-125 benchmark (questions + gold SQL + metadata), the 40-question robustness split, and a `schema.sql` structure-only dump of the 11 PostGIS tables referenced by gold SQL (no row data — reproduction does not require a database) |
| `data/results/` | Frozen `records_baseline.jsonl` and `records_full.jsonl` for the 11-family N=3 cross-family panel, plus the balanced N=5 `gemini-3.5-flash` A/B/C diagnostic records |
| `tables/build_tables.py` / `tables/verify_tables.py` | Legacy per-sample cross-family absolute-EX table gate retained for continuity |
| `tables/build_codex_tables.py` / `tables/verify_codex_tables.py` | Revised manuscript checks: question-level majority vote followed by exact two-sided McNemar tests |
| `paper/computers_geosciences_2026/` | Current Computers & Geosciences manuscript PDF, supplementary material, LaTeX source package, and source result tables |

## One-command reproduction

```bash
pip install -r requirements.txt   # ~5 packages, no LLM API, no PostgreSQL
python tables/build_tables.py
python tables/verify_tables.py    # exits 0 iff everything matches the paper
python tables/build_codex_tables.py
python tables/verify_codex_tables.py
```

Expected last line: `OK: tables/built/table4.json matches tables/expected/table4.json (11 families)`.
For the revised Computers & Geosciences manuscript, also expect:
`OK: codex majority-vote headline checks match the revised manuscript`.

## Reproducing each paper table

**Legacy cross-family absolute EX (per-sample mean, retained for continuity):**
```bash
python code/eval/cross_family_absolute_ex.py
```
The `# TeX-ready rows` block at the bottom is the verbatim `tabular` body
used in an earlier draft.

**Legacy cross-family paired Δ + pooled/per-sample McNemar:**
```bash
python code/eval/cross_family_grounding_effect.py
```

**Revised manuscript majority-vote headline checks:**
```bash
python tables/build_codex_tables.py
python tables/verify_codex_tables.py
```

This is the authoritative check for the revised Computers & Geosciences
submission. The cross-family panel remains capped at `N=3` for comparability
across all 11 families. The focused `gemini-3.5-flash` A/B/C diagnostic is now
balanced at `N=5`. Both analyses reduce repeated stochastic samples to one
question-level majority vote and then apply one exact two-sided McNemar test
per subset.

**Focused gemini-3.5-flash three-condition cells + paired Δ:**
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
questions. The revised manuscript uses a de-pooled statistical convention:
question-level majority vote across repeated stochastic samples followed by one
exact two-sided McNemar test on the per-question table. The cross-family panel
uses `N=3` for all 11 families. Under this convention, grounding improves the
Robustness subset for all 11 families by point estimate, whereas Spatial effects
are heterogeneous across families. The most negative cross-family panel estimate
is `gemini-3.5-flash` on Spatial (`Δ=-10.59 pp`, `p=0.136`), so the paper treats
it as a negative-tail observation rather than a confirmed stable family-level
regression. A balanced `N=5` focused three-condition diagnostic on
`gemini-3.5-flash` gives Spatial `B-A=-10.59 pp` (`b/c=19/10`, `p=0.136`) and
Robustness `B-A=+27.50 pp` (`p=0.0010`) under the same question-level
majority-vote convention.

For the analysis tools cited in the paper:
* `tables/build_codex_tables.py` — revised majority-vote reductions used for
  the current Computers & Geosciences submission.
* `tables/verify_codex_tables.py` — checks the current manuscript's headline
  values (`-10.59`, `+27.50`, `+8.24`, and related p-values).
* `cross_family_absolute_ex.py`, `cross_family_grounding_effect.py`, and
  `three_factor_analysis.py` — legacy per-sample/pooled diagnostics retained
  for auditability and comparison with earlier drafts.
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

Will be added on acceptance. For now, please cite the Computers & Geosciences submission DOI
(in the abstract metadata of the submission system).

## Review-note

For double-blind review, use the anonymised review snapshot cited in the
manuscript. This GitHub repository is maintained as the permanent reproduction
repository and may contain non-anonymous manuscript materials after submission.

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
