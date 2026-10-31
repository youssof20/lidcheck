import numpy as np

from lidcheck.normalize import normalize
from lidcheck.quality import measure
from lidcheck.segmentation import lab, linear, segment

NAMES = ["L_median", "L_iqr", "a_median", "a_iqr", "b_median", "b_iqr",
         "red_green", "erythema", "saturation_median", "saturation_iqr"]


def features(x: np.ndarray, mask: np.ndarray) -> np.ndarray:
    roi = x[mask]
    if len(roi) == 0:
        return np.full(10, np.nan)
    colors = lab(roi)
    result = []
    for i in range(3):
        result.extend([np.median(colors[:, i]), np.quantile(colors[:, i], 0.75) - np.quantile(colors[:, i], 0.25)])
    result.extend([np.median(roi[:, 0] / np.maximum(roi[:, 1], 1e-8)),
                   np.median(np.log((roi[:, 0] + 1e-8) / (roi[:, 1] + 1e-8)))])
    sat = (roi.max(axis=1) - roi.min(axis=1)) / np.maximum(roi.max(axis=1), 1e-8)
    result.extend([np.median(sat), np.quantile(sat, 0.75) - np.quantile(sat, 0.25)])
    return np.array(result)


def analyze(rgb: np.ndarray, method: str = "none", references: bool = True) -> dict:
    mask, cohesion = segment(rgb)
    q = measure(rgb, mask, cohesion)
    x = normalize(linear(rgb), method, references)
    values = features(x, mask) if x is not None else np.full(10, np.nan)
    return dict(mask=mask, quality=q, features=values)
