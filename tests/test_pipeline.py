import json

import numpy as np
import pytest
from sklearn.model_selection import StratifiedGroupKFold

from lidcheck.features import analyze
from lidcheck.io import ROOT
from lidcheck.models import fit, serialize
from lidcheck.normalize import normalize
from lidcheck.quality import failures
from lidcheck.segmentation import linear


@pytest.mark.parametrize("name", ["eye", "dark", "noise"])
def test_shared_fixtures(name: str) -> None:
    fixture = json.loads((ROOT / f"tests/parity/{name}.json").read_text())
    rgb = np.array(fixture["rgb"], dtype=np.uint8).reshape(fixture["size"], fixture["size"], 3)
    for method, expected in fixture["expected"].items():
        out = analyze(rgb, method)
        np.testing.assert_array_equal(out["mask"].astype(int).ravel(), expected["mask"])
        np.testing.assert_allclose(
            list(out["quality"].values()), list(expected["quality"].values()), atol=1e-8
        )
        np.testing.assert_allclose(
            out["features"], np.array(expected["features"], dtype=float), atol=1e-3, equal_nan=True
        )
        normalized = normalize(linear(rgb), method)
        if expected["normalized"] is None:
            assert normalized is None
        else:
            np.testing.assert_allclose(normalized.reshape(-1, 3), expected["normalized"], atol=1e-8)


def test_grouped_calibrated_export() -> None:
    rng = np.random.default_rng(4)
    groups = np.repeat(np.arange(80), 2)
    x = rng.normal(size=(160, 10))
    y = np.repeat(np.arange(80) % 2, 2)
    for train, test in StratifiedGroupKFold(5).split(x, y, groups):
        assert not set(groups[train]) & set(groups[test])
    model = fit(x, y, groups, 3)
    obj = serialize(model)
    z = ((x - obj["mean"]) / obj["scale"]) @ obj["coefficients"] + obj["intercept"]
    p = 1 / (1 + np.exp(-(z * obj["platt_coefficient"] + obj["platt_intercept"])))
    np.testing.assert_allclose(p, model.predict(x))


def test_missing_references_never_fall_back() -> None:
    assert normalize(np.ones((32, 32, 3)) * 0.5, "sclera", False) is None
    assert normalize(np.zeros((32, 32, 3)), "skin") is None


def test_dark_photo_rejected() -> None:
    from lidcheck.benchmark import config

    result = analyze(np.zeros((32, 32, 3), dtype=np.uint8))
    assert "eyelid" in failures(result["quality"], config()["quality"])
