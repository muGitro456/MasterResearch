import numpy as np
from masterresearch.src.archive import Archive


def _make_arc_k2(na_max=10):
    pos = np.array([[0.0, 0.0], [1.0, 1.0]])
    fit = np.array([[0.0, 1.0], [1.0, 0.0]])
    return Archive(pos, fit, NA_MAX=na_max, D=2, K=2)


def _make_arc_k3():
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
        pos = np.array([[float(i), 0.0] for i in range(5)])
        fit = np.array([[float(i), float(4 - i)] for i in range(5)])
        arc = Archive(pos, fit, NA_MAX=3, D=2, K=2)
        assert arc.fit_gb.shape[0] <= 3

    def test_normal_k3_exceeds_na_max(self):
        pos = np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
        fit = np.array([[0.0, 1.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 0.0]])
        arc = Archive(pos, fit, NA_MAX=2, D=2, K=3)
        assert arc.fit_gb.shape[0] <= 2


class TestArchiveUpdateArchive:
    def test_normal_does_not_update(self):
        arc = _make_arc_k2()
        original = arc.fit_gb.copy()
        arc.update_archive(
            np.array([[2.0, 2.0]]),
            np.array([[2.0, 2.0]])
        )
        np.testing.assert_array_equal(arc.fit_gb, original)

    def test_normal_updates_when_dominated_solution_added(self):
        # f1=0.0, f2=1.0 のみを持つアーカイブを作成
        pos = np.array([[0.0, 0.0]])
        fit = np.array([[0.0, 1.0]])
        arc = Archive(pos, fit, NA_MAX=10, D=2, K=2)

        # f1=1.0, f2=0.0 を追加するとパレートフロントが更新されるはず
        arc.update_archive(
            np.array([[1.0, 1.0]]),
            np.array([[1.0, 0.0]])
        )
        # 2点がパレートフロントに存在するはず
        assert arc.fit_gb.shape[0] == 2


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

    def test_na5_boundary_distance_uses_all_interior_points(self):
        # 境界解(cd[0], cd[-1])は「内側の全ての点」の混雑度の最大値であるべき
        # (NSGA-IIの境界解=最大混雑度扱いという定義)。
        # 末尾から2点を除外すると、最大値を持つ内側の点(index=3)が
        # 計算から漏れてしまう。
        pos = np.array([[0.0, 0.0]] * 5)
        fit_gb = np.array([[0, 10], [1, 9.5], [2, 9], [3, 1], [4, 0]], dtype=float)
        arc = Archive(pos, fit_gb, NA_MAX=10, D=2, K=2)
        cd = arc.calc_crowding_distance(fit_gb)
        assert cd[0] == 11
        assert cd[-1] == 11


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
    def test_normal_combines_arrays(self):
        arc = _make_arc_k2()
        pos1 = np.array([[0.0, 0.0]])
        fit1 = np.array([[0.0, 1.0]])
        pos2 = np.array([[1.0, 1.0]])
        fit2 = np.array([[1.0, 0.0]])
        pos_c, fit_c = arc.union_archive(pos1, fit1, pos2, fit2)
        assert pos_c.shape == (2, 2)
        assert fit_c.shape == (2, 2)
