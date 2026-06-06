"""Alternative-budget deterministic paired inference for trained DRL policies.

This script evaluates the already-trained MaskablePPO policies at paired
exchange budgets B = 25, 50, 100, and 200 by changing the inference episode
length to 2B raw actions. It does not retrain policies.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch


ROOT = Path(__file__).resolve().parent
V1 = ROOT / "v1_scripts"
sys.path.insert(0, str(V1))

torch.distributions.Distribution.set_default_validate_args(False)

from land_use_env_real import RealDataLandUseEnv  # noqa: E402
from sb3_contrib import MaskablePPO  # noqa: E402


REGIONS = [
    ("A", "999001", "main_sweep_AW_eval"),
    ("B", "999002", "main_sweep_AW_retrained"),
    ("C", "999003", "main_sweep_AW_eval"),
]
METHODS = ["lagrangian", "entonly"]
SEEDS = list(range(5))


def parse_csv_arg(text: str, cast=str):
    return [cast(x.strip()) for x in text.split(",") if x.strip()]


def model_path(results_root: Path, region: str, code: str, method: str, seed: int) -> Path:
    if region == "B":
        return results_root / "main_sweep_AW" / f"township_{code}" / method / f"model_seed{seed}.zip"
    return results_root / "main_sweep" / f"township_{code}" / method / f"model_seed{seed}.zip"


def make_env(features_dir: Path, adjacency_dir: Path, code: str, horizon_pairs: int, quiet: bool):
    kwargs = dict(
        features_csv=str(features_dir / f"township_{code}_features.csv"),
        adjacency_npz=str(adjacency_dir / f"township_{code}_adj.npz"),
        max_conversions=horizon_pairs * 2,
        enforce_pairs=True,
    )
    if not quiet:
        return RealDataLandUseEnv(**kwargs)
    with contextlib.redirect_stdout(io.StringIO()):
        return RealDataLandUseEnv(**kwargs)


def run_episode(env: RealDataLandUseEnv, model: MaskablePPO, budget_pairs: int) -> dict:
    obs, info = env.reset()
    initial_slope = float(info["avg_slope"])
    initial_cont = float(info["contiguity"])
    step = 0
    done = False
    t0 = time.time()

    while not done and step < budget_pairs * 2:
        masks = env.action_masks()
        if not masks.any():
            break
        action, _ = model.predict(obs, deterministic=True, action_masks=masks)
        obs, _reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        step += 1

    dt = time.time() - t0
    final_slope = float(info["avg_slope"])
    final_cont = float(info["contiguity"])
    slope_change = final_slope - initial_slope
    slope_change_pct = 100.0 * slope_change / initial_slope if initial_slope else 0.0

    return {
        "budget_pairs": budget_pairs,
        "horizon_pairs": env.max_steps // 2,
        "requested_steps": budget_pairs * 2,
        "total_steps": step,
        "completed_pairs": int(info["completed_pairs"]),
        "init_slope": initial_slope,
        "final_slope": final_slope,
        "slope_change": slope_change,
        "slope_change_pct": slope_change_pct,
        "init_cont": initial_cont,
        "final_cont": final_cont,
        "cont_change": final_cont - initial_cont,
        "farmland_change": int(info["farmland_change"]),
        "inference_time_s": dt,
    }


def build_summaries(rows: list[dict], local_summary_path: Path | None):
    df = pd.DataFrame(rows)
    ok = df[df["status"] == "ok"].copy()

    method_summary = (
        ok.groupby(["region", "code", "budget_pairs", "method"], as_index=False)
        .agg(
            n=("seed", "count"),
            slope_pct_mean=("slope_change_pct", "mean"),
            slope_pct_std=("slope_change_pct", lambda x: float(np.std(x, ddof=1)) if len(x) > 1 else 0.0),
            slope_pct_min=("slope_change_pct", "min"),
            slope_pct_max=("slope_change_pct", "max"),
            cont_change_mean=("cont_change", "mean"),
            cont_change_std=("cont_change", lambda x: float(np.std(x, ddof=1)) if len(x) > 1 else 0.0),
            completed_pairs_min=("completed_pairs", "min"),
            completed_pairs_max=("completed_pairs", "max"),
            farmland_change_max_abs=("farmland_change", lambda x: int(np.max(np.abs(x)))),
        )
    )

    all_summary = (
        ok.groupby(["region", "code", "budget_pairs"], as_index=False)
        .agg(
            n=("seed", "count"),
            drl_mean_slope_pct=("slope_change_pct", "mean"),
            drl_std_slope_pct=("slope_change_pct", lambda x: float(np.std(x, ddof=1)) if len(x) > 1 else 0.0),
            drl_best_slope_pct=("slope_change_pct", "min"),
            drl_worst_slope_pct=("slope_change_pct", "max"),
            drl_mean_cont_change=("cont_change", "mean"),
            drl_best_cont_at_best_slope=("cont_change", lambda x: float(ok.loc[x.index[np.argmin(ok.loc[x.index, "slope_change_pct"].to_numpy())], "cont_change"])),
            completed_pairs_min=("completed_pairs", "min"),
            completed_pairs_max=("completed_pairs", "max"),
            farmland_change_max_abs=("farmland_change", lambda x: int(np.max(np.abs(x)))),
        )
    )

    comparison = all_summary.copy()
    if local_summary_path and local_summary_path.exists():
        local = pd.read_csv(local_summary_path)
        comparison = comparison.merge(
            local[
                [
                    "region",
                    "budget_pairs",
                    "slope_opt_slope_pct",
                    "slope_opt_cont_change",
                    "nonneg_lambda",
                    "nonneg_slope_pct",
                    "nonneg_cont_change",
                ]
            ],
            on=["region", "budget_pairs"],
            how="left",
        )
        comparison["drl_best_minus_slope_exact"] = (
            comparison["drl_best_slope_pct"] - comparison["slope_opt_slope_pct"]
        )
        comparison["drl_best_minus_nonneg_local"] = (
            comparison["drl_best_slope_pct"] - comparison["nonneg_slope_pct"]
        )
        comparison["local_slope_exact_beats_best_drl"] = (
            comparison["slope_opt_slope_pct"] < comparison["drl_best_slope_pct"]
        )
        comparison["local_nonneg_beats_best_drl"] = (
            comparison["nonneg_slope_pct"] < comparison["drl_best_slope_pct"]
        )

    return df, method_summary, comparison


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", required=True, type=Path)
    parser.add_argument("--features-dir", type=Path, default=ROOT / "v1_compat" / "features")
    parser.add_argument("--adjacency-dir", type=Path, default=ROOT / "v1_compat" / "adjacency")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "v4_artifacts")
    parser.add_argument("--budgets", default="25,50,100,200")
    parser.add_argument("--regions", default="A,B,C")
    parser.add_argument("--methods", default="lagrangian,entonly")
    parser.add_argument("--seeds", default="0,1,2,3,4")
    parser.add_argument("--local-summary", type=Path, default=ROOT / "v4_artifacts" / "contiguity_aware_budget_summary.csv")
    parser.add_argument("--horizon-pairs", type=int, default=None,
                        help="Keep the environment horizon fixed at this paired budget while stopping after --budgets.")
    parser.add_argument("--output-tag", default="drl_budget",
                        help="Prefix for output file names under --out-dir.")
    parser.add_argument("--quiet-env", action="store_true")
    args = parser.parse_args()

    budgets = parse_csv_arg(args.budgets, int)
    if args.horizon_pairs is not None:
        too_large = [b for b in budgets if b > args.horizon_pairs]
        if too_large:
            raise ValueError(f"--horizon-pairs={args.horizon_pairs} cannot be smaller than requested budgets {too_large}")
    regions_requested = set(parse_csv_arg(args.regions, str))
    methods = parse_csv_arg(args.methods, str)
    seeds = parse_csv_arg(args.seeds, int)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    selected_regions = [r for r in REGIONS if r[0] in regions_requested]

    envs = {}
    for region, code, _source in selected_regions:
        for budget in budgets:
            horizon = args.horizon_pairs if args.horizon_pairs is not None else budget
            envs[(region, budget)] = make_env(args.features_dir, args.adjacency_dir, code, horizon, args.quiet_env)

    rows = []
    for region, code, source in selected_regions:
        for method in methods:
            for seed in seeds:
                mp = model_path(args.results_root, region, code, method, seed)
                base = {
                    "region": region,
                    "code": code,
                    "method": method,
                    "seed": seed,
                    "source": source,
                    "model_path": str(mp),
                }
                if not mp.exists():
                    for budget in budgets:
                        rows.append({**base, "budget_pairs": budget, "status": "missing_model"})
                    print(f"[missing] {region}/{method}/seed{seed}: {mp}")
                    continue

                t_load = time.time()
                model = MaskablePPO.load(str(mp))
                load_time = time.time() - t_load
                print(f"[model] {region}/{method}/seed{seed} loaded in {load_time:.2f}s")

                for budget in budgets:
                    env = envs[(region, budget)]
                    try:
                        res = run_episode(env, model, budget)
                        rows.append({**base, **res, "status": "ok", "model_load_time_s": load_time})
                        print(
                            f"  [ok] B={budget:3d} slope={res['slope_change_pct']:+.3f}% "
                            f"cont={res['cont_change']:+.3f} pairs={res['completed_pairs']}"
                        )
                    except Exception as exc:  # keep batch auditable if one policy fails
                        rows.append({**base, "budget_pairs": budget, "status": "error", "error": repr(exc)})
                        print(f"  [error] B={budget}: {exc!r}")

    full, method_summary, comparison = build_summaries(rows, args.local_summary)

    full_path = args.out_dir / f"{args.output_tag}_sensitivity.csv"
    method_path = args.out_dir / f"{args.output_tag}_summary.csv"
    comparison_path = args.out_dir / f"{args.output_tag}_vs_local.csv"
    full.to_csv(full_path, index=False)
    method_summary.to_csv(method_path, index=False)
    comparison.to_csv(comparison_path, index=False)

    audit = {
        "budgets": budgets,
        "regions": [r[0] for r in selected_regions],
        "methods": methods,
        "seeds": seeds,
        "n_rows": int(len(full)),
        "n_ok": int((full["status"] == "ok").sum()),
        "horizon_pairs": args.horizon_pairs,
        "output_tag": args.output_tag,
        "outputs": {
            "full": str(full_path),
            "method_summary": str(method_path),
            "comparison": str(comparison_path),
        },
        "boundary": "Already-trained policies decoded at alternative budgets; no DRL retraining.",
    }
    audit_path = args.out_dir / f"{args.output_tag}_sensitivity_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    print(f"[ok] wrote {full_path}")
    print(f"[ok] wrote {method_path}")
    print(f"[ok] wrote {comparison_path}")
    print(f"[ok] wrote {audit_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
