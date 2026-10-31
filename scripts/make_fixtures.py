import numpy as np
from PIL import Image

from lidcheck.features import analyze
from lidcheck.io import ROOT, write_json
from lidcheck.normalize import METHODS, normalize
from lidcheck.segmentation import linear


def run() -> None:
    folder = ROOT / "tests/parity"
    folder.mkdir(parents=True, exist_ok=True)
    yy, xx = np.indices((32, 32))
    base = np.full((32, 32, 3), [110, 105, 100], dtype=np.uint8)
    base[((xx - 16) / 12) ** 2 + ((yy - 20) / 5) ** 2 < 1] = [190, 90, 105]
    base[3:12, 5:28] = [205, 210, 215]
    base[15, 10:15] = [255, 255, 255]
    rng = np.random.default_rng(2)
    images = {
        "eye": base,
        "dark": np.zeros_like(base),
        "noise": rng.integers(0, 256, base.shape, dtype=np.uint8),
    }
    for name, rgb in images.items():
        result = {}
        for method in METHODS:
            a = analyze(rgb, method)
            x = normalize(linear(rgb), method)
            result[method] = {
                "mask": a["mask"].astype(int).ravel().tolist(),
                "quality": a["quality"],
                "features": [float(v) if np.isfinite(v) else None for v in a["features"]],
                "normalized": x.reshape(-1, 3).tolist() if x is not None else None,
            }
        write_json(
            folder / f"{name}.json",
            {"size": 32, "rgb": rgb.reshape(-1, 3).tolist(), "expected": result},
        )
    Image.fromarray(base).resize((320, 320), Image.Resampling.NEAREST).save(
        folder / "synthetic.png"
    )


if __name__ == "__main__":
    run()
