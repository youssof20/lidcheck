import numpy as np

from lidcheck.segmentation import lab

METHODS = ["none", "chromaticity", "gray_world", "white_patch", "sclera", "skin"]


def normalize(x: np.ndarray, method: str, references: bool = True) -> np.ndarray | None:
    if method == "none":
        return x.copy()
    if method == "chromaticity":
        return x / np.maximum(x.sum(axis=-1, keepdims=True), 1e-8)
    if method == "gray_world":
        ref = x.mean(axis=(0, 1))
        return np.clip(x * ref.mean() / np.maximum(ref, 1e-8), 0, 1)
    if method == "white_patch":
        ref = np.quantile(x, 0.95, axis=(0, 1))
    elif method in ["sclera", "skin"]:
        if not references:
            return None
        colors = lab(x)
        l, a, b = (colors[..., i] for i in range(3))
        if method == "sclera":
            region = (l > 65) & (l < 95) & (abs(a) < 8) & (abs(b) < 15)
        else:
            h, w = l.shape
            yy, xx = np.indices((h, w))
            border = (yy < h * 0.2) | (yy >= h * 0.8) | (xx < w * 0.2) | (xx >= w * 0.8)
            region = border & (l > 30) & (l < 85) & (a > 3) & (a < 20) & (b > 8) & (b < 35)
        if region.sum() < x.shape[0] * x.shape[1] * 0.01:
            return None
        ref = np.median(x[region], axis=0)
    else:
        raise ValueError(method)
    return np.clip(x / np.maximum(ref, 1e-8), 0, 1)
