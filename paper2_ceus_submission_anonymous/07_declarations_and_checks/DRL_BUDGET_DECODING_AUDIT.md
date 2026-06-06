# DRL budget-decoding audit

Experiment: deterministic paired-inference decoding of the 30 already-trained MaskablePPO policies at paired-exchange budgets B = {25, 50, 100, 200}. The environment episode length was set to 2B raw actions. This is a fixed-policy decoding sensitivity test, not DRL retraining at alternative budgets.

## Generated files

- `drl_budget_sensitivity_full.csv`: 120 rows, covering 4 budgets x 3 regions x 2 DRL configurations x 5 seeds.
- `drl_budget_summary.csv`: 24 rows, one method-level summary for each region-budget-method combination.
- `drl_budget_vs_local.csv`: 12 rows, one region-budget comparison against the local budget-sensitivity frontier.
- `drl_budget_sensitivity.log`: execution log for the 120 deterministic rollouts.
- `drl_budget_sensitivity_audit.json`: machine-readable run metadata.

## Main comparison

| Region | B | DRL mean slope % | Best DRL slope % | Best DRL cont | Slope-exact local slope % |
|---|---:|---:|---:|---:|---:|
| A | 25 | +0.35 | -0.53 | +0.110 | -5.05 |
| A | 50 | +0.17 | -1.08 | +0.168 | -7.33 |
| A | 100 | +0.83 | -0.97 | +0.039 | -9.66 |
| A | 200 | +4.08 | +1.37 | -0.145 | -9.89 |
| B | 25 | +0.24 | -0.05 | -0.044 | -3.24 |
| B | 50 | +0.73 | +0.36 | -0.080 | -5.14 |
| B | 100 | +2.19 | +1.62 | -0.159 | -7.64 |
| B | 200 | +6.06 | +4.97 | -0.302 | -9.57 |
| C | 25 | -0.63 | -1.05 | +0.025 | -2.43 |
| C | 50 | -1.22 | -2.25 | +0.020 | -3.83 |
| C | 100 | -1.84 | -3.33 | +0.037 | -5.87 |
| C | 200 | -2.23 | -4.45 | +0.047 | -8.30 |

## Verification notes

- All 120 deterministic rollouts completed the requested paired budget and preserved farmland count.
- At B=100, the fresh decode reproduced the archived A/C per-seed results exactly.
- At B=100, Region B fresh decoding changed the all-policy mean slope outcome by +0.019 percentage points relative to the archived aggregate. This difference is small and does not affect any qualitative conclusion; the fixed-policy budget experiment is therefore reported as a fresh decoding sensitivity analysis rather than as a replacement for the main benchmark table.

## Interpretation

The slope-exact local baseline outperforms the best fixed-policy DRL rollout in all 12 region-budget pairs. Fixed-policy decoding does not close the local-baseline gap at smaller or larger intervention budgets. Region C benefits from larger budgets, but remains behind slope-exact local ranking; Regions A and B deteriorate under larger deterministic budgets.

## Boundary

The experiment does not test budget-specific DRL retraining, alternative curricula, or policies trained with B = 25, 50, or 200. Those remain the strongest remaining sensitivity experiment if the study needs to claim budget-adaptive DRL behaviour.
