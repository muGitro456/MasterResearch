import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from metrics import cover_rate
import metrics


def test_normal_full_coverage():
    arc = np.array([[0.0, 1.0], [1.0, 0.0]])
    assert cover_rate(arc, divNum=2) == 1.0


def test_normal_partial_coverage():
    arc = np.array([[0.0, 1.0], [0.1, 0.9]])
    result = cover_rate(arc, divNum=4)
    assert result == 0.5


def test_normal_returns_float():
    arc = np.array([[0.0, 1.0], [1.0, 0.0]])
    result = cover_rate(arc, divNum=2)
    assert isinstance(result, float)


class TestMetricsDisplay:
    def test_normal(self, capsys):
        pfs = ['a.csv', 'b.csv', 'c.csv']
        idx = np.array([0.5, 0.8, 0.3])
        metrics.display(pfs, idx)
        captured = capsys.readouterr()
        assert "Average" in captured.out
        assert "Maximum" in captured.out


class TestMetricsEvaluation:
    def test_normal_with_indicators(self, mocker, capsys):
        mocker.patch('glob.glob', return_value=['f1.csv', 'f2.csv', 'f3.csv'])
        num_sols = np.array([5.0, 4.0, 6.0])
        cr = np.array([0.8, 0.7, 0.9])
        metrics.evaluation("dummy_dir", num_sols, cr)
        captured = capsys.readouterr()
        assert "COVER RATE" in captured.out

    def test_normal_without_indicators(self, mocker, capsys):
        mock_df = mocker.Mock()
        mock_df.values = np.array([[0.0, 1.0], [1.0, 0.0]])
        mocker.patch('glob.glob', return_value=['f1.csv', 'f2.csv'])
        mocker.patch('pandas.read_csv', return_value=mock_df)
        metrics.evaluation("dummy_dir")
        captured = capsys.readouterr()
        assert "COVER RATE" in captured.out


class TestMetricsRni:
    def test_normal(self, mocker):
        mock_df1 = mocker.Mock()
        mock_df1.values = np.array([[0.0, 1.0], [0.5, 0.5], [1.0, 0.0]])
        mock_df2 = mocker.Mock()
        mock_df2.values = np.array([[0.2, 0.8], [0.8, 0.2]])
        mocker.patch('pandas.read_csv', side_effect=[mock_df1, mock_df2])
        result = metrics.rni('f1.csv', 'f2.csv')
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert abs(result[0] + result[1] - 1.0) < 1e-9
