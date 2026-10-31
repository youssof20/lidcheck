import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from lidcheck.io import ROOT, write_json


def icc(matrix: np.ndarray) -> float | None:
    n, k = matrix.shape
    if n < 2 or k < 2:
        return None
    grand = matrix.mean()
    subject = matrix.mean(axis=1)
    condition = matrix.mean(axis=0)
    ms_subject = k * np.var(subject, ddof=1)
    residual = matrix - subject[:, None] - condition[None, :] + grand
    ms_error = float((residual**2).sum() / ((n - 1) * (k - 1)))
    ms_condition = n * np.var(condition, ddof=1)
    denominator = ms_subject + (k - 1) * ms_error + k * (ms_condition - ms_error) / n
    return float((ms_subject - ms_error) / denominator) if denominator else None


def run(path: Path | None = None) -> None:
    if path is None:
        write_json(
            ROOT / "results/consistency.json",
            {
                "status": "not collected",
                "participants": 0,
                "reason": "Written consent and real study records are required. Dummy tests are not evidence.",
            },
        )
        return
    data = json.loads(path.read_text())
    records = []
    for entry in data["entries"]:
        if entry.get("synthetic"):
            continue
        for method, m in entry["measurements"].items():
            records.append(
                dict(
                    participant=entry["participant"],
                    condition=int(entry["condition"]),
                    shot=int(entry["shot"]),
                    method=method,
                    score=m.get("score"),
                    rejected=m["rejected"],
                    features=m["features"],
                    synthetic_drift=m.get("synthetic_drift"),
                )
            )
    if not records:
        raise ValueError("No non-synthetic study records")
    df = pd.DataFrame(records)
    if df.duplicated(["participant", "condition", "shot", "method"]).any():
        raise ValueError("Repeated participant/condition/shot records")
    result = {}
    for method, part in df.groupby("method"):
        eligible = part[~part.rejected & part.score.notna()]
        means = (
            eligible.groupby(["participant", "condition"])
            .score.mean()
            .unstack()
            .reindex(columns=range(6))
        )
        counts = (
            eligible.groupby(["participant", "condition"])
            .shot.nunique()
            .unstack()
            .reindex(columns=range(6))
        )
        means = means.where(counts == 2)
        complete = means.dropna()
        rng = np.random.default_rng(20261031)
        values = []
        if len(complete) >= 2:
            for _ in range(2000):
                v = icc(complete.to_numpy()[rng.integers(0, len(complete), len(complete))])
                if v is not None and np.isfinite(v):
                    values.append(v)
        real, synthetic = [], []
        for _, person in eligible.groupby("participant"):
            if person.condition.nunique() < 2:
                continue
            f = np.array(person.features.tolist(), dtype=float)
            drift = float(np.sqrt(np.mean(np.var(f, axis=0))))
            synth = pd.to_numeric(person.synthetic_drift, errors="coerce").mean()
            if np.isfinite(synth):
                real.append(drift)
                synthetic.append(synth)
        corr = (
            float(spearmanr(real, synthetic).statistic)
            if len(real) >= 3 and np.std(real) > 0 and np.std(synthetic) > 0
            else None
        )
        deviations = eligible.groupby("participant").score.std().dropna()
        sd_boot = (
            [
                float(
                    deviations.to_numpy()[rng.integers(0, len(deviations), len(deviations))].mean()
                )
                for _ in range(2000)
            ]
            if len(deviations)
            else []
        )
        corr_boot = []
        if corr is not None:
            for _ in range(2000):
                ix = rng.integers(0, len(real), len(real))
                a = np.array(real)[ix]
                b = np.array(synthetic)[ix]
                if np.std(a) > 0 and np.std(b) > 0:
                    corr_boot.append(float(spearmanr(a, b).statistic))
        result[method] = dict(
            participants=int(part.participant.nunique()),
            complete_participants=len(complete),
            rejected=float(part.rejected.mean()),
            within_person_sd=float(deviations.mean()) if len(deviations) else None,
            within_person_sd_interval=np.quantile(sd_boot, [0.025, 0.975]).tolist()
            if sd_boot
            else None,
            icc=icc(complete.to_numpy()) if len(complete) >= 2 else None,
            icc_interval=np.quantile(values, [0.025, 0.975]).tolist() if values else None,
            drift_correlation=corr,
            drift_interval=np.quantile(corr_boot, [0.025, 0.975]).tolist() if corr_boot else None,
            drift_pairs=len(real),
        )
    write_json(
        ROOT / "results/consistency.json",
        {"status": "stability only; no hemoglobin labels", "methods": result},
    )
    from lidcheck.plotting import save
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(9, 3), squeeze=False)
    selected = [m for m in ["none", "gray_world"] if m in result]
    for ax, method in zip(axes.ravel(), selected):
        part = df[(df.method == method) & df.score.notna()]
        for _, person in part.groupby("participant"):
            means = person.groupby("condition").score.mean()
            ax.plot(means.index, means.values, alpha=0.6)
        ax.set(
            title=f"{method}: n={part.participant.nunique()}; ICC={result[method]['icc']}",
            xlabel="Lighting condition",
            ylabel="Model score",
        )
    save(fig, "real_lighting_consistency.png")
