from typing import Any
from tqdm import tqdm
import numpy as np
from agent import PredatorsSenior, Neighborhood
from agent_subs import SubSwarm, Neighborhood_C
from topology import Topology
from field import Problem
from related import MOPSO
from archive import Archive
import logger as db

class MASTER_A(MOPSO):
    def __init__(self, params: dict[str, Any], problem: Problem, topology_dict: dict[str, Any]) -> None:
        super().__init__(params, problem)
        
        self.N_SIZE = topology_dict["N_SIZE"]

        # トポロジーの初期化
        self.my_topology = Topology(self.N, topology_dict["N_SIZE"], topology_dict["name"])
        
        # 近傍粒子群とサブアーカイブの初期化
        self.init_neighbors()

        """
        self.neighbors = [None] * self.N
        self.sub_arc_MOPSO = [None] * self.N
        for i in range(self.N):
            self.neighbors[i] = Neighborhood(self.sw_MOPSO, i, self.field, self.my_topology)
            self.sub_arc_MOPSO[i] = Archive(self.neighbors[i].POS, self.neighbors[i].FIT, self.NA_MAX, self.field.D, self.field.K)
        """

        # FPO粒子群とアーカイブの初期化
        self.sw_FPO = PredatorsSenior(self.N, self.field)
        self.arc_FPO = Archive(self.sw_FPO.POS, self.sw_FPO.FIT, self.NA_MAX, self.field.D, self.field.K)

        # 全体アーカイブの初期化
        self.arc_MASTER = Archive(self.sw_MOPSO.POS, self.sw_MOPSO.FIT, self.NA_MAX, self.field.D, self.field.K)

    def init_neighbors(self) -> None:
        self.neighbors = [None] * self.N
        self.sub_arc_MOPSO = [None] * self.N
        for i in range(self.N):
            self.neighbors[i] = Neighborhood(self.sw_MOPSO, i, self.field, self.my_topology)
            self.sub_arc_MOPSO[i] = Archive(self.neighbors[i].POS, self.neighbors[i].FIT, self.NA_MAX, self.field.D, self.field.K)
    
    def simulation(self) -> Archive:
        for g in tqdm(range(self.GEN_MAX), desc="Generation", leave=False):
            # MOPSOの処理
            leader = self.arc_MOPSO.select_leader()
            for i in range(self.N):
                # サブアーカイブの統合
                #POS_TEMP, FIT_TEMP = self.union_neighbors(self.sub_arc_MOPSO, i, self.my_topology)
                #union_sub_arc_MOPSO  = Archive(POS_TEMP, FIT_TEMP, self.NA_MAX, self.field.D, self.field.K)
                #LBEST = union_sub_arc_MOPSO.select_leader()
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

        return self.arc_MASTER

    def union_neighbors(self, sub_arcs: list[Archive], index: int, topology: Topology) -> tuple[np.ndarray, np.ndarray]:
        POS_TEMP = sub_arcs[index].pos_gb
        FIT_TEMP = sub_arcs[index].fit_gb

        for m in range(1, self.N_SIZE):
            idx_edge = int(topology.relation[index][m])
            POS_TEMP = np.vstack((POS_TEMP, sub_arcs[idx_edge].pos_gb))
            FIT_TEMP = np.vstack((FIT_TEMP, sub_arcs[idx_edge].fit_gb))

        return POS_TEMP, FIT_TEMP

class MASTER_B(MASTER_A):
    def __init__(self, params: dict[str, Any], problem: Problem, topology_dict: dict[str, Any]) -> None:
        super().__init__(params, problem, topology_dict)

    def simulation(self) -> Archive:
        return super().simulation()

class MASTER_C(MOPSO):
    def __init__(self, params: dict[str, Any], problem: Problem, topology_dict: dict[str, Any]) -> None:
        super().__init__(params, problem)
        self.N_SUB_SWARM = params["N_SUB_SWARM"]  # サブ群の個数
        self.N_SUB_PARTICLE = self.N // self.N_SUB_SWARM  # サブ群を構成する粒子の数

        # トポロジーの初期化
        self.my_topology = Topology(self.N_SUB_SWARM, topology_dict["N_SIZE"], topology_dict["name"])
        
        # サブ粒子群とサブアーカイブの初期化        
        self.init_sub_swarm()

        self.neighbors_C = [None] * self.N_SUB_SWARM
        self.sub_arc_MOPSO = [None] * self.N_SUB_SWARM
        for i in range(self.N_SUB_SWARM):
            self.neighbors_C[i] = Neighborhood_C(self.sub_sw_MOPSO, i, self.field, self.my_topology)
            self.sub_arc_MOPSO[i] = Archive(self.neighbors_C[i].POS, self.neighbors_C[i].FIT, self.NA_MAX, self.field.D, self.field.K)
    
        # FPO粒子群とアーカイブの初期化
        self.sw_FPO = PredatorsSenior(self.N, self.field)
        self.arc_FPO = Archive(self.sw_FPO.POS, self.sw_FPO.FIT, self.NA_MAX, self.field.D, self.field.K)

        # 全体アーカイブの初期化
        self.arc_MASTER_C = Archive(self.sw_MOPSO.POS, self.sw_MOPSO.FIT, self.NA_MAX, self.field.D, self.field.K)

    def init_sub_swarm(self) -> None:
        self.sub_sw_MOPSO = [None] * self.N_SUB_SWARM  # サブ群の初期化

        for i in range(self.N_SUB_SWARM):
                self.sub_sw_MOPSO[i] = SubSwarm(self.N_SUB_PARTICLE, self.sw_MOPSO, i, self.field)
            
    def simulation(self) -> Archive:
        for g in tqdm(range(self.GEN_MAX), desc="Generation", leave=False):
            # MOPSOの処理
            leader = self.arc_MOPSO.select_leader()
            for i in range(self.N_SUB_SWARM):
                # 各サブアーカイブにおけるリーダーの中から最も良いものをLBESTとする.
                
                sub_arcs_pos = np.vstack((self.sub_arc_MOPSO[int(self.my_topology.relation[i][0])].pos_gb, \
                                          self.sub_arc_MOPSO[int(self.my_topology.relation[i][1])].pos_gb, \
                                          self.sub_arc_MOPSO[int(self.my_topology.relation[i][2])].pos_gb, \
                                          self.sub_arc_MOPSO[int(self.my_topology.relation[i][3])].pos_gb, \
                                          self.sub_arc_MOPSO[int(self.my_topology.relation[i][4])].pos_gb))
                
                sub_arcs_fit = np.vstack((self.sub_arc_MOPSO[int(self.my_topology.relation[i][0])].fit_gb, \
                                          self.sub_arc_MOPSO[int(self.my_topology.relation[i][1])].fit_gb, \
                                          self.sub_arc_MOPSO[int(self.my_topology.relation[i][2])].fit_gb, \
                                          self.sub_arc_MOPSO[int(self.my_topology.relation[i][3])].fit_gb, \
                                          self.sub_arc_MOPSO[int(self.my_topology.relation[i][4])].fit_gb))
                
                sub_arcs = Archive(sub_arcs_pos, sub_arcs_fit, self.NA_MAX, self.field.D, self.field.K)
                lbest = sub_arcs.select_leader()
                #lbest = self.sub_arc_MOPSO[i].select_leader() # 近傍サブアーカイブからリーダーを選択するか要検討
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

        return self.arc_MASTER_C