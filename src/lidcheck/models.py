from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


@dataclass
class Model:
    base: object
    calibration: LogisticRegression
    threshold: float
    band: float

    def predict(self, x: np.ndarray) -> np.ndarray:
        return self.calibration.predict_proba(self.base.decision_function(x).reshape(-1, 1))[:, 1]


def fit(x: np.ndarray, y: np.ndarray, groups: np.ndarray, seed: int) -> Model:
    splits = list(StratifiedGroupKFold(3, shuffle=True, random_state=seed).split(x, y, groups))
    candidates = []
    for c in [0.1, 1.0, 10.0]:
        score = np.zeros(len(y))
        for train, test in splits:
            model = make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=2000))
            model.fit(x[train], y[train])
            score[test] = model.decision_function(x[test])
        candidates.append((roc_auc_score(y, score), c, score))
    _, c, score = max(candidates, key=lambda item: item[0])
    calibration = LogisticRegression(C=1.0, max_iter=2000).fit(score.reshape(-1, 1), y)
    p = calibration.predict_proba(score.reshape(-1, 1))[:, 1]
    _, tpr, thresholds = roc_curve(y, p)
    threshold = float(thresholds[np.flatnonzero(tpr >= 0.9)[0]])
    choices = []
    for band in [0.0, 0.05, 0.1, 0.15]:
        keep = abs(p - threshold) >= band
        if keep.mean() >= 0.5:
            choices.append((np.mean((p[keep] >= threshold) != y[keep]), band))
    band = float(min(choices)[1])
    base = make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=2000)).fit(x, y)
    return Model(base, calibration, threshold, band)


def serialize(model: Model) -> dict:
    scaler, lr = model.base.steps[0][1], model.base.steps[1][1]
    return dict(
        mean=scaler.mean_.tolist(),
        scale=scaler.scale_.tolist(),
        coefficients=lr.coef_[0].tolist(),
        intercept=float(lr.intercept_[0]),
        platt_coefficient=float(model.calibration.coef_[0, 0]),
        platt_intercept=float(model.calibration.intercept_[0]),
        threshold=model.threshold,
        band=model.band,
    )
