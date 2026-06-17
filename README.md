# Reproduction package - subset-decomposed grounding effects in NL2GeoSQL on CQ-125

> Public reproduction repository for the associated manuscript:
> "Schema-Aware Grounding Effects in PostGIS Natural-Language-to-SQL:
> A Subset-Decomposed Evaluation Across Eleven LLMs".
> It contains the code, prompts, benchmark questions, and frozen LLM evaluation
> outputs needed to reproduce the subset-decomposed grounding analyses.

## What this repository contains

| Path | Contents |
|---|---|
| `code/eval/` | Offline analysis scripts; no LLM API is needed |
| `code/prompts/` | The five prompt families used in the paper (`gemini`, `gemini-3.5-flash`, `deepseek`, `qwen`, `gemma`) plus shared `domain_facts.md` |
| `data/benchmark/` | The 125-question CQ-125 benchmark, the 40-question robustness split, and a structure-only `schema.sql` dump of the 11 PostGIS tables referenced by gold SQL |
| `data/results/` | Frozen baseline and full-mode JSONL records for the 11-family N=3 panel, plus the balanced N=5 `gemini-3.5-flash` A/B/C diagnostic records |
| `tables/build_tables.py` / `tables/verify_tables.py` | Legacy per-sample cross-family absolute-EX table gate retained for continuity |
| `tables/build_codex_tables.py` / `tables/verify_codex_tables.py` | Current manuscript checks: question-level majority vote followed by exact two-sided McNemar tests |
| `docs/REPRODUCE.md` | Step-by-step reproduction guide |

The repository intentionally does not include journal submission PDFs, cover
letters, LaTeX submission bundles, or transfer-history documents. Those files
belong in the private submission package, not in the public reproduction repo.

## Quick test / example reproduction

The following commands rebuild the derived table files from frozen records and
verify them against the expected manuscript values. The test requires no LLM
API, no PostgreSQL or PostGIS database, and no GPU.

```bash
pip install -r requirements.txt
python tables/build_tables.py
python tables/verify_tables.py
python tables/build_codex_tables.py
python tables/verify_codex_tables.py
```

Expected lines include:

```text
OK: tables/built/table4.json matches tables/expected/table4.json (11 families)
OK: codex majority-vote headline checks match the revised manuscript
```

## Reproducing each paper table

### Legacy cross-family absolute EX

```bash
python code/eval/cross_family_absolute_ex.py
```

The `# TeX-ready rows` block at the bottom is the verbatim `tabular` body used
in an earlier draft and is retained for auditability.

### Legacy paired delta across families

```bash
python code/eval/cross_family_grounding_effect.py
```

This diagnostic reports paired effects across subsets under an earlier
per-sample/pooled convention. It is retained for comparison with earlier drafts;
the current manuscript uses question-level majority-vote reductions.

### Current manuscript majority-vote headline checks

```bash
python tables/build_codex_tables.py
python tables/verify_codex_tables.py
```

This is the authoritative check for the manuscript's headline values. The
cross-family panel remains capped at `N=3` for comparability across all 11
families. The focused `gemini-3.5-flash` A/B/C diagnostic is balanced at `N=5`.
Both analyses reduce repeated stochastic samples to one question-level majority
vote and then apply one exact two-sided McNemar test per subset.

### Focused gemini-3.5-flash three-condition cells

```bash
python code/eval/three_factor_analysis.py
```

### Per-family deep dive

```bash
python code/eval/post_analysis.py \
  --run-dir data/results/v7_d1d6_full_n3_2026-05-15_193934 \
  --family deepseek-v4-flash
```

## Method summary

The paper studies the grounding effect on PostGIS NL2SQL: paired comparison of
`records_baseline.jsonl` (no schema-aware grounding context, cell A) against
`records_full.jsonl` (with grounding context, cell B) on the same 125 questions.
The current manuscript uses a de-pooled statistical convention: question-level
majority vote across repeated stochastic samples followed by one exact
two-sided McNemar test on the per-question table.

The cross-family panel uses `N=3` for all 11 families. Under this convention,
grounding improves the Robustness subset for all 11 families by point estimate,
whereas Spatial effects are heterogeneous across families. The most negative
cross-family panel estimate is `gemini-3.5-flash` on Spatial (`delta=-10.59 pp`,
`p=0.136`), so the paper treats it as a negative-tail observation rather than a
confirmed stable family-level regression. A balanced `N=5` focused
three-condition diagnostic on `gemini-3.5-flash` gives Spatial `B-A=-10.59 pp`
(`b/c=19/10`, `p=0.136`) and Robustness `B-A=+27.50 pp` (`p=0.0010`) under the
same question-level majority-vote convention.

## Data layout

```text
data/results/<run-dir>/<family>/sample_<N>/records_<mode>.jsonl
                                                   |-- baseline | full
```

Each JSONL line is one `(qid, family, sample, mode)` evaluation, with fields
documented in `docs/REPRODUCE.md`. `mode == "baseline"` is the no-grounding
condition; `mode == "full"` is the grounding condition. The analysis pipeline
never re-invokes any LLM; all reductions are from these frozen outputs.

## Why no LLM API is needed

The 11 LLM families were sampled at evaluation time and their outputs were
frozen in the JSONL files committed here. Every manuscript number is a
deterministic reduction over these records. `verify_tables.py` and
`verify_codex_tables.py` exit non-zero if a checked reduction drifts.
Re-evaluating the LLMs themselves is out of scope for this reproduction package.

## License

Code: MIT (`LICENSE`).
Data and benchmark: CC-BY 4.0.

## Citation

The manuscript DOI will be added when available. Until then, please cite this
repository URL and the associated manuscript title.

## Repository status

This public GitHub repository is the reproduction repository cited by the
associated manuscript. It is intended for public download and inspection without
credentials, and it contains the source files, README, quick-test commands, and
license information needed for code and data availability review.

> **Note on LLM-hallucinated absolute paths.** A small number of `pred_sql`
> fields in `data/results/` contain LLM-generated absolute filesystem paths
> such as `D:/adk/...` references inside `pg_read_file(...)` calls. These are
> faithful records of model output during evaluation and do not affect any
> reduction in the analysis pipeline. They are preserved verbatim because the
> integrity of frozen LLM outputs is a stronger reproducibility guarantee than
> cosmetic anonymisation. The path string contains no author or institutional
> identifiers.
