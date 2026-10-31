import json

import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve

from lidcheck.benchmark import config, extract
from lidcheck.io import ROOT, write_json


def aggregate() -> None:
    cfg = config()
    df, _, _ = extract()
    oof = pd.read_csv(ROOT / "data/interim/oof.csv")
    roc_rows, cal_rows, risk_rows = [], [], []
    for dataset in ["eyes", "cp"]:
        part = oof[(oof.dataset == dataset) & (oof.method == "none")]
        y = part.label.to_numpy()
        p = part.probability.to_numpy()
        groups = df.iloc[part["index"]].group.to_numpy()
        grid = np.linspace(0, 1, 101)
        curves = []
        rng = np.random.default_rng(cfg["seed"])
        clusters = [np.flatnonzero(groups == g) for g in np.unique(groups)]
        for _ in range(cfg["bootstrap"]):
            ix = np.concatenate(
                [clusters[i] for i in rng.integers(0, len(clusters), len(clusters))]
            )
            if len(np.unique(y[ix])) < 2:
                continue
            fpr, tpr, _ = roc_curve(y[ix], p[ix])
            curves.append(np.interp(grid, fpr, tpr))
        fpr, tpr, _ = roc_curve(y, p)
        line = np.interp(grid, fpr, tpr)
        low, high = np.quantile(curves, [0.025, 0.975], axis=0)
        for x, v, lower, upper in zip(grid, line, low, high):
            roc_rows.append(dict(dataset=dataset, n=len(y), fpr=x, tpr=v, low=lower, high=upper))
        for b in range(10):
            use = np.minimum((p * 10).astype(int), 9) == b
            if use.any():
                cal_rows.append(
                    dict(
                        dataset=dataset,
                        n=len(y),
                        bin=b,
                        count=int(use.sum()),
                        predicted=float(p[use].mean()),
                        observed=float(y[use].mean()),
                    )
                )
        for gate in [False, True]:
            for band in np.linspace(0, 0.5, 51):
                keep = abs(p - part.threshold.to_numpy()) >= band
                if gate:
                    keep &= part.quality_pass.to_numpy()
                if keep.any():
                    risk_rows.append(
                        dict(
                            dataset=dataset,
                            n=len(y),
                            gate=gate,
                            band=band,
                            coverage=float(keep.mean()),
                            risk=float(
                                ((p[keep] >= part.threshold.to_numpy()[keep]) != y[keep]).mean()
                            ),
                        )
                    )
    for name, rows in [("roc", roc_rows), ("calibration", cal_rows), ("risk_coverage", risk_rows)]:
        pd.DataFrame(rows).to_csv(ROOT / f"results/tables/{name}.csv", index=False)
    comparisons = []
    for dataset in ["eyes", "cp"]:
        part = oof[oof.dataset == dataset]
        available = list(part.method.unique())
        common = set.intersection(*(set(part[part.method == m]["index"]) for m in available))
        from lidcheck.evaluate import auc_interval

        for method in available:
            subset = part[(part.method == method) & part["index"].isin(common)]
            if len(subset) < 10 or subset.label.nunique() < 2:
                continue
            ci = auc_interval(
                subset.label.to_numpy(),
                subset.probability.to_numpy(),
                df.iloc[subset["index"]].group.to_numpy(),
                cfg["bootstrap"],
                cfg["seed"],
            )
            comparisons.append(dict(dataset=dataset, method=method, n=len(subset), **ci))
    pd.DataFrame(comparisons).to_csv(ROOT / "results/tables/common_subset.csv", index=False)


def summary() -> None:
    benchmark = json.loads((ROOT / "results/benchmark.json").read_text())
    audit = pd.read_csv(ROOT / "results/tables/data_audit.csv")
    seg = pd.read_csv(ROOT / "results/tables/segmentation.csv")
    manifest = json.loads((ROOT / "web/public/model/manifest.json").read_text())
    results = dict(
        benchmark=benchmark,
        audit=audit.to_dict("records"),
        segmentation=dict(
            n=len(seg), mean_dice=float(seg.dice.mean()), mean_iou=float(seg.iou.mean())
        ),
        populations=manifest["populations"],
        study={"status": "not collected", "participants": 0},
        baselines=pd.read_csv(ROOT / "results/tables/baselines.csv").to_dict("records"),
    )
    stress_path = ROOT / "results/tables/lighting_stress.csv"
    if stress_path.exists():
        stress = pd.read_csv(stress_path)
        results["stress"] = {}
        for dataset, part in stress[stress.training == "unshifted"].groupby("dataset"):
            raw = part[part.method == "none"]
            comparisons = []
            for method in part.method.unique():
                if method == "none":
                    continue
                merged = raw.merge(
                    part[part.method == method],
                    on=["kind", "level", "strength"],
                    suffixes=("_raw", "_norm"),
                )
                overlap = (merged.low_raw <= merged.high_norm) & (
                    merged.low_norm <= merged.high_raw
                )
                comparisons.append(
                    dict(
                        method=method,
                        levels=len(merged),
                        overlap_all=bool(overlap.all()),
                        mean_auc_difference=float((merged.value_norm - merged.value_raw).mean()),
                    )
                )
            results["stress"][dataset] = dict(
                raw_min=float(raw.value.min()),
                raw_max=float(raw.value.max()),
                comparisons=comparisons,
            )
    cross = ROOT / "results/tables/cross_dataset.csv"
    if cross.exists():
        results["cross_dataset"] = json.loads(pd.read_csv(cross).to_json(orient="records"))
    write_json(ROOT / "results/summary.json", results)
