import json
import pickle

import numpy as np
import pandas as pd
import yaml
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from lidcheck.evaluate import bootstrap, metrics
from lidcheck.export import export_model
from lidcheck.features import analyze
from lidcheck.io import ROOT, read_image, write_json
from lidcheck.models import fit, serialize
from lidcheck.normalize import METHODS
from lidcheck.quality import failures


def config() -> dict:
    return yaml.safe_load((ROOT / "configs/default.yaml").read_text())


def extract() -> tuple:
    cache = ROOT / "data/interim/features.pkl"
    if cache.exists():
        with cache.open("rb") as f:
            return pickle.load(f)
    df = (
        pd.read_csv(ROOT / "data/interim/index.csv").dropna(subset=["label"]).reset_index(drop=True)
    )
    arrays = {method: [] for method in METHODS}
    quality, overlaps = [], []
    for i, row in df.iterrows():
        rgb = read_image(row)
        for method in METHODS:
            out = analyze(rgb, method, references=row.dataset == "eyes")
            arrays[method].append(out["features"])
            if method == "none":
                quality.append(out["quality"])
                if isinstance(row["mask"], str) and row["mask"]:
                    hand = read_image(row, mask=True).max(axis=-1) > 0
                    mask = out["mask"]
                    inter = (hand & mask).sum()
                    overlaps.append(
                        dict(
                            dataset=row.dataset,
                            dice=2 * inter / max(hand.sum() + mask.sum(), 1),
                            iou=inter / max((hand | mask).sum(), 1),
                        )
                    )
        if i % 100 == 0:
            print(f"Extracted {i}/{len(df)}", flush=True)
    pd.DataFrame(overlaps).to_csv(ROOT / "results/tables/segmentation.csv", index=False)
    result = df, {k: np.array(v) for k, v in arrays.items()}, pd.DataFrame(quality)
    with cache.open("wb") as f:
        pickle.dump(result, f)
    return result


def run() -> None:
    cfg = config()
    df, arrays, quality = extract()
    records, report, fitted = [], {}, {}
    quality_rows = []
    for dataset in ["eyes", "cp"]:
        quality_part = quality[df.dataset == dataset]
        reasons = [failures(q, cfg["quality"]) for q in quality_part.to_dict("records")]
        quality_rows.append(
            dict(
                dataset=dataset,
                n=len(reasons),
                rejected=sum(bool(r) for r in reasons),
                **{
                    k: sum(k in r for r in reasons)
                    for k in ["eyelid", "blur", "exposure", "glare", "cohesion"]
                },
            )
        )
        for method in METHODS:
            eligible = (df.dataset == dataset).to_numpy() & np.isfinite(arrays[method]).all(axis=1)
            ix = np.flatnonzero(eligible)
            if len(ix) < 30:
                report[f"{dataset}/{method}"] = dict(status="not applicable", n=len(ix))
                continue
            x, y, groups = (
                arrays[method][ix],
                df.label.to_numpy()[ix].astype(int),
                df.group.to_numpy()[ix],
            )
            if min(np.bincount(y)) < 10:
                report[f"{dataset}/{method}"] = dict(status="insufficient classes", n=len(ix))
                continue
            predictions = np.zeros((cfg["repeats"], len(ix)))
            thresholds = np.zeros_like(predictions)
            bands = np.zeros_like(predictions)
            folds = []
            for repeat in range(cfg["repeats"]):
                splitter = StratifiedGroupKFold(
                    cfg["folds"], shuffle=True, random_state=cfg["seed"] + repeat
                )
                for fold, (train, test) in enumerate(splitter.split(x, y, groups)):
                    assert not set(groups[train]) & set(groups[test])
                    model = fit(x[train], y[train], groups[train], cfg["seed"] + repeat)
                    predictions[repeat, test] = model.predict(x[test])
                    thresholds[repeat, test] = model.threshold
                    bands[repeat, test] = model.band
                    folds.append(
                        dict(repeat=repeat, fold=fold, train=ix[train], test=ix[test], model=model)
                    )
                print(f"{dataset}/{method}: repeat {repeat + 1}/{cfg['repeats']}", flush=True)
            average = predictions.mean(axis=0)
            metric = bootstrap(y, average, groups, cfg["bootstrap"], cfg["seed"])
            pooled = metrics(np.tile(y, cfg["repeats"]), predictions.ravel())
            report[f"{dataset}/{method}"] = dict(
                status="evaluated",
                n=len(ix),
                coverage=float(eligible.sum() / (df.dataset == dataset).sum()),
                metrics=metric,
                pooled_repeated_metrics=pooled,
            )
            fitted[f"{dataset}/{method}"] = folds
            for j, index in enumerate(ix):
                records.append(
                    dict(
                        index=int(index),
                        dataset=dataset,
                        method=method,
                        label=int(y[j]),
                        probability=float(average[j]),
                        threshold=float(thresholds[:, j].mean()),
                        band=float(bands[:, j].mean()),
                        quality_pass=not failures(quality.iloc[index].to_dict(), cfg["quality"]),
                    )
                )
            if dataset == "eyes" and method == "none":
                final = fit(x, y, groups, cfg["seed"])
                export_model(final, x, y, report[f"{dataset}/{method}"], cfg["quality"])
                manifest_path = ROOT / "web/public/model/manifest.json"
                manifest = json.loads(manifest_path.read_text())
                manifest["ensemble"] = [serialize(f["model"]) for f in folds[: cfg["folds"]]]
                write_json(manifest_path, manifest)
    pd.DataFrame(records).to_csv(ROOT / "data/interim/oof.csv", index=False)
    pd.DataFrame(quality_rows).to_csv(ROOT / "results/tables/quality.csv", index=False)
    with (ROOT / "data/interim/folds.pkl").open("wb") as f:
        pickle.dump(fitted, f)
    write_json(ROOT / "results/benchmark.json", report)
    baselines(df, arrays)
    from lidcheck.supplement import run as secondary
    from lidcheck.reporting import aggregate

    secondary()
    aggregate()


def baselines(df: pd.DataFrame, arrays: dict) -> None:
    cfg = config()
    rows = []
    for dataset in ["eyes", "cp"]:
        use = (df.dataset == dataset).to_numpy() & np.isfinite(arrays["none"]).all(axis=1)
        frame = df[use].reset_index(drop=True)
        x = arrays["none"][use]
        y, g = frame.label.astype(int).to_numpy(), frame.group.to_numpy()
        for name in ["majority", "demographics", "gradient_boosting"]:
            scores = []
            for repeat in range(cfg["repeats"]):
                p = np.zeros(len(y))
                for train, test in StratifiedGroupKFold(
                    5, shuffle=True, random_state=cfg["seed"] + repeat
                ).split(x, y, g):
                    if name == "majority":
                        p[test] = y[train].mean()
                    elif name == "gradient_boosting":
                        model = HistGradientBoostingClassifier(
                            max_iter=60, max_leaf_nodes=7, random_state=cfg["seed"]
                        )
                        model.fit(x[train], y[train])
                        p[test] = model.predict_proba(x[test])[:, 1]
                    else:
                        prep = ColumnTransformer(
                            [
                                ("age", make_pipeline(SimpleImputer(), StandardScaler()), ["age"]),
                                (
                                    "category",
                                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                                    ["sex", "site"],
                                ),
                            ]
                        )
                        model = make_pipeline(prep, LogisticRegression(max_iter=2000))
                        model.fit(frame.iloc[train], y[train])
                        p[test] = model.predict_proba(frame.iloc[test])[:, 1]
                scores.append(p)
            rows.append(
                dict(dataset=dataset, model=name, n=len(y), **metrics(y, np.mean(scores, axis=0)))
            )
    pd.DataFrame(rows).to_csv(ROOT / "results/tables/baselines.csv", index=False)
