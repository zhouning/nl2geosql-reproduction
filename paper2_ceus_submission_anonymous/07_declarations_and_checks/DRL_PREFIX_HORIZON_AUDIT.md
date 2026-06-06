# DRL prefix-horizon decoding audit

Experiment: deterministic paired-inference decoding of the 30 already-trained MaskablePPO policies at B = {25, 50}, while keeping the environment horizon fixed at the training-time 100-pair horizon. This tests whether the alternative-budget DRL result depends on changing the normalized progress feature by setting the episode length to 2B.

## Generated files

- `drl_budget_prefix100_sensitivity_full.csv`: 60 rows, covering 2 budgets x 3 regions x 2 DRL configurations x 5 seeds.
- `drl_budget_prefix100_summary.csv`: 12 method-level rows.
- `drl_budget_prefix100_vs_local.csv`: 6 region-budget comparisons against the local budget-sensitivity frontier.
- `drl_budget_prefix100.log`: execution log.
- `drl_budget_prefix100_sensitivity_audit.json`: machine-readable run metadata.

## Main comparison

| Region | B | Prefix DRL mean slope % | Prefix best DRL slope % | Native DRL mean slope % | Native best DRL slope % | Slope-exact local slope % |
|---|---:|---:|---:|---:|---:|---:|
| A | 25 | +0.30 | -0.47 | +0.35 | -0.53 | -5.05 |
| A | 50 | +0.17 | -1.26 | +0.17 | -1.08 | -7.33 |
| B | 25 | +0.19 | -0.33 | +0.24 | -0.05 | -3.24 |
| B | 50 | +0.69 | +0.15 | +0.73 | +0.36 | -5.14 |
| C | 25 | -0.66 | -1.18 | -0.63 | -1.05 | -2.43 |
| C | 50 | -1.18 | -2.05 | -1.22 | -2.25 | -3.83 |

## Verification notes

- All 60 deterministic prefix-horizon rollouts completed the requested budget and preserved farmland count.
- Compared with native-horizon decoding, DRL mean slope outcomes changed by at most 0.052 percentage points across the six region-budget pairs.
- Best-run slope outcomes changed by at most 0.287 percentage points.

## Interpretation

The qualitative conclusion is unchanged when B = 25 and B = 50 are decoded as prefixes of the training-time 100-pair horizon. The slope-exact local baseline still outperforms the best DRL rollout in all six tested region-budget pairs. The native-budget DRL result is therefore not an artefact of changing only the normalized progress feature.

## Boundary

This audit covers smaller-budget prefix decoding only. It does not address B = 200, because a 200-pair episode cannot be represented as a prefix of the 100-pair training horizon.
