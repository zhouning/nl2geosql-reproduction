# Contiguity-aware local baseline audit

Experiment: exact paired local ranking with scalarised normalized slope and contiguity improvements, `lambda_cont` in {0, 0.25, 0.5, 1, 2, 4, 8}, 100 paired exchanges per region. Lower slope change is better; higher contiguity change is better.

## Local summary

| region | local_point | lambda_cont | slope_change_pct | cont_change | completed_pairs |
| --- | --- | --- | --- | --- | --- |
| A | slope-optimal | 0.000 | -9.656 | -0.549 | 100 |
| A | first non-negative contiguity | 1.000 | -0.910 | 0.250 | 100 |
| A | max-contiguity | 8.000 | 5.585 | 0.405 | 100 |
| B | slope-optimal | 0.000 | -7.643 | -0.174 | 100 |
| B | first non-negative contiguity | 0.500 | -6.186 | 0.005 | 100 |
| B | max-contiguity | 8.000 | 3.698 | 0.251 | 100 |
| C | slope-optimal | 0.000 | -5.871 | -0.161 | 100 |
| C | first non-negative contiguity | 1.000 | -2.831 | 0.107 | 100 |
| C | max-contiguity | 8.000 | 1.539 | 0.204 | 100 |

## Dominance versus DRL

| region | drl_method | drl_slope_mean | drl_cont_mean | dominated_by_local_mean | dominating_lambda_example | dominating_local_slope_pct | dominating_local_cont_change | drl_seed_dominated_by_local_count | n_drl_seeds_region |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | lagrangian | 1.022 | 0.112 | True | 1.000 | -0.910 | 0.250 | 9 | 10 |
| A | entonly | 0.635 | 0.067 | True | 1.000 | -0.910 | 0.250 | 9 | 10 |
| B | lagrangian | 2.190 | -0.164 | True | 0.250 | -7.116 | -0.056 | 10 | 10 |
| B | entonly | 2.158 | -0.127 | True | 0.250 | -7.116 | -0.056 | 10 | 10 |
| C | lagrangian | -2.203 | 0.048 | True | 1.000 | -2.831 | 0.107 | 8 | 10 |
| C | entonly | -1.481 | 0.068 | True | 1.000 | -2.831 | 0.107 | 8 | 10 |

## Interpretation boundary

The local lambda grid dominates all DRL mean points and 27/30 individual deterministic DRL seed outcomes. It does not dominate every individual seed: A EntOnly seed 3 and C seed 1 under both configurations remain undominated by the sampled lambda grid. The result supports a stronger local-baseline requirement but not a universal claim that local search dominates all possible DRL policies or all scalarisations.
