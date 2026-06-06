from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CSV_PATH = ROOT / "gemma4_host228_scale_sweep_summary.csv"
OUT_BASE = HERE / "gemma4_host228_scale_sweep"


def configure_matplotlib() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "font.size": 12,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.linewidth": 0.8,
            "axes.labelcolor": "#1f2933",
            "xtick.color": "#1f2933",
            "ytick.color": "#1f2933",
            "text.color": "#1f2933",
            "legend.frameon": False,
        }
    )


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    order = ["Gemma4:e2b", "Gemma4:e4b", "Gemma4:12b", "Gemma4:26b", "Gemma4:31b"]
    df["model"] = pd.Categorical(df["model"], categories=order, ordered=True)
    df = df.sort_values("model").reset_index(drop=True)
    df["label"] = df["model"].str.replace("Gemma4:", "", regex=False)
    return df


def add_value_labels(ax, bars, fmt="{:.1f}", dy=1.5, color="#1f2933") -> None:
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + dy,
            fmt.format(height),
            ha="center",
            va="bottom",
            fontsize=9.5,
            color=color,
        )


def build_figure(df: pd.DataFrame) -> plt.Figure:
    base_color = "#A7B0BC"
    full_color = "#159A9C"
    accent_color = "#E36B2C"
    dark_color = "#2D4A7C"
    grid_color = "#E5E7EB"

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(13.333, 7.5),
        gridspec_kw={"width_ratios": [1.22, 1.0], "wspace": 0.26},
    )
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=0.08, right=0.98, top=0.78, bottom=0.14, wspace=0.26)

    # Panel A: execution accuracy by model scale.
    ax = axes[0]
    x = np.arange(len(df))
    width = 0.34
    base_bars = ax.bar(
        x - width / 2,
        df["baseline_ex_pct"],
        width,
        label="Schema-only baseline",
        color=base_color,
        edgecolor="white",
        linewidth=0.8,
    )
    full_bars = ax.bar(
        x + width / 2,
        df["full_ex_pct"],
        width,
        label="Full NL2Semantic2SQL",
        color=full_color,
        edgecolor="white",
        linewidth=0.8,
    )
    add_value_labels(ax, base_bars)
    add_value_labels(ax, full_bars)

    for i, delta in enumerate(df["delta_ex_pp"]):
        y = max(df.loc[i, "baseline_ex_pct"], df.loc[i, "full_ex_pct"]) + 8
        ax.text(
            i,
            y,
            f"+{delta:.1f} pp",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color=full_color,
        )

    ax.set_title("A  Grounding improves every tested scale", loc="left", pad=12, fontsize=15, fontweight="bold")
    ax.set_ylabel("Execution accuracy on CQ-125 (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(df["label"])
    ax.set_ylim(0, 104)
    ax.set_yticks(np.arange(0, 101, 20))
    ax.grid(axis="y", color=grid_color, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.01), ncol=1, fontsize=10)

    # Panel B: full-pipeline accuracy-runtime trade-off.
    ax = axes[1]
    ax.plot(
        df["full_minutes"],
        df["full_ex_pct"],
        color="#94A3B8",
        linewidth=1.6,
        zorder=1,
    )
    colors = [full_color] * len(df)
    colors[df.index[df["model"].astype(str) == "Gemma4:26b"][0]] = accent_color
    colors[df.index[df["model"].astype(str) == "Gemma4:31b"][0]] = dark_color
    sizes = [135, 135, 150, 190, 190]

    ax.scatter(
        df["full_minutes"],
        df["full_ex_pct"],
        s=sizes,
        color=colors,
        edgecolor="white",
        linewidth=1.6,
        zorder=3,
    )
    for _, row in df.iterrows():
        dx, dy = 0.25, 0.7
        if row["label"] == "e2b":
            dx, dy = -0.25, -3.2
        elif row["label"] == "e4b":
            dx, dy = -1.9, -2.5
        elif row["label"] == "12b":
            dx, dy = -1.3, 1.0
        elif row["label"] == "26b":
            dx, dy = -2.0, 1.3
        elif row["label"] == "31b":
            dx, dy = 0.35, 0.6
        ax.text(
            row["full_minutes"] + dx,
            row["full_ex_pct"] + dy,
            str(row["label"]),
            fontsize=10,
            fontweight="bold" if row["label"] in {"26b", "31b"} else "normal",
            color=accent_color if row["label"] == "26b" else dark_color if row["label"] == "31b" else "#334155",
        )

    row26 = df[df["label"] == "26b"].iloc[0]
    row31 = df[df["label"] == "31b"].iloc[0]
    faster_pct = (row31["full_minutes"] - row26["full_minutes"]) / row31["full_minutes"] * 100
    ax.annotate(
        f"26B is {faster_pct:.0f}% faster\nwith only 0.8 pp lower EX",
        xy=(row26["full_minutes"], row26["full_ex_pct"]),
        xytext=(8.8, 95.0),
        arrowprops=dict(arrowstyle="->", color=accent_color, linewidth=1.2),
        fontsize=10.5,
        color=accent_color,
        ha="left",
        va="center",
    )

    ax.set_title("B  Accuracy-runtime trade-off", loc="left", pad=12, fontsize=15, fontweight="bold")
    ax.set_xlabel("Full-pipeline wall-clock time (min)")
    ax.set_ylabel("Full-pipeline EX (%)")
    ax.set_xlim(11.0, 22.2)
    ax.set_ylim(60, 96.5)
    ax.set_xticks(np.arange(12, 23, 2))
    ax.set_yticks(np.arange(60, 97, 10))
    ax.grid(color=grid_color, linewidth=0.8)
    ax.set_axisbelow(True)

    fig.suptitle(
        "Gemma4 host228 CQ-125 scale sweep",
        x=0.035,
        y=0.97,
        ha="left",
        fontsize=19,
        fontweight="bold",
    )
    fig.text(
        0.035,
        0.915,
        "Base = direct schema-only generation; Full = NL2Semantic2SQL with semantic grounding, postprocessing, and execution-time correction.",
        ha="left",
        va="top",
        fontsize=10.5,
        color="#475569",
    )
    fig.text(
        0.035,
        0.025,
        "Source: gemma4_host228_scale_sweep_summary.csv. Descriptive fixed-host deployment probe; not a stochastic significance test.",
        ha="left",
        va="bottom",
        fontsize=9.5,
        color="#64748B",
    )

    return fig


def main() -> None:
    configure_matplotlib()
    df = load_data()
    fig = build_figure(df)
    fig.savefig(f"{OUT_BASE}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(f"{OUT_BASE}.svg", bbox_inches="tight", facecolor="white")
    fig.savefig(f"{OUT_BASE}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
