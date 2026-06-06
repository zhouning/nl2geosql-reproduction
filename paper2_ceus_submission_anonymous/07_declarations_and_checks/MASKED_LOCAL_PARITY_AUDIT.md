# No-Reuse Local Parity Audit

## Purpose

This audit tests whether the contiguity-aware exact-delta local baseline gains an unfair advantage from a looser feasible set than the Maskable PPO evaluation environment.

The DRL environment marks selected swappable parcels as converted, so a parcel cannot be selected again within one episode. The original local sweep ranks over the current farmland and forest sets. The audit re-runs the seven-weight local sweep with an explicit no-reuse mask that removes both parcels in each committed swap from subsequent candidate sets.

## Protocol

- Regions: A, B, and C.
- Budget: 100 paired farmland-forest exchanges.
- Scalarisation weights: `lambda_cont = {0, 0.25, 0.5, 1, 2, 4, 8}`.
- Modes: unrestricted local ranking and no-reuse local ranking.
- Outputs:
  - `masked_local_parity.py`
  - `masked_local_parity.csv`
  - `masked_local_parity_summary.csv`
  - `masked_local_parity_audit.json`

## Key Results

- The slope-exact setting (`lambda_cont = 0`) is unchanged by the no-reuse mask in all three regions.
- The no-reuse local grid still Pareto-dominates all 6 DRL mean outcomes.
- Individual deterministic rollout dominance is 24/30 under no-reuse, compared with 27/30 under the unrestricted local grid.
- The largest slope shift between unrestricted and no-reuse local ranking is 2.187 percentage points, occurring in Region A at high contiguity weights.

## Boundary

This audit checks action-mask parity between local ranking and DRL evaluation. It does not turn local ranking into a globally optimized planner, and it does not rule out stronger tuned metaheuristics such as NSGA-II, simulated annealing, tabu search, or a substantially larger-budget GA.
