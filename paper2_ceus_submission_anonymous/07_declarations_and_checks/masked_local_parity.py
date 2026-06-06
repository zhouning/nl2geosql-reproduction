"""No-reuse parity audit for contiguity-aware exact-delta local ranking.

The DRL environment marks selected swappable parcels as converted, so a parcel
cannot be selected again within one episode. The original exact-delta local
diagnostic ranks over the current farmland and forest sets and does not keep an
explicit converted-parcel mask. This script measures whether that implementation
detail materially affects the local frontier.

Default outputs under D:/test/paper2_v2/v4_artifacts:
  - masked_local_parity.csv
  - masked_local_parity_summary.csv
  - masked_local_parity_audit.json
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
V1 = ROOT / "v1_scripts"
sys.path.insert(0, str(V1))

from land_use_env_real import RealDataLandUseEnv  # noqa: E402


FEATS = ROOT / "v1_compat" / "features"
ADJ = ROOT / "v1_compat" / "adjacency"
OUT = ROOT / "v4_artifacts"

REGIONS = [
    ("A", "999001"),
    ("B", "999002"),
    ("C", "999003"),
]

FARMLAND = 1
FOREST = 2


def parse_csv_arg(text: str, cast=str):
    return [cast(x.strip()) for x in text.split(",") if x.strip()]


def make_env(code: str, n_pairs: int, quiet: bool = False) -> RealDataLandUseEnv:
    kwargs = dict(
        features_csv=str(FEATS / f"township_{code}_features.csv"),
        adjacency_npz=str(ADJ / f"township_{code}_adj.npz"),
        max_conversions=n_pairs * 2,
        enforce_pairs=True,
    )
    if not quiet:
        return RealDataLandUseEnv(**kwargs)

    import contextlib
    import io

    with contextlib.redirect_stdout(io.StringIO()):
        return RealDataLandUseEnv(**kwargs)


def metric_after_pair(env: RealDataLandUseEnv, farm_i: int, forest_j: int) -> tuple[float, float]:
    """Return exact area-weighted slope and contiguity after swapping one pair."""
    new_num = (
        env.total_farmland_slope
        - env.slopes[farm_i] * env.areas[farm_i]
        + env.slopes[forest_j] * env.areas[forest_j]
    )
    new_area = env.total_farmland_area - env.areas[farm_i] + env.areas[forest_j]
    new_slope = new_num / new_area if new_area > 0 else np.inf

    adjacent = 1 if forest_j in env.adjacency[farm_i] else 0
    delta_adj = -2 * env.farmland_nbr_count[farm_i] + 2 * (
        env.farmland_nbr_count[forest_j] - adjacent
    )
    new_cont = (env.total_farmland_adj + delta_adj) / max(env.n_farmland, 1)
    return float(new_slope), float(new_cont)


def validate_pair_delta(env: RealDataLandUseEnv, n_checks: int = 20, seed: int = 123) -> None:
    """Check analytic pair deltas against actual swaps on copied environments."""
    rng = np.random.default_rng(seed)
    env.reset()
    farm_idx = np.where(env.land_use == FARMLAND)[0]
    forest_idx = np.where(env.land_use == FOREST)[0]
    for _ in range(n_checks):
        i = int(rng.choice(farm_idx))
        j = int(rng.choice(forest_idx))
        expected_slope, expected_cont = metric_after_pair(env, i, j)
        trial = copy.deepcopy(env)
        trial._swap_to_forest(i)
        trial._swap_to_farmland(j)
        if not np.isclose(expected_slope, trial.avg_farmland_slope, rtol=1e-10, atol=1e-10):
            raise AssertionError((i, j, expected_slope, trial.avg_farmland_slope))
        if not np.isclose(expected_cont, trial.contiguity, rtol=1e-10, atol=1e-10):
            raise AssertionError((i, j, expected_cont, trial.contiguity))


def choose_pair(
    env: RealDataLandUseEnv,
    lambda_cont: float,
    unavailable: np.ndarray | None = None,
) -> tuple[int, int] | None:
    """Choose the best exact-delta pair under a normalized scalar objective."""
    farm_idx = np.where(env.land_use == FARMLAND)[0]
    forest_idx = np.where(env.land_use == FOREST)[0]
    if unavailable is not None:
        farm_idx = farm_idx[~unavailable[farm_idx]]
        forest_idx = forest_idx[~unavailable[forest_idx]]
    if len(farm_idx) == 0 or len(forest_idx) == 0:
        return None

    current_slope = env.avg_farmland_slope
    current_cont = env.contiguity
    init_slope_scale = abs(env.initial_avg_slope) + 1e-12
    init_cont_scale = abs(env.initial_contiguity) + 1e-12

    slopes_f = env.slopes[farm_idx]
    areas_f = env.areas[farm_idx]
    slopes_o = env.slopes[forest_idx]
    areas_o = env.areas[forest_idx]
    farm_contrib = slopes_f * areas_f
    forest_contrib = slopes_o * areas_o

    forest_pos = np.full(env.n_parcels, -1, dtype=np.int32)
    forest_pos[forest_idx] = np.arange(len(forest_idx), dtype=np.int32)
    base_cont_delta = 2 * env.farmland_nbr_count[forest_idx]

    best_score = -np.inf
    best_pair = None
    current_num = env.total_farmland_slope
    current_area = env.total_farmland_area

    for i_local, i_global in enumerate(farm_idx):
        new_num = current_num - farm_contrib[i_local] + forest_contrib
        new_area = current_area - areas_f[i_local] + areas_o
        new_slope = np.where(new_area > 0, new_num / new_area, np.inf)
        slope_improve = (current_slope - new_slope) / init_slope_scale

        cont_delta = base_cont_delta.astype(np.float64, copy=True)
        cont_delta -= 2 * env.farmland_nbr_count[i_global]
        nbr_pos = forest_pos[np.asarray(env.adjacency[i_global], dtype=np.int64)]
        nbr_pos = nbr_pos[nbr_pos >= 0]
        if len(nbr_pos):
            cont_delta[nbr_pos] -= 2
        new_cont = (env.total_farmland_adj + cont_delta) / max(env.n_farmland, 1)
        cont_improve = (new_cont - current_cont) / init_cont_scale

        score = slope_improve + lambda_cont * cont_improve
        local_best = int(np.argmax(score))
        if score[local_best] > best_score:
            best_score = float(score[local_best])
            best_pair = (int(i_global), int(forest_idx[local_best]))

    return best_pair


def run_local(
    env: RealDataLandUseEnv,
    lambda_cont: float,
    n_pairs: int,
    no_reuse: bool,
) -> dict:
    """Run scalarized exact-delta local ranking with or without a no-reuse mask."""
    env.reset()
    validate_pair_delta(env)
    init_slope = env.avg_farmland_slope
    init_cont = env.contiguity
    n_farm0 = env.n_farmland
    unavailable = np.zeros(env.n_parcels, dtype=bool) if no_reuse else None

    completed = 0
    t0 = time.time()
    while completed < n_pairs:
        pair = choose_pair(env, lambda_cont, unavailable=unavailable)
        if pair is None:
            break
        i, j = pair
        env._swap_to_forest(i)
        env._swap_to_farmland(j)
        if unavailable is not None:
            unavailable[i] = True
            unavailable[j] = True
        completed += 1

    elapsed = time.time() - t0
    final_slope = env.avg_farmland_slope
    final_cont = env.contiguity
    return {
        "mode": "no_reuse" if no_reuse else "unrestricted",
        "lambda_cont": lambda_cont,
        "init_slope": init_slope,
        "final_slope": final_slope,
        "slope_change_pct": 100.0 * (final_slope - init_slope) / init_slope if init_slope else 0.0,
        "init_cont": init_cont,
        "final_cont": final_cont,
        "cont_change": final_cont - init_cont,
        "completed_pairs": completed,
        "farmland_change": env.n_farmland - n_farm0,
        "elapsed_seconds": elapsed,
    }


def dominates(local_row: pd.Series, slope: float, cont: float) -> bool:
    """Return True if a local point Pareto-dominates a DRL outcome."""
    return (
        float(local_row["slope_change_pct"]) <= float(slope)
        and float(local_row["cont_change"]) >= float(cont)
        and (
            float(local_row["slope_change_pct"]) < float(slope)
            or float(local_row["cont_change"]) > float(cont)
        )
    )


def build_summary(rows: pd.DataFrame, artifacts_dir: Path) -> tuple[pd.DataFrame, dict]:
    """Summarize parity differences and no-reuse dominance against DRL outputs."""
    summaries = []
    audit: dict[str, object] = {}
    per_seed_path = artifacts_dir / "per_seed_results.csv"
    agg_path = artifacts_dir / "aggregate_table.csv"
    per_seed = pd.read_csv(per_seed_path) if per_seed_path.exists() else pd.DataFrame()
    agg = pd.read_csv(agg_path) if agg_path.exists() else pd.DataFrame()

    total_drl_runs = 0
    total_dominated_runs = 0
    total_mean_outcomes = 0
    total_dominated_means = 0

    for region in sorted(rows["region"].unique()):
        sub = rows[rows["region"] == region].copy()
        wide = sub.pivot(index="lambda_cont", columns="mode", values=["slope_change_pct", "cont_change"])
        slope_diff = wide["slope_change_pct"]["no_reuse"] - wide["slope_change_pct"]["unrestricted"]
        cont_diff = wide["cont_change"]["no_reuse"] - wide["cont_change"]["unrestricted"]

        no_reuse = sub[sub["mode"] == "no_reuse"].copy()
        slope_exact = no_reuse.loc[no_reuse["lambda_cont"].eq(0)].iloc[0]
        nonneg = no_reuse[no_reuse["cont_change"] >= -1e-12].sort_values("slope_change_pct")
        if len(nonneg) > 0:
            nonneg_best = nonneg.iloc[0]
        else:
            nonneg_best = no_reuse.loc[no_reuse["cont_change"].idxmax()]

        reg_seed = per_seed[(per_seed["region"] == region) & (per_seed.get("status", "ok") == "ok")]
        reg_agg = agg[agg["region"] == region]

        dominated_runs = 0
        for _, r in reg_seed.iterrows():
            if any(dominates(lr, r["slope_change_pct"], r["cont_change"]) for _, lr in no_reuse.iterrows()):
                dominated_runs += 1
        dominated_means = 0
        for _, r in reg_agg.iterrows():
            if any(dominates(lr, r["slope_pct_mean"], r["cont_change_mean"]) for _, lr in no_reuse.iterrows()):
                dominated_means += 1

        total_drl_runs += int(len(reg_seed))
        total_dominated_runs += int(dominated_runs)
        total_mean_outcomes += int(len(reg_agg))
        total_dominated_means += int(dominated_means)

        summaries.append(
            {
                "region": region,
                "n_lambdas": int(len(no_reuse)),
                "slope_exact_slope_pct": float(slope_exact["slope_change_pct"]),
                "slope_exact_cont_change": float(slope_exact["cont_change"]),
                "nonneg_lambda": float(nonneg_best["lambda_cont"]),
                "nonneg_slope_pct": float(nonneg_best["slope_change_pct"]),
                "nonneg_cont_change": float(nonneg_best["cont_change"]),
                "max_abs_slope_diff_pp": float(np.max(np.abs(slope_diff))),
                "max_abs_cont_diff": float(np.max(np.abs(cont_diff))),
                "drl_mean_outcomes": int(len(reg_agg)),
                "drl_mean_outcomes_dominated": int(dominated_means),
                "individual_drl_runs": int(len(reg_seed)),
                "individual_drl_runs_dominated": int(dominated_runs),
            }
        )

    audit["total_drl_mean_outcomes"] = total_mean_outcomes
    audit["total_drl_mean_outcomes_dominated"] = total_dominated_means
    audit["total_individual_drl_runs"] = total_drl_runs
    audit["total_individual_drl_runs_dominated"] = total_dominated_runs
    return pd.DataFrame(summaries), audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regions", default="A,B,C")
    parser.add_argument("--lambdas", default="0,0.25,0.5,1,2,4,8")
    parser.add_argument("--n-pairs", type=int, default=100)
    parser.add_argument("--out-dir", type=Path, default=OUT)
    parser.add_argument("--quiet-env", action="store_true")
    args = parser.parse_args()

    selected = set(parse_csv_arg(args.regions, str))
    lambdas = parse_csv_arg(args.lambdas, float)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    t_batch = time.time()
    for region, code in REGIONS:
        if region not in selected:
            continue
        for lam in lambdas:
            for no_reuse in (False, True):
                print(
                    f"[run] region={region} lambda={lam:g} "
                    f"mode={'no_reuse' if no_reuse else 'unrestricted'}"
                )
                env = make_env(code, args.n_pairs, quiet=args.quiet_env)
                result = run_local(env, lam, args.n_pairs, no_reuse=no_reuse)
                result.update(
                    {
                        "region": region,
                        "code": code,
                        "budget_pairs": args.n_pairs,
                        "method": f"local_{result['mode']}_lambda_{lam:g}",
                    }
                )
                print(
                    f"  slope={result['slope_change_pct']:+.3f}% "
                    f"cont={result['cont_change']:+.4f} pairs={result['completed_pairs']}"
                )
                rows.append(result)

    df = pd.DataFrame(rows)
    summary, dominance_audit = build_summary(df, args.out_dir)

    full_path = args.out_dir / "masked_local_parity.csv"
    summary_path = args.out_dir / "masked_local_parity_summary.csv"
    audit_path = args.out_dir / "masked_local_parity_audit.json"
    df.to_csv(full_path, index=False)
    summary.to_csv(summary_path, index=False)

    audit = {
        "regions": sorted(selected),
        "lambdas": lambdas,
        "budget_pairs": args.n_pairs,
        "n_rows": int(len(df)),
        "elapsed_seconds": time.time() - t_batch,
        "outputs": {
            "full": str(full_path),
            "summary": str(summary_path),
        },
        "dominance": dominance_audit,
        "boundary": (
            "No-reuse local ranking matches the DRL episode-level converted-parcel "
            "constraint but remains a deterministic exact-delta diagnostic, not a "
            "globally optimized planner."
        ),
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    print(f"[ok] wrote {full_path}")
    print(f"[ok] wrote {summary_path}")
    print(f"[ok] wrote {audit_path}")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
