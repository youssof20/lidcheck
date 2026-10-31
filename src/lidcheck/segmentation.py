import numpy as np
from scipy import ndimage


def linear(rgb: np.ndarray) -> np.ndarray:
    x = np.asarray(rgb, dtype=float) / 255.0
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def srgb(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0, 1)
    return np.rint(255 * np.where(x <= 0.0031308, x * 12.92,
                                 1.055 * x ** (1 / 2.4) - 0.055)).astype(np.uint8)


def lab(x: np.ndarray) -> np.ndarray:
    xyz = x @ np.array([[0.4124564, 0.3575761, 0.1804375],
                        [0.2126729, 0.7151522, 0.0721750],
                        [0.0193339, 0.1191920, 0.9503041]]).T
    xyz /= np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])], axis=-1)


def segment(rgb: np.ndarray) -> tuple[np.ndarray, float]:
    color = lab(linear(rgb))
    candidate = ((color[..., 1] > 12) & (color[..., 0] > 20) & (color[..., 0] < 90)
                 & ~(rgb.min(axis=-1) >= 245) & (rgb.max(axis=-1) > 30))
    structure = np.ones((3, 3), dtype=bool)
    cleaned = ndimage.binary_opening(candidate, structure)
    cleaned = ndimage.binary_closing(cleaned, structure)
    labels, n = ndimage.label(cleaned)
    if n == 0:
        return np.zeros(candidate.shape, dtype=bool), 0.0
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    mask = labels == np.argmax(sizes)
    return mask, float(mask.sum() / max(cleaned.sum(), 1))
