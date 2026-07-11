import numpy as np
from field import Problem
from archive import Archive
from related import MOPSO, FPOMOPSO, SENIOR


class TestMOPSOSimulation:
    def test_normal_returns_archive(self, param_dict, zdt2_dict):
        np.random.seed(42)
        problem = Problem(zdt2_dict)
        algo = MOPSO(param_dict, problem)
        result = algo.simulation()
        assert isinstance(result, Archive)


class TestFPOMOPSOSimulation:
    def test_normal_returns_archive(self, param_dict, zdt2_dict):
        np.random.seed(42)
        problem = Problem(zdt2_dict)
        algo = FPOMOPSO(param_dict, problem)
        result = algo.simulation()
        assert isinstance(result, Archive)


class TestSENIORSimulation:
    def test_normal_returns_archive(self, param_dict, zdt2_dict):
        np.random.seed(42)
        problem = Problem(zdt2_dict)
        algo = SENIOR(param_dict, problem)
        result = algo.simulation()
        assert isinstance(result, Archive)
