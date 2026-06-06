# Two-step lookahead local-search audit

## Purpose

This audit tests whether the exact-delta local-ranking baseline is too myopic.
At each paired exchange, the diagnostic first identifies the top-5 immediate
scalarised swaps, temporarily applies each candidate, evaluates the best next
immediate swap, and commits the first swap with the largest two-step score.

The scalarised objective is the same normalized slope-contiguity objective used
in the contiguity-aware local sweep. The tested weights are
`lambda_cont = {0, 0.5, 1}`, covering the slope-exact setting and the key
non-negative-contiguity settings for Regions A-C.

## Outputs

- Full output: `two_step_lookahead_local.csv`
- Summary: `two_step_lookahead_summary.csv`
- Script: `two_step_lookahead_local.py`
- Audit JSON: `two_step_lookahead_audit.json`

## Result summary

| Region | lambda | One-step slope % | Lookahead slope % | Diff pp | One-step cont. | Lookahead cont. | Diff cont. |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 0.0 | -9.656 | -9.656 | 0.000 | -0.5487 | -0.5487 | 0.0000 |
| A | 0.5 | -5.927 | -5.879 | +0.048 | -0.0142 | -0.0106 | +0.0035 |
| A | 1.0 | -0.910 | -0.831 | +0.079 | +0.2496 | +0.2549 | +0.0053 |
| B | 0.0 | -7.643 | -7.643 | +0.000 | -0.1742 | -0.1732 | +0.0010 |
| B | 0.5 | -6.186 | -6.191 | -0.005 | +0.0050 | +0.0070 | +0.0020 |
| B | 1.0 | -1.968 | -2.122 | -0.154 | +0.1411 | +0.1381 | -0.0030 |
| C | 0.0 | -5.871 | -5.871 | 0.000 | -0.1614 | -0.1614 | 0.0000 |
| C | 0.5 | -5.086 | -5.090 | -0.004 | -0.0258 | -0.0262 | -0.0004 |
| C | 1.0 | -2.831 | -2.831 | 0.000 | +0.1073 | +0.1073 | 0.0000 |

## Interpretation

The two-step audit does not reveal a hidden sequential advantage missed by
one-step local ranking. The largest slope difference is 0.154 percentage points,
and the largest contiguity difference is 0.0053. The slope-exact setting is
effectively unchanged. This supports the manuscript's near-independence
interpretation while remaining bounded to top-5 two-step lookahead rather than
global planning optimality.
