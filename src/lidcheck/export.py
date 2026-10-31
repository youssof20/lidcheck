import subprocess

import numpy as np

from lidcheck.features import NAMES
from lidcheck.io import ROOT, write_json
from lidcheck.models import serialize


def export_model(model, x, y, result, quality) -> None:
    try:
        commit = subprocess.check_output(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        commit = "uncommitted"
    p = model.predict(x)
    passed = (
        result["metrics"]["auroc"]["low"] >= 0.70
        and result["metrics"]["specificity_at_90_sensitivity"]["value"] >= 0.50
    )
    manifest = dict(
        version="0.1.0",
        git_commit=commit,
        normalization="none",
        features=NAMES,
        training_datasets=[dict(name="Eyes-defy-anemia", images=len(y))],
        metrics=result["metrics"],
        quality=quality,
        image_size=96,
        shipping_bar=passed,
        clinical_validation=False,
        populations={
            "older": "validated-in-prototype" if passed else "demo only, not validated",
            "child": "demo only, not validated",
        },
        density_bands={
            str(label): np.histogram(p[y == label], bins=20, range=(0, 1))[0].tolist()
            for label in [0, 1]
        },
        interval_description="Across-fold model score range; not a clinical confidence interval",
        model=serialize(model),
    )
    write_json(ROOT / "web/public/model/manifest.json", manifest)
