"""Generate CEUS manuscript figures from the current v4 area-weighted results.

Legacy figure scripts may read pre-v4 outputs and silently mix unweighted and
area-weighted runs. This script is deliberately tied to the current CEUS tables
in v4_artifacts and validates the DRL JSON trajectories against the per-seed
CSV before drawing.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
ART = ROOT / "v4_artifacts"
OUT = ROOT / "figures"
CEUS_DIRS = [
    Path("D:/test/CEUS_submission_paper2/05_figures"),
    Path("D:/test/CEUS_submission_paper2/06_latex_source_editable/figures"),
]

MAIN_SWEEP = Path("G:/我的云端硬盘/paper2_v2_results/main_sweep")
MAIN_SWEEP_AW = Path("G:/我的云端硬盘/paper2_v2_results/main_sweep_AW")

REGIONS = [
    {"region": "A", "code": "999001", "n": 3607},
    {"region": "B", "code": "999002", "n": 5500},
    {"region": "C", "code": "999003", "n": 11786},
]

METHOD_COLORS = {
    "Random": "#9a9a9a",
    "GA": "#c77c02",
    "Slope-only": "#2ca02c",
    "Exact-delta": "#d62728",
    "DRL-Lagr": "#1f77b4",
    "DRL-Ent": "#9467bd",
    "Local sweep": "#222222",
}

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 9,
        "legend.fontsize": 7,
        "figure.dpi": 120,
        "savefig.dpi": 450,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
    }
)


def read_tables() -> dict[str, pd.DataFrame]:
    tables = {
        "agg": pd.read_csv(ART / "aggregate_table.csv"),
        "baselines": pd.read_csv(ART / "baselines.csv"),
        "exact": pd.read_csv(ART / "exact_delta_greedy.csv"),
        "per_seed": pd.read_csv(ART / "per_seed_results.csv"),
        "local": pd.read_csv(ART / "contiguity_aware_greedy.csv"),
    }
    # Older CSVs do not include a region column for exact/local outputs.
    if "region" not in tables["exact"].columns:
        tables["exact"]["region"] = [r["region"] for r in REGIONS]
    if "region" not in tables["local"].columns:
        local = tables["local"].copy()
        local["region"] = np.repeat([r["region"] for r in REGIONS], 7)
        tables["local"] = local
    return tables


def drl_eval_path(region: str, code: str, method: str, seed: int) -> Path:
    if region == "B":
        return MAIN_SWEEP_AW / f"township_{code}" / method / f"eval_paired_seed{seed}.json"
    return MAIN_SWEEP / f"township_{code}" / method / f"eval_paired_AW_seed{seed}.json"


def load_drl_json(region: str, code: str, method: str, seed: int) -> dict:
    path = drl_eval_path(region, code, method, seed)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_trajectories(per_seed: pd.DataFrame) -> None:
    mismatches: list[str] = []
    for reg in REGIONS:
        region, code = reg["region"], reg["code"]
        for method in ["lagrangian", "entonly"]:
            for seed in range(5):
                js = load_drl_json(region, code, method, seed)
                row = per_seed[
                    (per_seed.region == region)
                    & (per_seed.method == method)
                    & (per_seed.seed == seed)
                ].iloc[0]
                for col, key in [
                    ("init_slope", "initial_avg_slope"),
                    ("final_slope", "final_avg_slope"),
                    ("slope_change_pct", "slope_change_pct"),
                    ("init_cont", "initial_contiguity"),
                    ("final_cont", "final_contiguity"),
                    ("cont_change", "cont_change"),
                ]:
                    if abs(float(row[col]) - float(js[key])) > 1e-8:
                        mismatches.append(f"{region} {method} seed{seed}: {col} != {key}")
    if mismatches:
        raise RuntimeError("Trajectory JSONs do not match per_seed_results.csv:\n" + "\n".join(mismatches))


def baseline_value(baselines: pd.DataFrame, region: str, method: str, col: str) -> float:
    return float(baselines[(baselines.region == region) & (baselines.method == method)][col].iloc[0])


def exact_value(exact: pd.DataFrame, region: str, col: str) -> float:
    return float(exact[exact.region == region][col].iloc[0])


def save_figure(fig: plt.Figure, filename: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / filename
    fig.savefig(path)
    plt.close(fig)
    for target_dir in CEUS_DIRS:
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target_dir / filename)


def fig1_cross_region(t: dict[str, pd.DataFrame]) -> None:
    """Primary cross-region slope comparison."""
    methods = ["Random", "GA", "Slope-only", "Exact-delta", "DRL-Lagr", "DRL-Ent"]
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    x = np.arange(len(REGIONS))
    width = 0.13

    for i, method in enumerate(methods):
        values, errors = [], []
        for reg in REGIONS:
            region = reg["region"]
            if method == "Random":
                values.append(baseline_value(t["baselines"], region, "random", "slope_pct"))
                errors.append(0.0)
            elif method == "GA":
                values.append(baseline_value(t["baselines"], region, "ga", "slope_pct"))
                errors.append(0.0)
            elif method == "Slope-only":
                values.append(baseline_value(t["baselines"], region, "greedy", "slope_pct"))
                errors.append(0.0)
            elif method == "Exact-delta":
                values.append(exact_value(t["exact"], region, "slope_change_pct"))
                errors.append(0.0)
            elif method == "DRL-Lagr":
                row = t["agg"][(t["agg"].region == region) & (t["agg"].method == "lagrangian")].iloc[0]
                values.append(float(row.slope_pct_mean))
                errors.append(float(row.slope_pct_std))
            elif method == "DRL-Ent":
                row = t["agg"][(t["agg"].region == region) & (t["agg"].method == "entonly")].iloc[0]
                values.append(float(row.slope_pct_mean))
                errors.append(float(row.slope_pct_std))

        ax.bar(
            x + (i - 2.5) * width,
            values,
            width,
            yerr=errors,
            capsize=2,
            color=METHOD_COLORS[method],
            edgecolor="black",
            linewidth=0.45,
            label=method,
        )

    ax.axhline(0, color="black", linestyle="--", linewidth=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r['region']}\n({r['n']:,} parcels)" for r in REGIONS])
    ax.set_ylabel("Area-weighted farmland slope change (%)")
    ax.set_title("Exact-delta local ranking is the strongest slope reducer")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(ncol=3, frameon=False, loc="upper right")
    save_figure(fig, "fig1_cross_region.png")


def fig2_per_seed(t: dict[str, pd.DataFrame]) -> None:
    """Per-seed DRL distribution with current local references."""
    fig, axes = plt.subplots(1, 3, figsize=(8.4, 3.1), sharey=True)
    for ax, reg in zip(axes, REGIONS):
        region = reg["region"]
        subset = t["per_seed"][t["per_seed"].region == region]
        for method, label, marker, color, offset in [
            ("lagrangian", "DRL-Lagr", "o", METHOD_COLORS["DRL-Lagr"], -0.06),
            ("entonly", "DRL-Ent", "s", METHOD_COLORS["DRL-Ent"], 0.06),
        ]:
            rows = subset[subset.method == method].sort_values("seed")
            ax.scatter(
                rows.seed.astype(float) + offset,
                rows.slope_change_pct.astype(float),
                s=44,
                marker=marker,
                c=color,
                edgecolors="black",
                linewidths=0.5,
                alpha=0.88,
                label=label,
            )
        slope_only = baseline_value(t["baselines"], region, "greedy", "slope_pct")
        exact = exact_value(t["exact"], region, "slope_change_pct")
        ax.axhline(slope_only, color=METHOD_COLORS["Slope-only"], linestyle=":", linewidth=1.2,
                   label=f"Slope-only ({slope_only:+.2f}%)")
        ax.axhline(exact, color=METHOD_COLORS["Exact-delta"], linestyle="--", linewidth=1.2,
                   label=f"Exact-delta ({exact:+.2f}%)")
        ax.axhline(0, color="black", linewidth=0.65)
        ax.set_title(f"Region {region} ({reg['n']:,} parcels)")
        ax.set_xlabel("Seed")
        ax.set_xticks(range(5))
        ax.grid(True, alpha=0.22)
        ax.legend(loc="best", frameon=False)
    axes[0].set_ylabel("Slope change (%, paired inference)")
    fig.suptitle("Per-seed outcomes expose Region A bimodality and Region B uniform failure", y=1.03)
    save_figure(fig, "fig2_per_seed_bimodal.png")


def fig3_trajectories(t: dict[str, pd.DataFrame]) -> None:
    """Area-weighted paired-inference trajectories from validated JSON logs."""
    fig, axes = plt.subplots(1, 3, figsize=(8.4, 3.0), sharey=False)
    for panel_idx, (ax, reg) in enumerate(zip(axes, REGIONS)):
        region, code = reg["region"], reg["code"]
        for method, label, color in [
            ("lagrangian", "DRL-Lagr", METHOD_COLORS["DRL-Lagr"]),
            ("entonly", "DRL-Ent", METHOD_COLORS["DRL-Ent"]),
        ]:
            for seed in range(5):
                js = load_drl_json(region, code, method, seed)
                steps = [0] + [int(s["step"]) for s in js["step_log"]]
                slopes = [float(js["initial_avg_slope"])] + [float(s["avg_slope"]) for s in js["step_log"]]
                alpha = 0.88 if seed == 0 else 0.28
                lw = 1.4 if seed == 0 else 0.8
                ax.plot(steps, slopes, color=color, alpha=alpha, linewidth=lw,
                        label=label if seed == 0 else None)
        init = float(t["per_seed"][t["per_seed"].region == region].init_slope.iloc[0])
        ax.axhline(init, color="black", linestyle=":", linewidth=0.8, label=f"Initial ({init:.2f} deg)")
        ax.set_title(f"Region {region} ({reg['n']:,} parcels)")
        ax.set_xlabel("Inference step")
        if panel_idx == 0:
            ax.set_ylabel("Area-weighted farmland slope (deg)")
        ax.grid(True, alpha=0.22)
        ax.legend(loc="best", frameon=False)
    fig.suptitle("Deterministic paired-inference trajectories under the area-weighted objective", y=1.03)
    save_figure(fig, "fig3_trajectories.png")


def fig4_tradeoff(t: dict[str, pd.DataFrame]) -> None:
    """Slope-contiguity plane including the scalarised local sweep."""
    fig, axes = plt.subplots(1, 3, figsize=(8.8, 3.25), sharey=False)
    legend_handles = None
    legend_labels = None
    for panel_idx, (ax, reg) in enumerate(zip(axes, REGIONS)):
        region = reg["region"]
        # Stochastic baselines and slope-only/exact local references.
        ax.scatter(
            baseline_value(t["baselines"], region, "random", "slope_pct"),
            baseline_value(t["baselines"], region, "random", "cont_change"),
            marker="s",
            s=55,
            c=METHOD_COLORS["Random"],
            edgecolors="black",
            linewidths=0.5,
            label="Random",
            zorder=2,
        )
        ax.scatter(
            baseline_value(t["baselines"], region, "ga", "slope_pct"),
            baseline_value(t["baselines"], region, "ga", "cont_change"),
            marker="^",
            s=62,
            c=METHOD_COLORS["GA"],
            edgecolors="black",
            linewidths=0.5,
            label="GA",
            zorder=3,
        )
        ax.scatter(
            baseline_value(t["baselines"], region, "greedy", "slope_pct"),
            baseline_value(t["baselines"], region, "greedy", "cont_change"),
            marker="*",
            s=130,
            c=METHOD_COLORS["Slope-only"],
            edgecolors="black",
            linewidths=0.65,
            label="Slope-only",
            zorder=5,
        )
        ax.scatter(
            exact_value(t["exact"], region, "slope_change_pct"),
            exact_value(t["exact"], region, "cont_change"),
            marker="D",
            s=70,
            c=METHOD_COLORS["Exact-delta"],
            edgecolors="black",
            linewidths=0.6,
            label="Exact-delta",
            zorder=5,
        )

        local = t["local"][t["local"].region == region].sort_values("lambda_cont")
        ax.plot(
            local.slope_change_pct.astype(float),
            local.cont_change.astype(float),
            color=METHOD_COLORS["Local sweep"],
            linewidth=1.1,
            marker="x",
            markersize=4,
            label="Local sweep",
            zorder=4,
        )

        subset = t["per_seed"][t["per_seed"].region == region]
        for method, label, marker, color in [
            ("lagrangian", "DRL-Lagr", "o", METHOD_COLORS["DRL-Lagr"]),
            ("entonly", "DRL-Ent", "P", METHOD_COLORS["DRL-Ent"]),
        ]:
            rows = subset[subset.method == method]
            ax.scatter(
                rows.slope_change_pct.astype(float),
                rows.cont_change.astype(float),
                marker=marker,
                s=38,
                c=color,
                edgecolors="black",
                linewidths=0.45,
                alpha=0.76,
                label=label,
                zorder=3,
            )

        ax.axhline(0, color="black", linestyle="--", linewidth=0.65)
        ax.axvline(0, color="black", linestyle="--", linewidth=0.65)
        ax.set_title(f"Region {region} ({reg['n']:,} parcels)")
        ax.set_xlabel("Slope change (%) - lower is better")
        if panel_idx == 0:
            ax.set_ylabel("Contiguity change - higher is better")
        ax.grid(True, alpha=0.22)
        if legend_handles is None:
            legend_handles, legend_labels = ax.get_legend_handles_labels()
    fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.5, -0.06),
    )
    fig.suptitle("Scalarised local ranking fills the slope-contiguity tradeoff left by DRL", y=1.04)
    fig.subplots_adjust(bottom=0.22, top=0.82, wspace=0.28)
    save_figure(fig, "fig4_tradeoff.png")


def write_source_audit(t: dict[str, pd.DataFrame]) -> None:
    audit = {
        "source_tables": sorted([p.name for p in ART.glob("*.csv")]),
        "trajectory_sources": {
            f"{r['region']}_{m}_seed{s}": str(drl_eval_path(r["region"], r["code"], m, s))
            for r in REGIONS
            for m in ["lagrangian", "entonly"]
            for s in range(5)
        },
        "figure_files": [
            "fig1_cross_region.png",
            "fig2_per_seed_bimodal.png",
            "fig3_trajectories.png",
            "fig4_tradeoff.png",
        ],
    }
    path = ART / "ceus_figure_generation_audit.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)
    for target_dir in [Path("D:/test/CEUS_submission_paper2/07_declarations_and_checks")]:
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target_dir / path.name)


def main() -> None:
    tables = read_tables()
    validate_trajectories(tables["per_seed"])
    fig1_cross_region(tables)
    fig2_per_seed(tables)
    fig3_trajectories(tables)
    fig4_tradeoff(tables)
    write_source_audit(tables)
    print("[ok] CEUS figures regenerated and copied to submission folders")


if __name__ == "__main__":
    main()
