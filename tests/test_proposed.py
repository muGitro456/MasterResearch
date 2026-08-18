import numpy as np
from src.field import Problem
from src.archive import Archive
from src.proposed import MASTER_A, MASTER_B, MASTER_C


class TestMASTERASimulation:
    def test_normal_returns_archive(self, param_dict, zdt2_dict, ring5_topo_dict):
        np.random.seed(42)
        problem = Problem(zdt2_dict)
        algo = MASTER_A(param_dict, problem, ring5_topo_dict)
        result = algo.simulation()
        assert isinstance(result, Archive)


class TestMASTERAUnionNeighbors:
    def test_normal_returns_2d_arrays(self, param_dict, zdt2_dict, ring5_topo_dict):
        np.random.seed(42)
        problem = Problem(zdt2_dict)
        algo = MASTER_A(param_dict, problem, ring5_topo_dict)
        pos, fit = algo.union_neighbors(algo.sub_arc_MOPSO, index=0, topology=algo.my_topology)
        assert pos.ndim == 2
        assert fit.ndim == 2


class TestMASTERBSimulation:
    def test_normal_returns_archive(self, param_dict, zdt2_dict, ring5_topo_dict):
        np.random.seed(42)
        problem = Problem(zdt2_dict)
        algo = MASTER_B(param_dict, problem, ring5_topo_dict)
        result = algo.simulation()
        assert isinstance(result, Archive)


class TestMASTERCSimulation:
    def test_normal_returns_archive(self, master_c_param_dict, zdt2_dict, ring5_topo_dict):
        np.random.seed(42)
        problem = Problem(zdt2_dict)
        algo = MASTER_C(master_c_param_dict, problem, ring5_topo_dict)
        result = algo.simulation()
        assert isinstance(result, Archive)
