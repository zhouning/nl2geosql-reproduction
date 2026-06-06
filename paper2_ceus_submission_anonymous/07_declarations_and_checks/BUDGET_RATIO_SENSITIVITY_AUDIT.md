# Budget-ratio sensitivity audit

Experiment: contiguity-aware exact-delta local ranking at paired-exchange budgets B = {25, 50, 100, 200}; regions A/B/C; lambda_cont = {0, 0.25, 0.5, 1, 2, 4, 8}. This is a local-baseline sensitivity test, not DRL retraining at alternative budgets.

## Generated files

- `contiguity_aware_budget_sensitivity_full.csv`: 84 rows, covering 4 budgets x 3 regions x 7 lambda values.
- `contiguity_aware_budget_summary.csv`: 12 rows, one representative summary for each region-budget pair.
- The B=100 rerun was checked against the original 21-row contiguity-aware local-sweep output. All shared numeric columns and region/code identifiers matched exactly; maximum numeric difference was 0.

## Representative points

| Region | B | slope-exact slope % | slope-exact cont | nonneg lambda | nonneg slope % | nonneg cont |
|---|---:|---:|---:|---:|---:|---:|
| A | 25 | -5.05 | -0.170 | 0.5 | -3.87 | +0.012 |
| A | 50 | -7.33 | -0.329 | 0.5 | -5.27 | +0.002 |
| A | 100 | -9.66 | -0.549 | 1 | -0.91 | +0.250 |
| A | 200 | -9.89 | -0.653 | 1 | -0.91 | +0.250 |
| B | 25 | -3.24 | -0.048 | 0.5 | -2.70 | +0.019 |
| B | 50 | -5.14 | -0.083 | 0.5 | -4.23 | +0.023 |
| B | 100 | -7.64 | -0.174 | 0.5 | -6.19 | +0.005 |
| B | 200 | -9.57 | -0.287 | 1 | -1.75 | +0.148 |
| C | 25 | -2.43 | -0.052 | 0.5 | -2.11 | +0.006 |
| C | 50 | -3.83 | -0.088 | 1 | -2.41 | +0.054 |
| C | 100 | -5.87 | -0.161 | 1 | -2.83 | +0.107 |
| C | 200 | -8.30 | -0.287 | 1 | -3.25 | +0.172 |

## Interpretation

Slope-exact local ranking gives increasingly negative slope changes as B increases, but contiguity loss also deepens. A sampled non-negative-contiguity local point exists for every tested region-budget pair and still gives negative slope change in all 12 cases. Region A shows saturation for some high-lambda local policies between B=100 and B=200, consistent with the possibility of local cycling or exhausted beneficial moves under the unconstrained swap process.

## Boundary

These results support the robustness of the local slope-contiguity frontier to the tested intervention budgets. They do not establish DRL behaviour at B = 25, 50, or 200, because the trained DRL policies were not retrained or decoded under matched alternative-budget protocols.
