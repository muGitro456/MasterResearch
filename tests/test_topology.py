import numpy as np
import pytest
from masterresearch.src.topology import Topology


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
        assert topo.relation[0][0] == 0

    def test_neumann_left_right_wrap_within_same_row(self):
        # 3x3トーラス上でLEFT/RIGHTは同じ行内でラップアラウンドするべき
        # (行をまたいで先頭行に潰れてはいけない)
        CENTER, UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3, 4
        topo = Topology(N=9, N_SIZE=5, name="Neumann")

        # i=3 (row=1, col=0): LEFTは同じ行の右端(row=1,col=2)=5, RIGHTは(row=1,col=1)=4
        assert topo.relation[3][LEFT] == 5
        assert topo.relation[3][RIGHT] == 4

        # i=8 (row=2, col=2): LEFTは(row=2,col=1)=7, RIGHTは同じ行の左端(row=2,col=0)=6
        assert topo.relation[8][LEFT] == 7
        assert topo.relation[8][RIGHT] == 6

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

    def test_grid_down_neighbor_for_non_bottom_row(self):
        # 3x3格子でi=0(row=0,col=0)は下端でないので、下の要素(row=1,col=0)=3を
        # 近傍に持つべき(ラップアラウンドしない純粋な格子)
        topo = Topology(N=9, N_SIZE=5, name="Grid")
        assert 3 in topo.relation[0]

    def test_grid_bottom_row_has_no_wrapped_down_neighbor(self):
        # 3x3格子でi=6(row=2,col=0、下端)は下近傍を持たない
        # (現状の実装は誤ってラップした0を下近傍として追加してしまう)
        topo = Topology(N=9, N_SIZE=5, name="Grid")
        assert 0 not in topo.relation[6]

    def test_abnormal_unknown_name(self):
        with pytest.raises(ValueError, match="Unknown topology"):
            Topology(N=9, N_SIZE=3, name="Unknown")

def test_select_edge_unknown_name_raises():
    topo = Topology(N=5, N_SIZE=5, name="Ring_5")
    with pytest.raises(ValueError, match="Unknown topology"):
        topo.select_edge("UNKNOWN_TOPOLOGY")
