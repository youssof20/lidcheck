import json

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from lidcheck.benchmark import config, extract
from lidcheck.evaluate import auc_interval
from lidcheck.io import ROOT, write_json
from lidcheck.models import fit, serialize


def run() -> None:
    cfg = config()
    df, arrays, _ = extract()
    rows = []
    for dataset, rule in [("eyes", "11"), ("eyes", "13"), ("cp", "who2024")]:
        use = (df.dataset.to_numpy() == dataset) & np.isfinite(arrays["none"]).all(axis=1)
        frame = df[use].reset_index(drop=True)
        x = arrays["none"][use]
        threshold = np.where(frame.age < 24, 10.5, 11.0) if rule == "who2024" else float(rule)
        y = (frame.hb.to_numpy() < threshold).astype(int)
        g = frame.group.to_numpy()
        pred = []
        reg = []
        for repeat in range(cfg["repeats"]):
            p = np.zeros(len(y))
            hb = np.zeros(len(y))
            for train, test in StratifiedGroupKFold(
                5, shuffle=True, random_state=cfg["seed"] + repeat
            ).split(x, y, g):
                model = fit(x[train], y[train], g[train], cfg["seed"] + repeat)
                p[test] = model.predict(x[test])
                regression = make_pipeline(StandardScaler(), Ridge(alpha=10)).fit(
                    x[train], frame.hb.to_numpy()[train]
                )
                hb[test] = regression.predict(x[test])
            pred.append(p)
            reg.append(hb)
        ci = auc_interval(y, np.mean(pred, axis=0), g, cfg["bootstrap"], cfg["seed"])
        rows.append(
            dict(
                dataset=dataset,
                label_rule=rule,
                n=len(y),
                positive=int(y.sum()),
                hb_mae=float(mean_absolute_error(frame.hb, np.mean(reg, axis=0))),
                **ci,
            )
        )
    pd.DataFrame(rows).to_csv(ROOT / "results/tables/label_sensitivity.csv", index=False)
    path = ROOT / "web/public/model/manifest.json"
    manifest = json.loads(path.read_text())
    models = {}
    for method, array in arrays.items():
        use = (df.dataset.to_numpy() == "eyes") & np.isfinite(array).all(axis=1)
        if use.sum() < 30:
            continue
        y = df.label.to_numpy()[use].astype(int)
        if min(np.bincount(y)) < 10:
            continue
        models[method] = serialize(fit(array[use], y, df.group.to_numpy()[use], cfg["seed"]))
    manifest["study_models"] = models
    write_json(path, manifest)
