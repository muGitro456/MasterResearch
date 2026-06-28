import numpy as np
import pytest
from archive import Archive


def _make_arc_k2(na_max=10):
    """K=2 の非優越解2点を持つアーカイブを返す"""
    pos = np.array([[0.0, 0.0], [1.0, 1.0]])
    fit = np.array([[0.0, 1.0], [1.0, 0.0]])
    return Archive(pos, fit, NA_MAX=na_max, D=2, K=2)


def _make_arc_k3():
    """K=3 の非優越解3点を持つアーカイブを返す"""
    pos = np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
    fit = np.array([[0.0, 1.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 0.0]])
    return Archive(pos, fit, NA_MAX=10, D=2, K=3)


class TestArchiveMakeParetoFront:
    def test_normal_k2(self):
        arc = _make_arc_k2()
        assert arc.fit_gb.shape == (2, 2)

    def test_normal_k3(self):
        arc = _make_arc_k3()
        assert arc.fit_gb.shape == (3, 3)

    def test_normal_exceeds_na_max(self):
        # 5非優越解、NA_MAX=3 → 混雑距離トリミングで3以下になる
        pos = np.array([[float(i), 0.0] for i in range(5)])
        fit = np.array([[float(i), float(4 - i)] for i in range(5)])
        arc = Archive(pos, fit, NA_MAX=3, D=2, K=2)
        assert arc.fit_gb.shape[0] <= 3

    def test_normal_k3_exceeds_na_max(self):
        # K=3 かつ非優越解3点、NA_MAX=2 → lines 48-49 (vstack branch) を通過する
        pos = np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
        fit = np.array([[0.0, 1.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 0.0]])
        arc = Archive(pos, fit, NA_MAX=2, D=2, K=3)
        assert arc.fit_gb.shape[0] <= 2


class TestArchiveUpdateArchive:
    def test_normal_does_not_update(self):
        # 既知バグ: update_archive は make_pareto_front の戻り値を代入しないため
        # fit_gb は呼び出し前後で変化しない
        arc = _make_arc_k2()
        original = arc.fit_gb.copy()
        arc.update_archive(
            np.array([[0.5, 0.5]]),
            np.array([[0.5, 0.5]])
        )
        np.testing.assert_array_equal(arc.fit_gb, original)


class TestArchiveSelectLeader:
    def test_normal_single(self):
        pos = np.array([[1.0, 0.0]])
        fit = np.array([[0.5, 0.5]])
        arc = Archive(pos, fit, NA_MAX=10, D=2, K=2)
        leader = arc.select_leader()
        np.testing.assert_array_equal(leader, arc.pos_gb[0])

    def test_normal_two(self):
        np.random.seed(42)
        arc = _make_arc_k2()
        leader = arc.select_leader()
        assert leader.shape == (2,)

    def test_normal_multiple(self):
        np.random.seed(42)
        pos = np.array([[float(i), 0.0] for i in range(4)])
        fit = np.array([[float(i), float(3 - i)] for i in range(4)])
        arc = Archive(pos, fit, NA_MAX=10, D=2, K=2)
        leader = arc.select_leader()
        assert leader.shape == (2,)


class TestArchiveCalcCrowdingDistance:
    def test_normal_na1(self):
        pos = np.array([[1.0, 0.0]])
        fit = np.array([[0.5, 0.5]])
        arc = Archive(pos, fit, NA_MAX=10, D=2, K=2)
        cd = arc.calc_crowding_distance()
        assert len(cd) == 1
        assert cd[0] == 1

    def test_normal_na2(self):
        arc = _make_arc_k2()
        cd = arc.calc_crowding_distance()
        assert len(cd) == 2
        assert cd[0] == cd[-1]

    def test_normal_na3(self):
        pos = np.array([[float(i), 0.0] for i in range(3)])
        fit = np.array([[float(i), float(2 - i)] for i in range(3)])
        arc = Archive(pos, fit, NA_MAX=10, D=2, K=2)
        cd = arc.calc_crowding_distance()
        assert len(cd) == 3
        assert cd[0] == cd[-1]

    def test_normal_na4(self):
        pos = np.array([[float(i), 0.0] for i in range(4)])
        fit = np.array([[float(i), float(3 - i)] for i in range(4)])
        arc = Archive(pos, fit, NA_MAX=10, D=2, K=2)
        cd = arc.calc_crowding_distance()
        assert len(cd) == 4
        assert cd[0] == cd[-1]


class TestArchiveCalcCoverRate:
    def test_normal_k2(self):
        arc = _make_arc_k2()
        cr = arc.calc_cover_rate(divNum=2)
        assert isinstance(cr, float)
        assert 0.0 <= cr <= 1.0

    def test_normal_k3(self):
        arc = _make_arc_k3()
        cr = arc.calc_cover_rate(divNum=2)
        assert isinstance(cr, float)
        assert 0.0 <= cr <= 1.0


class TestArchiveUnionArchive:
    def test_normal(self):
        arc = _make_arc_k2()
        pos1 = np.array([[0.0, 0.0]])
        fit1 = np.array([[0.0, 1.0]])
        pos2 = np.array([[1.0, 1.0]])
        fit2 = np.array([[1.0, 0.0]])
        pos_c, fit_c = arc.union_archive(pos1, fit1, pos2, fit2)
        assert pos_c.shape == (2, 2)
        assert fit_c.shape == (2, 2)
