import io
import pickle
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat

import numpy as np
import pandas as pd
from PIL import Image

from lidcheck.benchmark import config, extract
from lidcheck.evaluate import auc_interval
from lidcheck.features import features
from lidcheck.io import ROOT, read_image
from lidcheck.models import fit
from lidcheck.normalize import METHODS, normalize
from lidcheck.quality import failures, measure
from lidcheck.segmentation import linear, srgb, segment


def shifts() -> list[dict]:
    return (
        [
            dict(kind="temperature", level=t, strength=s)
            for t in [2700, 3500, 4500, 5500, 6500, 7500]
            for s in [0.5, 1.0]
        ]
        + [dict(kind="exposure", level=e, strength=1.0) for e in [0.4, 0.6, 1.0, 1.4, 2.0]]
        + [dict(kind="noise", level=e, strength=1.0) for e in [0.005, 0.015, 0.03]]
        + [dict(kind="jpeg", level=e, strength=1.0) for e in [90, 60]]
        + [dict(kind=k, level=1.0, strength=1.0) for k in ["mixed", "glare"]]
    )


def gains(temperature: float) -> np.ndarray:
    t = temperature / 100
    r = 255 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = (
        99.4708025861 * np.log(t) - 161.1195681661
        if t <= 66
        else 288.1221695283 * (t - 60) ** -0.0755148492
    )
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * np.log(t - 10) - 305.0447927307)
    color = linear(np.clip([r, g, b], 0, 255))
    return color / (color @ np.array([0.2126, 0.7152, 0.0722]))


def shift(rgb: np.ndarray, spec: dict, seed: int) -> np.ndarray:
    kind, level = spec["kind"], spec["level"]
    x = linear(rgb)
    if kind == "temperature":
        x *= 1 + spec["strength"] * (gains(level) - 1)
    elif kind == "exposure":
        x *= level
    elif kind == "noise":
        x += np.random.default_rng(seed).normal(0, level, x.shape)
    elif kind == "mixed":
        weight = np.linspace(0, 1, x.shape[1])[None, :, None]
        x *= gains(2700) * (1 - weight) + gains(7500) * weight
    elif kind == "glare":
        yy, xx = np.indices(x.shape[:2])
        blob = np.exp(
            -((xx - x.shape[1] * 0.55) ** 2 + (yy - x.shape[0] * 0.6) ** 2)
            / (x.shape[0] * 0.06) ** 2
        )
        x = x * (1 - blob[..., None]) + blob[..., None]
    elif kind == "jpeg":
        buffer = io.BytesIO()
        Image.fromarray(rgb).save(buffer, format="JPEG", quality=int(level))
        buffer.seek(0)
        return np.asarray(Image.open(buffer).convert("RGB"))
    return srgb(x)


def extract_shift(spec: dict, photos: list, references: np.ndarray, cfg: dict) -> tuple:
    vectors = {m: [] for m in METHODS}
    rejected = []
    for i, rgb in enumerate(photos):
        altered = shift(rgb, spec, cfg["seed"] + i)
        mask, cohesion = segment(altered)
        rejected.append(bool(failures(measure(altered, mask, cohesion), cfg["quality"])))
        x = linear(altered)
        for method in METHODS:
            normalized = normalize(x, method, references[i])
            vectors[method].append(
                features(normalized, mask) if normalized is not None else np.full(10, np.nan)
            )
    return spec, {m: np.array(v) for m, v in vectors.items()}, np.array(rejected)


def run() -> None:
    cfg = config()
    df, arrays, _ = extract()
    with (ROOT / "data/interim/folds.pkl").open("rb") as f:
        folds = pickle.load(f)
    cache = ROOT / "data/interim/stress.pkl"
    if cache.exists():
        with cache.open("rb") as f:
            shifted = pickle.load(f)
    else:
        shifted = []
    if len(shifted) < len(shifts()):
        photos = [read_image(row) for _, row in df.iterrows()]
        reference_flags = (df.dataset == "eyes").to_numpy()
        with ProcessPoolExecutor(max_workers=4) as executor:
            for result in executor.map(
                extract_shift,
                shifts()[len(shifted) :],
                repeat(photos),
                repeat(reference_flags),
                repeat(cfg),
            ):
                shifted.append(result)
                print(f"Extracted stress {result[0]}", flush=True)
                with cache.open("wb") as f:
                    pickle.dump(shifted, f)
    rows = []
    for key, fitted in folds.items():
        dataset, method = key.split("/")
        augmented = []
        # The same patient's augmented copies inherit its training group.
        for entry in fitted:
            train = entry["train"]
            xx = [arrays[method][train]]
            yy = [df.label.to_numpy()[train]]
            gg = [df.group.to_numpy()[train]]
            for k in [0, 10, 12, 16]:
                values = shifted[k][1][method][train]
                valid = np.isfinite(values).all(axis=1)
                xx.append(values[valid])
                yy.append(df.label.to_numpy()[train][valid])
                gg.append(df.group.to_numpy()[train][valid])
            augmented.append(
                fit(
                    np.concatenate(xx),
                    np.concatenate(yy).astype(int),
                    np.concatenate(gg),
                    cfg["seed"],
                )
            )
        for spec, vectors, reject in shifted:
            values = vectors[method]
            valid = np.isfinite(values).all(axis=1)
            for mode in ["unshifted", "augmented"]:
                total = np.zeros(len(df))
                counts = np.zeros(len(df))
                for k, entry in enumerate(fitted):
                    test = entry["test"]
                    test = test[valid[test]]
                    if not len(test):
                        continue
                    model = entry["model"] if mode == "unshifted" else augmented[k]
                    total[test] += model.predict(values[test])
                    counts[test] += 1
                use = counts > 0
                if use.sum() < 10 or df.label[use].nunique() < 2:
                    continue
                p = total[use] / counts[use]
                ci = auc_interval(
                    df.label.to_numpy()[use].astype(int),
                    p,
                    df.group.to_numpy()[use],
                    cfg["bootstrap"],
                    cfg["seed"],
                )
                rows.append(
                    dict(
                        dataset=dataset,
                        method=method,
                        training=mode,
                        **spec,
                        n=int(use.sum()),
                        rejected=float(reject[df.dataset.to_numpy() == dataset].mean()),
                        **ci,
                    )
                )
        print(f"Evaluated stress {key}", flush=True)
    pd.DataFrame(rows).to_csv(ROOT / "results/tables/lighting_stress.csv", index=False)


def transfer() -> None:
    cfg = config()
    df, arrays, _ = extract()
    rows = []
    for method in METHODS:
        for source, target in [("eyes", "cp"), ("cp", "eyes")]:
            valid = np.isfinite(arrays[method]).all(axis=1)
            train = valid & (df.dataset.to_numpy() == source)
            test = valid & (df.dataset.to_numpy() == target)
            if train.sum() < 30 or test.sum() < 30:
                rows.append(
                    dict(
                        source=source,
                        target=target,
                        method=method,
                        status="not applicable",
                        n=int(test.sum()),
                    )
                )
                continue
            model = fit(
                arrays[method][train],
                df.label.to_numpy()[train].astype(int),
                df.group.to_numpy()[train],
                cfg["seed"],
            )
            p = model.predict(arrays[method][test])
            ci = auc_interval(
                df.label.to_numpy()[test].astype(int),
                p,
                df.group.to_numpy()[test],
                cfg["bootstrap"],
                cfg["seed"],
            )
            rows.append(
                dict(
                    source=source,
                    target=target,
                    method=method,
                    status="evaluated",
                    n=int(test.sum()),
                    **ci,
                )
            )
    pd.DataFrame(rows).to_csv(ROOT / "results/tables/cross_dataset.csv", index=False)
