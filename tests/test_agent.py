import copy
import numpy as np
import pytest
from src.field import SearchSpace, Problem
from src.agent import Swarm, Predators, PredatorsSenior, Neighborhood
from src.topology import Topology


@pytest.fixture
def field(param_dict, zdt2_dict):
    return SearchSpace(param_dict, Problem(zdt2_dict))


@pytest.fixture
def swarm(field):
    np.random.seed(42)
    return Swarm(5, field)


class TestSwarm:
    def test_normal_init(self, swarm, field):
        assert swarm.POS.shape == (5, field.D)
        assert swarm.VEL.shape == (5, field.D)
        assert swarm.FIT.shape == (5, field.K)
        assert swarm.POS_PB.shape == (5, field.D)

    def test_normal_explore(self, swarm, field):
        np.random.seed(42)
        leader = swarm.POS[0]
        pos, fit = swarm.explore(generation=1, leader=leader)
        assert pos.shape == (5, field.D)
        assert fit.shape == (5, field.K)

    def test_normal_update_pb_all_better(self, swarm):
        swarm.FIT = np.zeros((5, 2))
        swarm.FIT_PB = np.ones((5, 2))
        swarm.POS_PB = np.full((5, swarm.my_field.D), 999.0)
        original_pos_pb = copy.deepcopy(swarm.POS_PB)
        swarm.update_pb()
        assert not np.allclose(swarm.POS_PB, original_pos_pb)

    def test_normal_update_pb_partial(self, swarm):
        np.random.seed(0)
        swarm.N = 1
        swarm.POS = swarm.POS[:1]
        swarm.VEL = swarm.VEL[:1]
        swarm.FIT = np.array([[0.0, 1.5]])
        swarm.FIT_PB = np.array([[1.0, 1.0]])
        swarm.POS_PB = np.full((1, swarm.my_field.D), 999.0)
        old_pb = swarm.POS_PB.copy()
        swarm.update_pb()
        assert not np.allclose(swarm.POS_PB, old_pb)


class TestPredators:
    @pytest.fixture
    def predators(self, field):
        np.random.seed(42)
        return Predators(5, field)

    def test_normal_init(self, predators, field):
        assert predators.RIVALS.shape == (5, field.D)

    def test_normal_explore(self, predators, field):
        np.random.seed(42)
        pos, fit = predators.explore(generation=1)
        assert pos.shape == (5, field.D)

    def test_normal_calc_fit_predator(self, predators):
        fp = predators.calc_fit_predator()
        assert fp.shape == (5,)
        assert np.all(fp > 0)

    def test_normal_update_rivals(self, predators):
        np.random.seed(42)
        predators.update_rivals()
        assert predators.RIVALS.shape == (5, predators.my_field.D)


class TestPredatorsSenior:
    @pytest.fixture
    def senior(self, field):
        np.random.seed(42)
        return PredatorsSenior(5, field)

    def test_normal_init(self, senior, field):
        assert senior.RIVALS.shape == (5, field.D)
        assert senior.POS_PB.shape == (5, field.D)

    def test_normal_explore(self, senior, field):
        np.random.seed(42)
        pos, fit = senior.explore(generation=1)
        assert pos.shape == (5, field.D)

    def test_normal_update_rivals(self, senior):
        np.random.seed(42)
        senior.update_rivals()
        assert senior.RIVALS.shape == (5, senior.my_field.D)


class TestNeighborhood:
    @pytest.fixture
    def neighborhood(self, field):
        np.random.seed(42)
        sw = Swarm(25, field)
        topo = Topology(N=25, N_SIZE=5, name="Ring_5")
        return Neighborhood(sw, index=0, field=field, my_topology=topo)

    def test_normal_init(self, neighborhood, field):
        assert neighborhood.N_SIZE == 5
        assert neighborhood.POS.shape == (5, field.D)
        assert neighborhood.FIT.shape == (5, field.K)

    def test_normal_explore(self, neighborhood, field):
        np.random.seed(42)
        leader = np.zeros(field.D)
        lbest = np.zeros(field.D)
        pos, fit = neighborhood.explore(generation=1, leader=leader, LBEST=lbest)
        assert pos.shape == (5, field.D)
