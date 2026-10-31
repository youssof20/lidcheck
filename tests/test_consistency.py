import numpy as np
from lidcheck.consistency import icc


def test_identical_repeated_subject_measurements() -> None:
    matrix = np.repeat(np.array([0.1, 0.3, 0.7, 0.9])[:, None], 6, axis=1)
    assert abs(icc(matrix) - 1) < 1e-10


def test_icc_needs_multiple_people() -> None:
    assert icc(np.ones((1, 6))) is None


def test_dummy_study_end_to_end(tmp_path, monkeypatch) -> None:
    import json
    import lidcheck.consistency as study
    import lidcheck.plotting as plotting

    monkeypatch.setattr(study, "ROOT", tmp_path)
    monkeypatch.setattr(plotting, "ROOT", tmp_path)
    records = []
    for participant in range(4):
        for condition in range(6):
            for shot in [1, 2]:
                score = 0.15 + 0.15 * participant + 0.003 * condition + 0.001 * shot
                measurement = {
                    "features": [score] * 10,
                    "score": score,
                    "rejected": False,
                    "synthetic_drift": 0.03 + 0.001 * participant,
                }
                records.append(
                    {
                        "participant": f"D{participant}",
                        "condition": condition,
                        "shot": shot,
                        "synthetic": False,
                        "measurements": {"none": measurement, "gray_world": measurement},
                    }
                )
    path = tmp_path / "dummy.json"
    path.write_text(json.dumps({"entries": records}))
    study.run(path)
    result = json.loads((tmp_path / "results/consistency.json").read_text())
    assert result["methods"]["none"]["complete_participants"] == 4
    assert result["methods"]["none"]["icc"] > 0.9
    assert (tmp_path / "results/figures/real_lighting_consistency.png").exists()
