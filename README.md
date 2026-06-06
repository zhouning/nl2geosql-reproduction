# Paper 2 CEUS Anonymous Submission Package

This repository currently hosts the anonymous submission package and audit artifacts for **Paper 2**, a Computers, Environment and Urban Systems submission on cadastral-style land-use optimisation.

The latest manuscript asks a practical decision-support question: **when parcel-level deep reinforcement learning (DRL) is expensive to train, does it add enough value over transparent exact-delta local baselines to justify deployment?**

## Current Paper 2 Message

The paper evaluates farmland-forest parcel exchange on a reproducible synthetic-parcel benchmark generated from public geospatial sources: Copernicus DEM, Impact Observatory land cover, and SLIC tessellation. The benchmark is heuristically matched to aggregate structural ranges for mountainous cadastral settings and avoids restricted cadastral boundary data.

The main empirical result is bounded but strong:

- A slope-exact local baseline reduces area-weighted farmland slope by 5.9 to 9.7 percentage points across three synthetic regions.
- A seven-weight contiguity-aware exact-delta local sweep recovers positive-contiguity local points in every region.
- The sampled local grid Pareto-dominates all 6 DRL mean outcomes and 27 of 30 deterministic DRL rollouts.
- A stricter no-reuse action-mask parity audit, matching the DRL converted-parcel constraint, leaves the slope-exact local outcomes unchanged and still dominates all 6 DRL mean outcomes; individual-run dominance is 24 of 30.
- A top-5 two-step local lookahead changes one-step local slope outcomes by at most 0.154 percentage points.
- Fixed-policy decoding across 25, 50, 100, and 200 paired exchanges does not remove the slope-exact local advantage.
- DRL learns non-trivial spatial clustering, but weak inter-swap coupling and train-evaluation mismatch limit its deterministic decision-support value.

The paper does **not** claim that all DRL or all metaheuristics fail for land-use optimisation. It makes a narrower claim: in the tested low-intervention, sparse-adjacency synthetic parcel regimes, Maskable PPO with a scorer-MLP policy did not justify its training cost relative to transparent exact-delta local diagnostics.

## Practical Implication

For CEUS-style decision support, the recommended screening workflow is:

1. Characterise the planning area: parcel-area heterogeneity, Queen degree, farm-forest ratio, candidate-pool size, and exchange-budget ratio.
2. Run transparent local diagnostics: slope-only ranking, slope-exact exact-delta ranking, and a scalarised slope-contiguity local sweep.
3. Compare the local frontier with planning thresholds.
4. Escalate to DRL or stronger metaheuristics only when the local frontier fails or when diagnostics suggest strong inter-swap coupling.

## Repository Layout

| Path | Contents |
|---|---|
| `paper2_ceus_submission_anonymous/` | Anonymous CEUS Paper 2 submission package |
| `paper2_ceus_submission_anonymous/01_main_document_anonymous/` | Anonymous manuscript PDF and TEX |
| `paper2_ceus_submission_anonymous/03_highlights/` | CEUS-style highlights |
| `paper2_ceus_submission_anonymous/05_figures/` | Standalone manuscript figures |
| `paper2_ceus_submission_anonymous/07_declarations_and_checks/` | Experiment audit scripts, logs, CSV/JSON outputs, and reviewer-facing checks |
| `paper2_ceus_submission_anonymous/CEUS_paper2_latex_source_anonymous.zip` | Anonymous LaTeX source package |
| `code/`, `data/`, `tables/`, `docs/` | Earlier NL2GeoSQL reproduction materials retained for continuity |

## Important Files

- Manuscript source: `paper2_ceus_submission_anonymous/01_main_document_anonymous/manuscript_ceus_anonymous.tex`
- Manuscript PDF: `paper2_ceus_submission_anonymous/01_main_document_anonymous/manuscript_ceus_anonymous.pdf`
- LaTeX source ZIP: `paper2_ceus_submission_anonymous/CEUS_paper2_latex_source_anonymous.zip`
- No-reuse parity audit: `paper2_ceus_submission_anonymous/07_declarations_and_checks/MASKED_LOCAL_PARITY_AUDIT.md`
- Two-step lookahead audit: `paper2_ceus_submission_anonymous/07_declarations_and_checks/TWO_STEP_LOOKAHEAD_LOCAL_AUDIT.md`
- Budget sensitivity audit: `paper2_ceus_submission_anonymous/07_declarations_and_checks/BUDGET_RATIO_SENSITIVITY_AUDIT.md`
- Fixed-policy DRL budget decoding audit: `paper2_ceus_submission_anonymous/07_declarations_and_checks/DRL_BUDGET_DECODING_AUDIT.md`
- Figure generation audit: `paper2_ceus_submission_anonymous/07_declarations_and_checks/ceus_figure_generation_audit.json`

## Double-Anonymous Boundary

This public repository contains only the anonymous review package. The following files are intentionally excluded:

- author-identifying title page
- cover letter
- author contribution declaration with names
- administrative checklist entries that reference author identity fields

Those files remain only in the local submission workspace and should not be made reviewer-visible during double-anonymous review.

## Full Reproducibility Boundary

This repository stores the manuscript-facing anonymous package and audit artifacts. The manuscript data-availability statement points reviewers to the anonymised review archive for the full synthetic-data pipeline, trained models, paired-inference outputs, local-sweep outputs, generated figures, and related reproduction assets.

The committed audit outputs document the latest reported checks, including:

- 21-run contiguity-aware local sweep
- 42-run no-reuse local parity audit
- 9-run two-step local lookahead audit
- 84-run local budget-sensitivity sweep
- 120-run fixed-policy DRL budget-decoding sweep
- 60-run prefix-horizon audit

## Suggested GitHub About Text

Description:

> Anonymous CEUS Paper 2 package: cadastral parcel DRL benchmark showing exact-delta local diagnostics can beat Maskable PPO in low-intervention regimes.

Suggested topics:

`deep-reinforcement-learning`, `spatial-optimization`, `land-use-planning`, `cadastral-parcels`, `synthetic-data`, `maskable-ppo`, `reproducibility`, `ceus`
