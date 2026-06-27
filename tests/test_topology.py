import numpy as np
import pytest
from topology import Topology


class TestTopologySelectEdge:
    def test_normal_ring_5(self):
        topo = Topology(N=25, N_SIZE=5, name="Ring_5")
        assert len(topo.relation) == 25
        assert len(topo.relation[0]) == 5

    def test_normal_ring_3(self):
        topo = Topology(N=9, N_SIZE=3, name="Ring_3")
        assert len(topo.relation) == 9
        assert len(topo.relation[0]) == 3

    def test_normal_ring_7(self):
        topo = Topology(N=25, N_SIZE=7, name="Ring_7")
        assert len(topo.relation) == 25
        assert len(topo.relation[0]) == 7

    def test_normal_neumann(self):
        topo = Topology(N=25, N_SIZE=5, name="Neumann")
        assert len(topo.relation) == 25
        # 中心粒子は自分自身
        assert topo.relation[0][0] == 0

    def test_normal_cylinder(self):
        topo = Topology(N=25, N_SIZE=5, name="Cylinder")
        assert len(topo.relation) == 25
        assert topo.relation[0] is not None

    def test_normal_hexagonal(self):
        topo = Topology(N=25, N_SIZE=7, name="Hexagonal")
        assert len(topo.relation) == 25

    def test_normal_grid(self):
        topo = Topology(N=25, N_SIZE=5, name="Grid")
        assert len(topo.relation) == 25

    def test_abnormal_unknown_name(self, capsys):
        topo = Topology(N=9, N_SIZE=3, name="Unknown")
        captured = capsys.readouterr()
        assert "ERROR" in captured.out
        assert topo.relation == -1
