import numpy as np
from scipy.stats import rankdata
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score, roc_curve


def metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    fpr, tpr, _ = roc_curve(y, p)
    ece = 0.0
    bins = np.minimum((p * 10).astype(int), 9)
    for i in range(10):
        use = bins == i
        if use.any():
            ece += use.mean() * abs(y[use].mean() - p[use].mean())
    return dict(auroc=float(roc_auc_score(y, p)), auprc=float(average_precision_score(y, p)),
                sensitivity_at_90_specificity=float(tpr[fpr <= 0.1].max()),
                specificity_at_90_sensitivity=float(1 - fpr[tpr >= 0.9].min()),
                brier=float(brier_score_loss(y, p)), ece=float(ece))


def bootstrap(y: np.ndarray, p: np.ndarray, groups: np.ndarray, count: int = 2000, seed: int = 20261031) -> dict:
    rng = np.random.default_rng(seed)
    unique = np.unique(groups)
    indices = [np.flatnonzero(groups == g) for g in unique]
    values = []
    for _ in range(count):
        ix = np.concatenate([indices[i] for i in rng.integers(0, len(unique), len(unique))])
        if len(np.unique(y[ix])) == 2:
            values.append(metrics(y[ix], p[ix]))
    result = metrics(y, p)
    return {name: dict(value=value, low=float(np.quantile([v[name] for v in values], 0.025)),
                       high=float(np.quantile([v[name] for v in values], 0.975)))
            for name, value in result.items()}


def auc_interval(y: np.ndarray, p: np.ndarray, groups: np.ndarray, count: int = 2000, seed: int = 20261031) -> dict:
    rng = np.random.default_rng(seed)
    indices = [np.flatnonzero(groups == g) for g in np.unique(groups)]
    values = []
    for _ in range(count):
        ix = np.concatenate([indices[i] for i in rng.integers(0, len(indices), len(indices))])
        labels = y[ix]
        n1 = labels.sum()
        n0 = len(labels) - n1
        if n0 and n1:
            rank = rankdata(p[ix])
            values.append((rank[labels == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
    return dict(value=float(roc_auc_score(y, p)), low=float(np.quantile(values, .025)),
                high=float(np.quantile(values, .975)))
