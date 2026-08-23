"""提案手法（MASTER_A / MASTER_B / MASTER_C）の実装。"""
from typing import Any

import numpy as np
from tqdm import tqdm

from ..utils import logger as db
from .agent import Neighborhood, PredatorsSenior
from .agent_subs import Neighborhood_C, SubSwarm
from .archive import Archive
from .field import Problem
from .related import MOPSO
from .topology import Topology


class MASTER_A(MOPSO):
    """MOPSO をトポロジー付き近傍探索に拡張し、FPO（Senior版）と統合した提案手法。

    粒子ごとに近傍集合 `Neighborhood` とサブアーカイブを持ち、局所認識項を
    加えた探索を行う。近傍探索の結果と FPO 捕食者群の結果を全体アーカイブ
    `arc_MASTER` に統合する。
    """

    def __init__(self, params: dict[str, Any], problem: Problem, topology_dict: dict[str, Any]) -> None:
        """MOPSO を初期化した上で、トポロジー・近傍・FPO・全体アーカイブを構築する。

        Args:
            params: `parameters.yaml` 由来のパラメータ辞書。
            problem: 解くべきベンチマーク問題。
            topology_dict: `topologies.yaml` の1エントリ（`name`, `N_SIZE`）。
        """
        super().__init__(params, problem)

        # トポロジーの初期化
        self.my_topology = Topology(self.N, topology_dict["N_SIZE"], topology_dict["name"])

        # 近傍粒子群とサブアーカイブの初期化
        self.init_neighbors()

        # FPO粒子群とアーカイブの初期化
        self.sw_FPO = PredatorsSenior(self.N, self.field)
        self.arc_FPO = Archive(self.sw_FPO.POS, self.sw_FPO.FIT, self.NA_MAX, self.field.D, self.field.K)

        # 全体アーカイブの初期化
        self.arc_MASTER = Archive(self.sw_MOPSO.POS, self.sw_MOPSO.FIT, self.NA_MAX, self.field.D, self.field.K)

    def init_neighbors(self) -> None:
        """全粒子分の近傍集合 `Neighborhood` とサブアーカイブを構築する。"""
        self.neighbors: list[Neighborhood] = []
        self.sub_arc_MOPSO: list[Archive] = []
        for i in range(self.N):
            neighbor = Neighborhood(self.sw_MOPSO, i, self.field, self.my_topology)
            sub_arc = Archive(neighbor.POS, neighbor.FIT, self.NA_MAX, self.field.D, self.field.K)
            self.neighbors.append(neighbor)
            self.sub_arc_MOPSO.append(sub_arc)

    def simulation(self) -> Archive:
        """`GEN_MAX` 世代分、近傍探索・FPO探索・アーカイブ統合を繰り返す。

        Returns:
            近傍探索と FPO の非劣解を統合した最終世代のアーカイブ。
        """
        for g in tqdm(range(self.GEN_MAX), desc="Generation", leave=False):
            # MOPSOの処理
            leader = self.arc_MOPSO.select_leader()
            for i in range(self.N):
                # サブアーカイブの統合
                lbest = self.sub_arc_MOPSO[i].select_leader()
                POS, FIT = self.neighbors[i].explore(g+1, leader, lbest)

                # アーカイブの更新
                self.sub_arc_MOPSO[i].update_archive(POS, FIT)
                self.arc_MOPSO.update_archive(POS, FIT)

            # FPOの処理
            POS_FPO, FIT_FPO = self.sw_FPO.explore(g+1)

            # アーカイブの更新
            self.arc_FPO.update_archive(POS_FPO, FIT_FPO)

            # アーカイブの統合
            POS_COMB, FIT_COMB = self.arc_MASTER.union_archive(self.arc_MOPSO.pos_gb, self.arc_MOPSO.fit_gb, self.arc_FPO.pos_gb, self.arc_FPO.fit_gb)

            # 全体アーカイブの更新
            self.arc_MASTER.update_archive(POS_COMB, FIT_COMB)
            db.store(self.arc_MASTER.fit_gb, 'e')
            db.store_trajectory(self.arc_MASTER.fit_gb)

        return self.arc_MASTER

class MASTER_B(MASTER_A):
    """現状は `MASTER_A` と同一の挙動（トポロジー種別の使い分けのために独立した手法として定義）。"""

    def __init__(self, params: dict[str, Any], problem: Problem, topology_dict: dict[str, Any]) -> None:
        """`MASTER_A` と同じ初期化を行う。

        Args:
            params: `parameters.yaml` 由来のパラメータ辞書。
            problem: 解くべきベンチマーク問題。
            topology_dict: `topologies.yaml` の1エントリ（`name`, `N_SIZE`）。
        """
        super().__init__(params, problem, topology_dict)

    def simulation(self) -> Archive:
        """`MASTER_A.simulation` をそのまま実行する。

        Returns:
            最終世代のアーカイブ。
        """
        return super().simulation()

class MASTER_C(MOPSO):
    """粒子群を複数のサブ粒子群に分割し、サブ粒子群単位でトポロジーを構成する提案手法。

    `MASTER_A` が粒子単位で近傍を構成するのに対し、`MASTER_C` は粒子群を
    `N_SUB_SWARM` 個のサブ粒子群（`SubSwarm`）に分割し、サブ粒子群同士の
    近傍関係（`Neighborhood_C`）で探索する。FPO（Senior版）との統合方法は
    `MASTER_A` と同様。
    """

    def __init__(self, params: dict[str, Any], problem: Problem, topology_dict: dict[str, Any]) -> None:
        """MOPSO を初期化した上で、サブ粒子群・トポロジー・FPO・全体アーカイブを構築する。

        Args:
            params: `parameters.yaml` 由来のパラメータ辞書
                （`N_SUB_SWARM` を追加で使用）。
            problem: 解くべきベンチマーク問題。
            topology_dict: `topologies.yaml` の1エントリ（`name`, `N_SIZE`）。
                サブ粒子群同士の近傍関係に使う。
        """
        super().__init__(params, problem)
        self.N_SUB_SWARM = params["N_SUB_SWARM"]  # サブ粒子群の個数
        self.N_SUB_PARTICLE = self.N // self.N_SUB_SWARM  # サブ粒子群を構成する粒子の数

        # トポロジーの初期化
        self.my_topology = Topology(self.N_SUB_SWARM, topology_dict["N_SIZE"], topology_dict["name"])

        # サブ粒子群とサブアーカイブの初期化
        self.init_sub_swarm()

        self.neighbors_C: list[Neighborhood_C] = []
        self.sub_arc_MOPSO: list[Archive] = []
        for i in range(self.N_SUB_SWARM):
            neighbor_c = Neighborhood_C(self.sub_sw_MOPSO, i, self.field, self.my_topology)
            sub_arc = Archive(neighbor_c.POS, neighbor_c.FIT, self.NA_MAX, self.field.D, self.field.K)
            self.neighbors_C.append(neighbor_c)
            self.sub_arc_MOPSO.append(sub_arc)

        # FPO粒子群とアーカイブの初期化
        self.sw_FPO = PredatorsSenior(self.N, self.field)
        self.arc_FPO = Archive(self.sw_FPO.POS, self.sw_FPO.FIT, self.NA_MAX, self.field.D, self.field.K)

        # 全体アーカイブの初期化
        self.arc_MASTER_C = Archive(self.sw_MOPSO.POS, self.sw_MOPSO.FIT, self.NA_MAX, self.field.D, self.field.K)

    def init_sub_swarm(self) -> None:
        """全体粒子群を `N_SUB_SWARM` 個の `SubSwarm` に等分割して構築する。"""
        self.sub_sw_MOPSO: list[SubSwarm] = []
        for i in range(self.N_SUB_SWARM):
            self.sub_sw_MOPSO.append(SubSwarm(self.N_SUB_PARTICLE, self.sw_MOPSO, i, self.field))

    def simulation(self) -> Archive:
        """`GEN_MAX` 世代分、サブ粒子群単位の近傍探索・FPO探索・アーカイブ統合を繰り返す。

        各サブ粒子群のローカルリーダー（LBEST）は、トポロジー上の近傍サブアーカイブ
        （個数はトポロジーの種類・位置により変動する）を一時的に結合した
        アーカイブから選出する。

        Returns:
            サブ粒子群探索と FPO の非劣解を統合した最終世代のアーカイブ。
        """
        for g in tqdm(range(self.GEN_MAX), desc="Generation", leave=False):
            # MOPSOの処理
            leader = self.arc_MOPSO.select_leader()
            for i in range(self.N_SUB_SWARM):
                # 各サブアーカイブにおけるリーダーの中から最も良いものをLBESTとする.

                neighbor_indices = [int(idx) for idx in self.my_topology.relation[i]]
                sub_arcs_pos = np.vstack([self.sub_arc_MOPSO[idx].pos_gb for idx in neighbor_indices])
                sub_arcs_fit = np.vstack([self.sub_arc_MOPSO[idx].fit_gb for idx in neighbor_indices])

                sub_arcs = Archive(sub_arcs_pos, sub_arcs_fit, self.NA_MAX, self.field.D, self.field.K)
                lbest = sub_arcs.select_leader()
                POS, FIT = self.neighbors_C[i].explore(g+1, leader, lbest)

                # MOPSOアーカイブの更新
                self.sub_arc_MOPSO[i].update_archive(POS, FIT)
                self.arc_MOPSO.update_archive(POS, FIT)

            # FPOの処理
            POS_FPO, FIT_FPO = self.sw_FPO.explore(g+1)

            # FPOアーカイブの更新
            self.arc_FPO.update_archive(POS_FPO, FIT_FPO)

            # アーカイブの統合
            POS_COMB, FIT_COMB = self.arc_MASTER_C.union_archive(self.arc_MOPSO.pos_gb, self.arc_MOPSO.fit_gb, self.arc_FPO.pos_gb, self.arc_FPO.fit_gb)

            # 全体アーカイブの更新
            self.arc_MASTER_C.update_archive(POS_COMB, FIT_COMB)
            db.store(self.arc_MASTER_C.fit_gb, 'e')
            db.store_trajectory(self.arc_MASTER_C.fit_gb)

        return self.arc_MASTER_C
