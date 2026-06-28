import numpy as np
import pytest
from field import SearchSpace, Problem
from agent import Swarm
from agent_subs import SubSwarm, Neighborhood_C
from topology import Topology


@pytest.fixture
def field(param_dict, zdt2_dict):
    return SearchSpace(param_dict, Problem(zdt2_dict))


@pytest.fixture
def swarm(field):
    np.random.seed(42)
    return Swarm(10, field)


@pytest.fixture
def sub_swarms(swarm, field):
    # N=10, N_SUB_SWARM=2 → N_SUB_PARTICLE=5
    subs = [SubSwarm(5, swarm, i, field) for i in range(2)]
    return subs


class TestSubSwarm:
    def test_normal_init(self, swarm, field):
        sub = SubSwarm(5, swarm, index=0, field=field)
        assert sub.POS.shape == (5, field.D)
        assert sub.VEL.shape == (5, field.D)
        assert sub.FIT.shape == (5, field.K)
        assert sub.POS_PB.shape == (5, field.D)

    def test_normal_update_vel(self, swarm, field):
        sub = SubSwarm(5, swarm, index=0, field=field)
        leader = np.zeros(field.D)
        sub.update_vel(leader, field, gen=1)
        assert sub.VEL.shape == (5, field.D)

    def test_normal_update_pos(self, swarm, field):
        sub = SubSwarm(5, swarm, index=0, field=field)
        sub.update_pos(field)
        assert sub.POS.shape == (5, field.D)

    def test_normal_update_pb_all_better(self, swarm, field):
        sub = SubSwarm(5, swarm, index=0, field=field)
        sub.FIT = np.zeros((5, field.K))
        sub.FIT_PB = np.ones((5, field.K))
        sub.POS_PB = np.full((5, field.D), 999.0)  # sentinel: distinguishable from POS
        original = sub.POS_PB.copy()
        sub.update_pb()
        assert not np.allclose(sub.POS_PB, original)

    def test_normal_update_pb_partial(self, swarm, field):
        np.random.seed(0)
        sub = SubSwarm(1, swarm, index=0, field=field)
        sub.N_SUB_PARTICLE = 1
        sub.POS = sub.POS[:1]
        sub.FIT = np.array([[0.0, 1.5]])
        sub.FIT_PB = np.array([[1.0, 1.0]])
        sub.POS_PB = np.full((1, field.D), 999.0)  # sentinel: distinguishable from POS
        old_pb = sub.POS_PB.copy()
        sub.update_pb()
        assert not np.allclose(sub.POS_PB, old_pb)


class TestNeighborhoodC:
    def test_normal_init(self, sub_swarms, field):
        topo = Topology(N=2, N_SIZE=5, name="Ring_5")
        nc = Neighborhood_C(sub_swarms, index=0, field=field, my_topology=topo)
        assert nc.N_SIZE == 5
        assert nc.N_SUB_PARTICLE == 5

    def test_normal_explore(self, sub_swarms, field):
        np.random.seed(42)
        topo = Topology(N=2, N_SIZE=5, name="Ring_5")
        nc = Neighborhood_C(sub_swarms, index=0, field=field, my_topology=topo)
        leader = np.zeros(field.D)
        lbest = np.zeros(field.D)
        pos, fit = nc.explore(generation=1, leader=leader, LBEST=lbest)
        assert pos.shape[1] == field.D
