"""Two-step lookahead local-search diagnostic for the CEUS manuscript.

This experiment tests whether the exact-delta local baseline is too myopic.
At each paired exchange, it first finds the top-K immediate scalarized swaps,
then scores each candidate by applying it temporarily and adding the best next
immediate scalarized swap. The selected first swap is then committed.

The objective is the same normalized slope-contiguity scalarization used by
contiguity_aware_greedy.py. This is not a globally optimal planner; it is a
transparent two-step diagnostic for the claimed weak inter-swap coupling.
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

sys.path.insert(0, "D:/test/paper2_v2/v1_scripts")
from land_use_env_real import RealDataLandUseEnv  # noqa: E402


FEATS = Path("D:/test/paper2_v2/v1_compat/features")
ADJ = Path("D:/test/paper2_v2/v1_compat/adjacency")
OUT = Path("D:/test/paper2_v2/v4_artifacts")

REGIONS = [
    ("A", "999001"),
    ("B", "999002"),
    ("C", "999003"),
]

FARMLAND = 1
FOREST = 2


def make_env(code: str, n_pairs: int) -> RealDataLandUseEnv:
    return RealDataLandUseEnv(
        features_csv=str(FEATS / f"township_{code}_features.csv"),
        adjacency_npz=str(ADJ / f"township_{code}_adj.npz"),
        max_conversions=n_pairs * 2,
        enforce_pairs=True,
    )


def snapshot(env: RealDataLandUseEnv) -> dict:
    return {
        "land_use": env.land_use.copy(),
        "n_farmland": env.n_farmland,
        "n_forest": env.n_forest,
        "total_farmland_slope": env.total_farmland_slope,
        "total_farmland_area": env.total_farmland_area,
        "farmland_nbr_count": env.farmland_nbr_count.copy(),
        "total_farmland_adj": env.total_farmland_adj,
    }


def restore(env: RealDataLandUseEnv, snap: dict) -> None:
    env.land_use = snap["land_use"].copy()
    env.n_farmland = snap["n_farmland"]
    env.n_forest = snap["n_forest"]
    env.total_farmland_slope = snap["total_farmland_slope"]
    env.total_farmland_area = snap["total_farmland_area"]
    env.farmland_nbr_count = snap["farmland_nbr_count"].copy()
    env.total_farmland_adj = snap["total_farmland_adj"]


def apply_pair(env: RealDataLandUseEnv, farm_i: int, forest_j: int) -> None:
    env._swap_to_forest(int(farm_i))
    env._swap_to_farmland(int(forest_j))


def validate_pair_delta(env: RealDataLandUseEnv, n_checks: int = 20, seed: int = 123) -> None:
    rng = np.random.default_rng(seed)
    env.reset()
    farm_idx = np.where(env.land_use == FARMLAND)[0]
    forest_idx = np.where(env.land_use == FOREST)[0]
    for _ in range(n_checks):
        i = int(rng.choice(farm_idx))
        j = int(rng.choice(forest_idx))
        snap = snapshot(env)
        current_num = env.total_farmland_slope
        current_area = env.total_farmland_area
        expected_slope = (
            current_num - env.slopes[i] * env.areas[i] + env.slopes[j] * env.areas[j]
        ) / (current_area - env.areas[i] + env.areas[j])
        adjacent = 1 if j in env.adjacency[i] else 0
        delta_adj = -2 * env.farmland_nbr_count[i] + 2 * (env.farmland_nbr_count[j] - adjacent)
        expected_cont = (env.total_farmland_adj + delta_adj) / max(env.n_farmland, 1)
        apply_pair(env, i, j)
        if not np.isclose(expected_slope, env.avg_farmland_slope, rtol=1e-10, atol=1e-10):
            raise AssertionError((i, j, expected_slope, env.avg_farmland_slope))
        if not np.isclose(expected_cont, env.contiguity, rtol=1e-10, atol=1e-10):
            raise AssertionError((i, j, expected_cont, env.contiguity))
        restore(env, snap)


def top_pairs(env: RealDataLandUseEnv, lambda_cont: float, top_k: int) -> list[tuple[float, int, int]]:
    farm_idx = np.where(env.land_use == FARMLAND)[0]
    forest_idx = np.where(env.land_use == FOREST)[0]
    if len(farm_idx) == 0 or len(forest_idx) == 0:
        return []

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

    current_num = env.total_farmland_slope
    current_area = env.total_farmland_area
    candidates: list[tuple[float, int, int]] = []
    per_farm_k = max(1, min(top_k, len(forest_idx)))

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

        if per_farm_k == 1:
            local_ids = [int(np.argmax(score))]
        else:
            local_ids = np.argpartition(score, -per_farm_k)[-per_farm_k:]
        for j_local in local_ids:
            candidates.append((float(score[j_local]), int(i_global), int(forest_idx[j_local])))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[:top_k]


def choose_lookahead_pair(
    env: RealDataLandUseEnv,
    lambda_cont: float,
    top_k: int,
) -> tuple[int, int, float, float, int]:
    first_stage = top_pairs(env, lambda_cont, top_k)
    if not first_stage:
        raise RuntimeError("No feasible first-stage pair")

    best_total = -np.inf
    best_first = None
    best_first_score = np.nan
    best_second_score = 0.0
    evaluated = 0
    base = snapshot(env)
    for first_score, farm_i, forest_j in first_stage:
        restore(env, base)
        apply_pair(env, farm_i, forest_j)
        second_stage = top_pairs(env, lambda_cont, 1)
        second_score = second_stage[0][0] if second_stage else 0.0
        total_score = first_score + second_score
        evaluated += 1
        if total_score > best_total:
            best_total = total_score
            best_first = (farm_i, forest_j)
            best_first_score = first_score
            best_second_score = second_score
    restore(env, base)
    if best_first is None:
        raise RuntimeError("No feasible lookahead pair")
    return best_first[0], best_first[1], best_first_score, best_second_score, evaluated


def run_lookahead(env: RealDataLandUseEnv, lambda_cont: float, top_k: int, n_pairs: int) -> dict:
    env.reset()
    validate_pair_delta(env)
    init_slope = env.avg_farmland_slope
    init_cont = env.contiguity
    n_farm0 = env.n_farmland

    scores = []
    evaluated = 0
    start = time.time()
    completed = 0
    while completed < n_pairs:
        farm_i, forest_j, first_score, second_score, n_eval = choose_lookahead_pair(
            env, lambda_cont=lambda_cont, top_k=top_k
        )
        apply_pair(env, farm_i, forest_j)
        scores.append((first_score, second_score))
        evaluated += n_eval
        completed += 1

    final_slope = env.avg_farmland_slope
    final_cont = env.contiguity
    return {
        "lambda_cont": lambda_cont,
        "top_k": top_k,
        "budget_pairs": n_pairs,
        "init_slope": init_slope,
        "final_slope": final_slope,
        "slope_change_pct": 100 * (final_slope - init_slope) / init_slope if init_slope else 0.0,
        "init_cont": init_cont,
        "final_cont": final_cont,
        "cont_change": final_cont - init_cont,
        "completed_pairs": completed,
        "farmland_change": env.n_farmland - n_farm0,
        "lookahead_candidates_evaluated": evaluated,
        "mean_first_score": float(np.mean([s[0] for s in scores])) if scores else np.nan,
        "mean_second_score": float(np.mean([s[1] for s in scores])) if scores else np.nan,
        "elapsed_seconds": time.time() - start,
    }


def build_summary(full: pd.DataFrame, one_step: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in full.iterrows():
        base = one_step[
            (one_step.region == r.region)
            & np.isclose(one_step.lambda_cont.astype(float), float(r.lambda_cont))
        ].iloc[0]
        rows.append(
            {
                "region": r.region,
                "lambda_cont": float(r.lambda_cont),
                "top_k": int(r.top_k),
                "one_step_slope_pct": float(base.slope_change_pct),
                "lookahead_slope_pct": float(r.slope_change_pct),
                "lookahead_minus_one_step_slope_pp": float(r.slope_change_pct - base.slope_change_pct),
                "one_step_cont_change": float(base.cont_change),
                "lookahead_cont_change": float(r.cont_change),
                "lookahead_minus_one_step_cont": float(r.cont_change - base.cont_change),
                "completed_pairs": int(r.completed_pairs),
                "elapsed_seconds": float(r.elapsed_seconds),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lambdas", default="0,0.5,1")
    parser.add_argument("--regions", default="A,B,C")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--n-pairs", type=int, default=100)
    parser.add_argument("--output", default="two_step_lookahead_local.csv")
    args = parser.parse_args()

    lambdas = [float(x) for x in args.lambdas.split(",") if x.strip()]
    want_regions = {x.strip() for x in args.regions.split(",") if x.strip()}
    rows = []

    for region, code in REGIONS:
        if region not in want_regions:
            continue
        for lam in lambdas:
            print(f"--- Region {region} lambda={lam:g} topK={args.top_k} pairs={args.n_pairs} ---")
            env = make_env(code, args.n_pairs)
            result = run_lookahead(env, lam, args.top_k, args.n_pairs)
            result.update({"region": region, "code": code, "method": "two_step_lookahead"})
            print(
                f"  slope={result['slope_change_pct']:+.3f}% "
                f"cont={result['cont_change']:+.4f} "
                f"elapsed={result['elapsed_seconds']:.1f}s"
            )
            rows.append(result)

    OUT.mkdir(parents=True, exist_ok=True)
    full = pd.DataFrame(rows)
    out_path = OUT / args.output
    full.to_csv(out_path, index=False)

    one_step = pd.read_csv(OUT / "contiguity_aware_greedy.csv")
    summary = build_summary(full, one_step)
    summary_path = OUT / "two_step_lookahead_summary.csv"
    summary.to_csv(summary_path, index=False)

    audit = {
        "experiment": "two-step lookahead local search",
        "lambdas": lambdas,
        "regions": sorted(want_regions),
        "top_k": args.top_k,
        "n_pairs": args.n_pairs,
        "full_output": str(out_path),
        "summary_output": str(summary_path),
    }
    audit_path = OUT / "two_step_lookahead_audit.json"
    with audit_path.open("w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)
    print(f"\n[ok] wrote {out_path}")
    print(f"[ok] wrote {summary_path}")
    print(f"[ok] wrote {audit_path}")


if __name__ == "__main__":
    main()
