import numpy as np
from masterresearch.src.field import Problem
from masterresearch.src.archive import Archive
from masterresearch.src.proposed import MASTER_A, MASTER_B, MASTER_C


class TestMASTERASimulation:
    def test_normal_returns_archive(self, param_dict, zdt2_dict, ring5_topo_dict):
        np.random.seed(42)
        problem = Problem(zdt2_dict)
        algo = MASTER_A(param_dict, problem, ring5_topo_dict)
        result = algo.simulation()
        assert isinstance(result, Archive)


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

    def test_normal_grid_topology_with_corner_subswarm_does_not_crash(self, zdt2_dict):
        # Gridトポロジーは角・辺のサブ粒子群で近傍が5個未満になるため、
        # 固定長(5個)決め打ちのインデックスアクセスだとIndexErrorになってはいけない。
        np.random.seed(42)
        param_dict = {
            "N": 18, "N_ARCHIVE_MAX": 10, "GENERATION_MAX": 1,
            "INERTIA": 0.7, "SELF_AWARENESS": 1.5, "SOCIAL_AWARENESS": 1.5,
            "RIVAL_AWARENESS": 1.5, "INERTIA_INITIAL": 0.9, "INERTIA_END": 0.4,
            "SELF_AWARENESS_OF_PREDATOR": 1.0, "LOCAL_AWARENESS": 0.5,
            "VMAX_INITIAL": 5.0, "VMAX_END": 10.0, "DAMP": 0.5,
            "N_SUB_SWARM": 9,  # 3x3のGridで角のサブ粒子群(近傍3個)を含む
        }
        grid_topo_dict = {"name": "Grid", "N_SIZE": 5}
        problem = Problem(zdt2_dict)
        algo = MASTER_C(param_dict, problem, grid_topo_dict)
        result = algo.simulation()
        assert isinstance(result, Archive)
