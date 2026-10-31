import numpy as np
from lidcheck.consistency import icc


def test_identical_repeated_subject_measurements() -> None:
    matrix=np.repeat(np.array([.1,.3,.7,.9])[:,None],6,axis=1)
    assert abs(icc(matrix)-1)<1e-10


def test_icc_needs_multiple_people() -> None:
    assert icc(np.ones((1,6))) is None
