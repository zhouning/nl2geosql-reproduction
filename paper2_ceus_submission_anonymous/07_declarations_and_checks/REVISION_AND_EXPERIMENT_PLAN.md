# CEUS Paper 2 Revision and Experiment Plan

## Core Argument After Revision

In cadastral-style land-use decision support, this paper shows that Maskable PPO does not Pareto-dominate transparent local baselines under the tested synthetic-parcel settings, supported by 30 trained policies across three regions, exact-delta Greedy comparisons, a seven-weight contiguity-aware exact-delta local sweep, stochastic-vs-deterministic inference tests, and neighbour-overlap analysis. The claim stops at the tested synthetic-parcel benchmark, Maskable PPO, scorer-MLP architecture, deterministic paired-inference protocol, and sampled local scalarisation weights.

## Experiment Completed After Review

### Contiguity-Aware Exact-Delta Local Baseline

Status: completed and integrated into the main manuscript.

Design:
- Evaluated every feasible farmland-forest swap by exact area-weighted slope delta and exact contiguity delta.
- Used the scalar score `normalized slope improvement + lambda_cont * normalized contiguity improvement`.
- Swept `lambda_cont = {0, 0.25, 0.5, 1, 2, 4, 8}` across Regions A, B, and C.
- Used the same 100-pair exchange budget and farmland-count conservation as DRL paired-inference.
- Verified that `lambda_cont = 0` exactly reproduces the previous exact-delta Greedy result.

Main result:
- The local grid dominates all six DRL mean outcomes.
- It dominates 27/30 individual deterministic DRL seed outcomes.
- It does not dominate three individual DRL runs: A EntOnly seed 3, C Lagrangian seed 1, and C EntOnly seed 1.
- Therefore the paper now claims that DRL does not Pareto-dominate transparent local ranking, not that every DRL run is dominated.

Generated audit files:
- `contiguity_aware_local_summary.csv`
- `contiguity_aware_local_dominance.csv`
- `CONTIGUITY_AWARE_LOCAL_BASELINE_AUDIT.md`

## Manuscript Revisions Already Required

- Make the manuscript self-contained and remove any dependence on unpublished companion papers.
- Frame the paper for CEUS as computer-based land-use decision support, not only as a GIScience benchmark.
- Replace broad DRL claims with bounded claims about the tested Maskable PPO and scorer-MLP family.
- Treat exact-delta Greedy vs DRL as a slope-contiguity tradeoff, not a simple DRL failure.
- Remove title-page statements saying the paper builds on manuscripts under review or submitted elsewhere.

## Experiments Strongly Recommended Before Submission

### 1. Contiguity-Aware Local Search or Greedy Baseline

Status: completed; retained here as rationale for the experiment design.

Purpose: address the strongest reviewer objection that exact-delta Greedy optimises slope but not the joint slope-contiguity decision-support problem.

Minimum design:
- Add a local baseline that evaluates each feasible farmland-forest swap by a scalarised change in area-weighted slope and contiguity.
- Sweep at least 5 contiguity weights to produce a local-search Pareto curve.
- Evaluate the same three regions and the same 100-pair exchange budget.
- Report slope change, contiguity change, runtime, and whether any local baseline Pareto-dominates DRL.

Expected value:
- If the local baseline also dominates or matches DRL, the practical decision-support conclusion becomes much stronger.
- If DRL remains uniquely strong on contiguity, the paper can present a more balanced and credible tradeoff.

### 2. CV(area) Sensitivity Test

Purpose: address the limitation that SLIC parcel CV(area) is below the target for real cadastral data.

Minimum design:
- Use synthetic variants with different area heterogeneity levels if already available.
- Run exact-delta Greedy, slope-only Greedy, random, and at least one trained or transferred DRL setting where feasible.
- Report how the DRL-Greedy slope gap changes with CV(area).

Expected value:
- This directly tests whether the central conclusion is stable as parcels become more cadastral-like.
- If full DRL retraining is too expensive, report the greedy/random sensitivity and mark DRL retraining as future work.

### 3. Budget-Ratio Sensitivity

Purpose: test the mechanism that low exchange-budget ratio weakens sequential dependencies.

Minimum design:
- Evaluate B = 25, 50, 100, and 200 paired exchanges where the environment supports it.
- Compare exact-delta Greedy, slope-only Greedy, random, and available DRL policies.
- Report whether neighbour-overlap and DRL relative performance increase with B / N_swap.

Expected value:
- This provides mechanism-level evidence for the near-independence interpretation.

## Experiments That Would Strengthen But Are Not Strictly Required

- Tuned stochastic metaheuristic baseline: larger-budget GA, simulated annealing, tabu search, or NSGA-II.
- Inference-time decoding sweep: temperature sampling, top-k sampling, or beam-style paired decoding across all three regions.
- Graph or pair-scoring DRL baseline: GNN policy or pairwise compatibility scorer, if time and implementation capacity permit.
- Expanded geographic envelope: regenerate synthetic regions from another topographic setting to test transfer of the conclusion.

## Claim-Evidence Map

| Claim | Current evidence | Status |
|---|---|---|
| Exact-delta Greedy outperforms Maskable PPO on slope in the tested regions | Three-region table and bootstrap CIs | Supported |
| DRL preserves contiguity better than exact-delta Greedy | Cross-region slope-contiguity comparison | Supported |
| No tested method Pareto-dominates the others | Current slope-contiguity results | Supported for tested methods |
| Local-ranking baselines should be mandatory before DRL deployment | Strong slope results plus runtime gap | Supported as a bounded decision-support recommendation |
| Classical heuristics suffice for the sampled multi-objective problem | Seven-weight contiguity-aware exact-delta local sweep | Supported for sampled weights; continuous Pareto frontier not exhausted |
| Synthetic parcels represent real cadastral parcels | Aggregate calibration, but CV(area) remains low | Partially supported |
| Near-independence explains the DRL-Greedy gap | Neighbour-overlap and stochastic decoding analyses | Plausible, needs sensitivity evidence |

## Pre-Submission Priority

The highest-priority additional experiment has now been completed. Remaining optional strengthening work would be CV(area) sensitivity, budget-ratio sensitivity, or a tuned multi-objective metaheuristic baseline; these are not required for the revised central claim, but would further test generality.
