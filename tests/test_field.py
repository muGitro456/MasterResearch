import numpy as np
import pytest
from masterresearch.src.field import SearchSpace, Problem


@pytest.fixture
def zdt2_field(param_dict, zdt2_dict):
    problem = Problem(zdt2_dict)
    return SearchSpace(param_dict, problem)


class TestSearchSpaceUpdateFit:
    def test_normal_returns_n_k_shape(self, zdt2_field):
        N, D = 5, 3
        pos = np.random.rand(N, D)
        fit = zdt2_field.update_fit(pos)
        assert fit.shape == (N, 2)


class TestSearchSpaceCheckBoundaries:
    def test_normal_in_range(self, zdt2_field):
        pos = np.array([[0.5, 0.5, 0.5], [0.3, 0.7, 0.2]])
        vel = np.zeros_like(pos)
        pos_new, vel_new = zdt2_field.check_boundaries(pos, vel)
        assert pos_new.shape == pos.shape
        assert np.all(pos_new >= 0.0) and np.all(pos_new <= 1.0)

    def test_normal_out_of_range(self, zdt2_field):
        pos = np.array([[1.5, -0.1, 0.5]])
        vel = np.zeros_like(pos)
        pos_new, vel_new = zdt2_field.check_boundaries(pos, vel)
        assert np.all(pos_new >= 0.0) and np.all(pos_new <= 1.0)


class TestSearchSpaceSpeedmeter:
    def test_normal_clamps_velocity(self, zdt2_field):
        vel = np.ones((3, 3)) * 999.0
        vel_new = zdt2_field.speedmeter(vel, gen=1)
        vmax = zdt2_field.VMAX(1)
        assert np.all(vel_new <= vmax)
        assert vel_new.shape == (3, 3)


class TestProblemInit:
    def test_normal_zdt2(self, zdt2_dict):
        p = Problem(zdt2_dict)
        assert p.K == 2
        assert p.D == 3
        assert np.all(p.upper == 1.0)
        assert np.all(p.lower == 0.0)

    def test_normal_zdt6(self):
        d = {"name": "ZDT6", "dimension": 3, "upper": 1.0, "lower": 0.0}
        p = Problem(d)
        assert p.K == 2
        assert p.D == 3

    def test_normal_dtlz1(self, dtlz1_dict):
        p = Problem(dtlz1_dict)
        assert p.K == 3
        assert p.D == 3

    def test_normal_rastrigin(self):
        d = {"name": "Rastrigin", "dimension": 2, "upper": 5.12, "lower": -5.12}
        p = Problem(d)
        assert p.K == 2

    def test_normal_ackley(self):
        d = {"name": "Ackley", "dimension": 2, "upper": 32.768, "lower": -32.768}
        p = Problem(d)
        assert p.K == 2

    def test_normal_griewank(self):
        d = {"name": "Griewank", "dimension": 2, "upper": 600.0, "lower": -600.0}
        p = Problem(d)
        assert p.K == 2

    def test_normal_sphere(self):
        d = {"name": "Sphere", "dimension": 2, "upper": 5.0, "lower": -5.0}
        p = Problem(d)
        assert p.K == 2

    def test_normal_booth(self):
        d = {"name": "Booth", "dimension": 2, "upper": 10.0, "lower": -10.0}
        p = Problem(d)
        assert p.K == 2

    def test_normal_alpine(self):
        d = {"name": "Alpine", "dimension": 2, "upper": 10.0, "lower": -10.0}
        p = Problem(d)
        assert p.K == 2

    def test_abnormal_unknown_function(self):
        d = {"name": "Unknown", "dimension": 2, "upper": 1.0, "lower": 0.0}
        with pytest.raises(ValueError, match="Unknown function"):
            Problem(d)
