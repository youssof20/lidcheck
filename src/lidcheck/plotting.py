import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lidcheck.io import ROOT

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.labelcolor": "#1b2430",
        "text.color": "#1b2430",
        "axes.grid": True,
        "grid.color": "#e6e9ed",
        "font.size": 10,
    }
)
COLORS = ["#1b2430", "#2f5d8a", "#8a94a0", "#b5483a", "#567568", "#71638b"]


def save(fig: plt.Figure, name: str) -> None:
    folder = ROOT / "results/figures"
    folder.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(folder / name, dpi=200)
    plt.close(fig)


def audit_figure(df) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(8, 3))
    for ax, (name, part) in zip(axes, df.groupby("dataset"), strict=True):
        ax.hist(part.hb.dropna(), bins=15, color="#8a94a0")
        for threshold in sorted(part.threshold.unique()):
            ax.axvline(threshold, color="#b5483a", linestyle="--")
        ax.set(title=f"{name}: n={len(part)}", xlabel="Hemoglobin (g/dL)", ylabel="Images")
    save(fig, "data_audit.png")


def figures() -> None:
    import pandas as pd
    import numpy as np

    tables = ROOT / "results/tables"
    roc = pd.read_csv(tables / "roc.csv")
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.3))
    for ax, (dataset, part) in zip(axes, roc.groupby("dataset")):
        ax.plot(part.fpr, part.tpr, color=COLORS[1])
        ax.fill_between(part.fpr, part.low, part.high, color=COLORS[1], alpha=0.15)
        ax.plot([0, 1], [0, 1], color=COLORS[2], linestyle="--")
        point = part[part.tpr >= 0.9].iloc[0]
        ax.scatter([point.fpr], [point.tpr], color=COLORS[0], s=20)
        ax.set(
            title=f"{dataset}: n={part.n.iloc[0]}",
            xlabel="False positive rate",
            ylabel="Sensitivity",
            xlim=(0, 1),
            ylim=(0, 1),
        )
    save(fig, "roc_grouped_cv.png")
    cal = pd.read_csv(tables / "calibration.csv")
    fig, axes = plt.subplots(2, 2, figsize=(8, 5), gridspec_kw={"height_ratios": [3, 1]})
    for col, (dataset, part) in enumerate(cal.groupby("dataset")):
        ax = axes[0, col]
        ax.plot(part.predicted, part.observed, "o-", color=COLORS[1])
        ax.plot([0, 1], [0, 1], "--", color=COLORS[2])
        ax.set(
            title=f"{dataset}: n={part.n.iloc[0]}",
            ylabel="Observed fraction",
            xlim=(0, 1),
            ylim=(0, 1),
        )
        axes[1, col].bar(part.predicted, part["count"], width=0.07, color=COLORS[2])
        axes[1, col].set(xlabel="Predicted probability", ylabel="Count", xlim=(0, 1))
    save(fig, "calibration.png")
    risk = pd.read_csv(tables / "risk_coverage.csv")
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.3))
    for ax, (dataset, part) in zip(axes, risk.groupby("dataset")):
        for gate, subset in part.groupby("gate"):
            ax.plot(
                subset.coverage,
                subset.risk,
                label="With gate" if gate else "Without gate",
                color=COLORS[int(gate)],
                linestyle="-" if gate else "--",
            )
        ax.set(
            title=f"{dataset}: n={part.n.iloc[0]}",
            xlabel="Share answered",
            ylabel="Error rate",
            xlim=(0, 1),
            ylim=(0, 1),
        )
        ax.legend(frameon=False, fontsize=8)
    save(fig, "risk_coverage.png")
    seg = pd.read_csv(tables / "segmentation.csv")
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.hist(seg.dice, bins=np.linspace(0, 1, 21), color=COLORS[2])
    ax.set(
        title=f"Heuristic mask overlap: n={len(seg)}",
        xlabel="Dice against hand segmentation",
        ylabel="Images",
    )
    save(fig, "segmentation_examples.png")
    if (tables / "lighting_stress.csv").exists():
        stress = pd.read_csv(tables / "lighting_stress.csv")
        fig, axes = plt.subplots(2, 2, figsize=(10, 6))
        for row, dataset in enumerate(["eyes", "cp"]):
            for col, kind in enumerate(["temperature", "exposure"]):
                ax = axes[row, col]
                part = stress[
                    (stress.dataset == dataset)
                    & (stress.kind == kind)
                    & (stress.strength == 1)
                    & (stress.training == "unshifted")
                ]
                for i, (method, sub) in enumerate(part.groupby("method")):
                    sub = sub.sort_values("level")
                    ax.plot(sub.level, sub.value, label=method, color=COLORS[i])
                    ax.fill_between(sub.level, sub.low, sub.high, color=COLORS[i], alpha=0.08)
                ax.set(
                    title=f"{dataset}: n={int(part.n.max())}",
                    xlabel="Temperature (K)" if kind == "temperature" else "Exposure multiplier",
                    ylabel="AUROC",
                    ylim=(0, 1),
                )
                ax.legend(frameon=False, fontsize=7, ncol=2)
        save(fig, "lighting_stress.png")
    if (tables / "cross_dataset.csv").exists():
        cross = pd.read_csv(tables / "cross_dataset.csv")
        import json

        benchmark = json.loads((ROOT / "results/benchmark.json").read_text())
        fig, ax = plt.subplots(figsize=(6, 3.8))
        ax.grid(False)
        ax.set_xticks([0, 1], ["Test Eyes (adults)", "Test CP (children)"])
        ax.set_yticks([0, 1], ["Train Eyes", "Train CP"])
        ax.set(xlim=(-0.5, 1.5), ylim=(1.5, -0.5), title="Raw-color AUROC across populations")
        for i, source in enumerate(["eyes", "cp"]):
            for j, target in enumerate(["eyes", "cp"]):
                if source == target:
                    item = benchmark[f"{source}/none"]
                    ci = item["metrics"]["auroc"]
                    n = item["n"]
                    label = "Within-dataset CV"
                else:
                    item = cross[
                        (cross.source == source)
                        & (cross.target == target)
                        & (cross.method == "none")
                    ].iloc[0]
                    ci = item
                    n = int(item.n)
                    label = "Transfer"
                ax.text(
                    j,
                    i,
                    f"{label}\n{ci['value']:.3f} [{ci['low']:.3f}, {ci['high']:.3f}]\nn={n}",
                    ha="center",
                    va="center",
                    fontsize=10,
                )
        fig.text(
            0.5,
            0.01,
            "Populations and acquisition differ; no pooled accuracy claim.",
            ha="center",
            fontsize=8,
        )
        save(fig, "cross_dataset.png")


def summary() -> None:
    from lidcheck.reporting import summary as build_summary

    build_summary()
