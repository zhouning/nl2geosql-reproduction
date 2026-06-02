# Reproduction guide

This document walks through reproducing the IJGIS submission analyses. The
total runtime on a 2020-era laptop is **under 90 seconds**; no GPU, no
PostgreSQL, no LLM API key, and no network access is required.

## Environment

Python 3.10 or newer. Tested on:
* Python 3.13 / Windows 11
* Python 3.11 / Ubuntu 22.04 (CI)

```bash
python -m venv .venv
. .venv/bin/activate            # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

The dependency list is intentionally minimal. All
statistical machinery — paired t-tests, McNemar exact two-sided, Wilson 95% CIs
— is implemented in `code/eval/post_analysis.py` so that no SciPy/StatsModels
version-pinning concerns leak into the reviewer's environment.

## End-to-end smoke test

```bash
python tables/build_tables.py       # ~2 s
python tables/verify_tables.py      # ~0.5 s, exits 0 if everything matches
python tables/build_codex_tables.py
python tables/verify_codex_tables.py
```

If `verify_tables.py` exits 0, the legacy per-sample cross-family absolute-EX
table is reproduced bit-exact (to 0.01 pp) from the frozen JSONL. If
`verify_codex_tables.py` exits 0, the revised manuscript's majority-vote
headline checks match the current IJGIS submission.

## Reproducing each table

### Revised manuscript — question-level majority-vote headline checks

```bash
python tables/build_codex_tables.py
python tables/verify_codex_tables.py
```

This is the authoritative check for the revised IJGIS submission. It uses
uniform `N=3`, computes a majority-vote execution outcome per question, and then
uses one exact two-sided McNemar test on the per-question table. The verifier
checks the current headline values, including `gemini-3.5-flash` Spatial panel
`Δ=-10.59 pp, p=0.136`, focused Spatial `B-A=-14.12 pp, b/c=21/9, p=0.043`,
focused Robustness `B-A=+32.50 pp, p=0.0002`, and mini-mod Spatial
`C-B=+8.24 pp, p=0.092`.

### Legacy Table 4 — cross-family absolute EX (11 families × 2 subsets)

```bash
python code/eval/cross_family_absolute_ex.py
```

The output ends with a `# TeX-ready rows` block. These rows are retained for
auditability against earlier drafts. To inspect the LaTeX rows, redirect:

```bash
python code/eval/cross_family_absolute_ex.py | \
  awk '/# TeX-ready/,0'
```

### Legacy paired Δ across families with pooled/per-sample McNemar exact two-sided p

```bash
python code/eval/cross_family_grounding_effect.py
```

The output covers every subset (Overall, Robust, Spatial, Easy, Medium, Hard)
for every family under an earlier pooled/per-sample convention. It is kept as a
diagnostic, not as the revised manuscript's primary inferential convention.

### Legacy three-factor decomposition (gemini-3.5-flash only)

```bash
python code/eval/three_factor_analysis.py
```

Cell A (no grounding) and cell C (grounding + mini-mod) are at N=5; cell B
(grounding only, no mini-mod) is at N=3. The revised manuscript caps A and C to
`N=3` for symmetry; use `tables/build_codex_tables.py` for that convention.
Output includes:
* Per-cell EX on Overall / Robustness / Spatial / Easy / Medium / Hard
* Top-category breakdown
* Paired t-test 95% CI and McNemar exact two-sided p for B-A, C-B, C-A

### Failure-bin attribution

For any family, run:

```bash
python code/eval/post_analysis.py \
  --run-dir data/results/v7_d1d6_full_n3_2026-05-15_193934 \
  --family <family-name>
```

Valid `<family-name>` values:
`gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-3.1-flash-lite-preview`,
`gemini-3.1-pro-preview`, `deepseek-v4-flash`, `deepseek-v4-pro`,
`qwen3.6-flash`, `qwen3.6-plus`, `gemma-4-31b-it-ollama`.

For `gemini-3.5-flash` (different run directory):
```bash
python code/eval/post_analysis.py \
  --run-dir data/results/v7_gemini35_recheck_n3_2026-05-22_095253 \
  --family gemini-3.5-flash
```

For `qwen3.7-max`:
```bash
python code/eval/post_analysis.py \
  --run-dir data/results/v7_qwen37max_n3_2026-05-22_095715 \
  --family qwen3.7-max
```

## JSONL record schema

Each line in `data/results/<run-dir>/<family>/sample_<N>/records_<mode>.jsonl`
is a JSON object with these fields:

| Field | Type | Notes |
|---|---|---|
| `qid` | str | e.g. `CQ_GEO_EASY_01`, `CQ_ROBUST_SECREJ_03` |
| `category` | str | One of: Attribute Filtering, Spatial Join, KNN, Cross-Table, ... |
| `difficulty` | str | `Easy`, `Medium`, `Hard`, or `Robustness` |
| `is_robust` | bool | True iff `difficulty == "Robustness"` |
| `question` | str | Natural-language question (Chinese) |
| `gold_sql` | str | Ground-truth SQL |
| `pred_sql` | str | LLM-generated SQL |
| `ex` | int | 1 if `pred_sql` execution-equivalent to `gold_sql`, else 0 |
| `valid` | int | 1 if `pred_sql` is syntactically valid PostgreSQL, else 0 |
| `reason` | str | Free-form failure reason if `ex == 0` |
| `tokens` | int | Total tokens spent generating `pred_sql` |
| `pred_error` / `gold_error` | str | DB error strings, if any |
| `gen_status` / `gen_error` | str | Generation pipeline status |
| `hint_injection_stats` | dict | Diagnostic counters for the grounding pipeline |

The `mode` axis (`baseline` vs `full`) is encoded in the filename. `baseline`
runs the LLM with question only (no schema-aware grounding context); `full`
runs it with the complete grounding pipeline output as system context.

## Data manifest

```
data/results/v7_d1d6_full_n3_2026-05-15_193934/
   ├── deepseek-v4-flash/sample_{1,2,3}/records_{baseline,full}.jsonl
   ├── deepseek-v4-pro/...
   ├── gemini-2.5-flash/...
   ├── gemini-2.5-pro/...
   ├── gemini-3.1-flash-lite-preview/...
   ├── gemini-3.1-pro-preview/...
   ├── gemma-4-31b-it-ollama/...
   ├── qwen3.6-flash/...
   └── qwen3.6-plus/...

data/results/v7_qwen37max_n3_2026-05-22_095715/
   └── qwen3.7-max/sample_{1,2,3}/records_{baseline,full}.jsonl

data/results/v7_gemini35_recheck_n3_2026-05-22_095253/
   └── gemini-3.5-flash/sample_{1,2,3}/records_{baseline,full}.jsonl

data/results/v7_gemini35_minimod_n3_20260524/
   └── gemini-3.5-flash/sample_{1..5}/records_{baseline,full}.jsonl
       (source for cell A and cell C; revised checks cap these to N=3)
```

The N=3 vs N=5 asymmetry is described in the Limitations section of the paper.

## Troubleshooting

* **`UnicodeEncodeError: 'gbk' codec ...`** on Windows — the scripts call
  `sys.stdout.reconfigure(encoding='utf-8')` at startup, but if you're using
  a very old Python (< 3.7) this won't work. Upgrade to Python 3.10+.
* **`ModuleNotFoundError: failure_classifier`** — the eval scripts add their
  own directory to `sys.path` at import time. If you've moved them, edit the
  `sys.path.insert(...)` line near the top.
* **`tables/verify_tables.py` reports drift** — please file an issue. The
  expected values are committed to the repository at submission time and are
  intended to be bit-exact.
