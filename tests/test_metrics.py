import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from metrics import cover_rate


def test_cover_rate_full_coverage():
    # パレートフロント上の2点が各分割区間を完全にカバーする場合
    arc = np.array([[0.0, 1.0], [1.0, 0.0]])
    assert cover_rate(arc, divNum=2) == 1.0


def test_cover_rate_partial_coverage():
    # 2点が4分割のうち2区間にしか存在しない場合 → 被覆率0.5
    arc = np.array([[0.0, 1.0], [0.1, 0.9]])
    result = cover_rate(arc, divNum=4)
    assert result == 0.5


def test_cover_rate_returns_float():
    arc = np.array([[0.0, 1.0], [1.0, 0.0]])
    result = cover_rate(arc, divNum=2)
    assert isinstance(result, float)
