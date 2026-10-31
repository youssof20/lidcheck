import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lidcheck.io import ROOT

plt.rcParams.update({"figure.facecolor": "white", "axes.spines.top": False,
                     "axes.spines.right": False, "axes.labelcolor": "#1b2430",
                     "text.color": "#1b2430", "axes.grid": True,
                     "grid.color": "#e6e9ed", "font.size": 10})
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
