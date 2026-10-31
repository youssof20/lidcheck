import numpy as np

from lidcheck.segmentation import linear


def measure(rgb: np.ndarray, mask: np.ndarray, cohesion: float) -> dict[str, float]:
    lum = linear(rgb) @ np.array([0.2126, 0.7152, 0.0722])
    lap = -4 * lum[1:-1, 1:-1] + lum[:-2, 1:-1] + lum[2:, 1:-1] + lum[1:-1, :-2] + lum[1:-1, 2:]
    interior = mask[1:-1, 1:-1]
    roi = rgb[mask]
    return dict(area=float(mask.mean()), cohesion=cohesion,
                blur=float(np.var(lap[interior])) if interior.any() else 0.0,
                clipped=float(((roi.min(axis=1) <= 5) | (roi.max(axis=1) >= 250)).mean()) if len(roi) else 1.0,
                glare=float((rgb.min(axis=-1) >= 245).mean()))


def failures(q: dict, limits: dict) -> list[str]:
    failed = []
    if q["area"] < limits["min_area"] or q["area"] > limits["max_area"]:
        failed.append("eyelid")
    if q["blur"] < limits["min_blur"]:
        failed.append("blur")
    if q["clipped"] > limits["max_clipped"]:
        failed.append("exposure")
    if q["glare"] > limits["max_glare"]:
        failed.append("glare")
    if q["cohesion"] < limits["min_cohesion"]:
        failed.append("cohesion")
    return failed
