"""粒子群最適化（PSO）の基底エージェントクラス。"""
from __future__ import annotations

import copy
import json
from typing import TYPE_CHECKING

import numpy as np

import logger as db

if TYPE_CHECKING:
    from field import SearchSpace
    from topology import Topology

with open('./property/parameters.json', 'r') as f:
    param_dict = json.load(f)

class Swarm:
    # クラス変数
    W = param_dict["INERTIA"]
    C1 = param_dict["SELF_AWARENESS"]
    C2 = param_dict["SOCIAL_AWARENESS"]

    def __init__(self, N: int, field: SearchSpace) -> None:
        self.N = N
        self.my_field = field

        self.POS = field.lower + (field.upper - field.lower) * np.random.rand(self.N, field.D)
        self.VEL = np.zeros((self.N, field.D))
        self.FIT = field.update_fit(self.POS)
        self.POS_PB = copy.deepcopy(self.POS)
        self.FIT_PB = copy.deepcopy(self.FIT)

    def explore(self, generation: int, leader: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        self.update_vel(leader, self.my_field, generation)

        self.update_pos(self.my_field)
        self.FIT = self.my_field.update_fit(self.POS)

        db.store(self.POS, 'p')
        db.store(self.VEL, 'v')

        self.update_pb()
        self.my_field.update_fit(self.POS_PB)

        return self.POS, self.FIT

    def update_vel(self, gbL: np.ndarray, my_field: SearchSpace, gen: int) -> None:
        VEL_TMP = Swarm.W * self.VEL \
                + Swarm.C1 * np.random.rand(self.N, my_field.D) * (self.POS_PB - self.POS) \
                + Swarm.C2 * np.random.rand(self.N, my_field.D) * (gbL - self.POS)
        #print("In update_vel _VEL_TMP.shape = ",_VEL_TMP.shape)
        self.VEL = my_field.speedmeter(VEL_TMP, gen)

    def update_pos(self, field: SearchSpace) -> None:
        _POS_TMP = self.POS + self.VEL
        self.POS, self.VEL = field.check_boundaries(_POS_TMP, self.VEL)

    def update_pb(self) -> None:
        for i in range(self.N):
            if all(self.FIT[i] < self.FIT_PB[i]):
                self.POS_PB[i] = copy.deepcopy(self.POS[i])
            elif any(self.FIT[i] < self.FIT_PB[i]):
                if np.random.rand() > 0.5:
                    self.POS_PB[i] = copy.deepcopy(self.POS[i])

class Predators(Swarm):
    C3 = param_dict["RIVAL_AWARENESS"]
    W_INI = param_dict["INERTIA_INITIAL"]
    W_END = param_dict["INERTIA_END"]

    def __init__(self, N: int, field: SearchSpace) -> None:
        super().__init__(N, field)
        self.RIVALS = np.zeros((self.N, field.D))

    def explore(self, generation: int) -> tuple[np.ndarray, np.ndarray]:  # type: ignore[override]
        self.update_rivals()
        self.update_vel(self.my_field, generation)

        super().update_pos(self.my_field)
        self.FIT = self.my_field.update_fit(self.POS)

        db.store(self.POS, 'p')
        db.store(self.VEL, 'v')

        return self.POS, self.FIT

    def update_vel(self, my_field: SearchSpace, gen: int) -> None:  # type: ignore[override]
        W_FPO = Predators.W_INI + (Predators.W_END - Predators.W_INI) * (gen / my_field.GEN_MAX)

        VEL_TMP = W_FPO * Predators.C3 * np.random.rand(self.N, my_field.D) * (self.RIVALS - self.POS)
        self.VEL = my_field.speedmeter(VEL_TMP, gen)

    def update_rivals(self) -> None:
        FIT_PRED = self.calc_fit_predator()
        SUM_FIT_PRED = np.sum(FIT_PRED)
        for i in range(self.N):
            rival_idx: int = i
            if np.random.rand() < (FIT_PRED[i] / SUM_FIT_PRED) * np.random.rand():
                rivals = np.array([k for k in range(self.N) if k != i])
                rival_idx = int(np.random.choice(rivals, 1)[0])
            self.RIVALS[i] = self.POS[rival_idx]

    def calc_fit_predator(self) -> np.ndarray:
        K = self.FIT.shape[1]
        FIT_PRED: np.ndarray = np.zeros(self.N)
        for i in range(self.N):
            for k in range(K):
                FIT_PRED[i] += self.FIT[i, k] / (np.max(self.FIT[:, k]) - np.min(self.FIT[:, k]))

        FIT_PRED = 1 / FIT_PRED
        return FIT_PRED

class PredatorsSenior(Predators):
    C4 = param_dict["SELF_AWARENESS_OF_PREDATOR"]

    def __init__(self, N: int, field: SearchSpace) -> None:
        super().__init__(N, field)

    def explore(self, generation: int) -> tuple[np.ndarray, np.ndarray]:  # type: ignore[override]
        self.update_rivals()
        self.update_vel(self.my_field, generation)

        super().update_pos(self.my_field)
        self.FIT = self.my_field.update_fit(self.POS)

        db.store(self.POS, 'p')
        db.store(self.VEL, 'v')

        super().update_pb()
        self.my_field.update_fit(self.POS_PB)

        return self.POS, self.FIT

    def update_rivals(self) -> None:
        FIT_PRED = self.calc_fit_predator()
        SUM_FIT_PRED = np.sum(FIT_PRED)
        for i in range(self.N):
            rival_idx: int = i
            if np.random.rand() < (FIT_PRED[i] / SUM_FIT_PRED):
                rivals = np.array([k for k in range(self.N) if k != i])
                rival_idx = int(np.random.choice(rivals, 1)[0])
            self.RIVALS[i] = self.POS[rival_idx]

    def update_vel(self, my_field: SearchSpace, gen: int) -> None:  # type: ignore[override]
        W_FPO = Predators.W_INI + \
                (Predators.W_END - Predators.W_INI) * (gen / my_field.GEN_MAX)

        VEL_TMP = W_FPO * Predators.C3 * np.random.rand(self.N, my_field.D) * (self.RIVALS - self.POS) \
                        + PredatorsSenior.C4 * np.random.rand(self.N, my_field.D) * (self.POS_PB - self.POS)
        self.VEL = my_field.speedmeter(VEL_TMP, gen)

class Neighborhood:
    C5 = param_dict["LOCAL_AWARENESS"]

    def __init__(self, swarm: Swarm, index: int, field: SearchSpace, my_topology: Topology) -> None:
        self.N_SIZE = len(my_topology.relation[index])
        self.my_field = field
        self.my_swarm = swarm

        self.POS = np.empty((self.N_SIZE, field.D))
        self.VEL = np.empty((self.N_SIZE, field.D))
        self.FIT = np.empty((self.N_SIZE, field.K))
        self.POS_PB = np.empty((self.N_SIZE, field.D))
        self.FIT_PB = np.empty((self.N_SIZE, field.K))

        for m in range(self.N_SIZE):
            idx_edge = int(my_topology.relation[index][m])
            self.POS[m] = swarm.POS[idx_edge]
            self.VEL[m] = swarm.VEL[idx_edge]
            self.FIT[m] = swarm.FIT[idx_edge]
            self.POS_PB[m] = swarm.POS_PB[idx_edge]
            self.FIT_PB[m] = swarm.FIT_PB[idx_edge]

    def explore(self, generation: int, leader: np.ndarray, LBEST: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        self.update_vel(leader, LBEST, self.my_field, generation)

        self.my_swarm.update_pos(self.my_field)
        self.FIT = self.my_field.update_fit(self.POS)

        db.store(self.POS, 'p')
        db.store(self.VEL, 'v')

        self.my_swarm.update_pb()
        self.my_field.update_fit(self.POS_PB)

        return self.POS, self.FIT

    def update_vel(self, gbL: np.ndarray, lb: np.ndarray, my_field: SearchSpace, gen: int) -> None:
        VEL_TMP = self.my_swarm.W * self.VEL \
                + self.my_swarm.C1 * np.random.rand(self.N_SIZE, my_field.D) * (self.POS_PB - self.POS) \
                + self.my_swarm.C2 * np.random.rand(self.N_SIZE, my_field.D) * (gbL - self.POS) \
                + self.C5          * np.random.rand(self.N_SIZE, my_field.D) * (lb - self.POS)

        self.VEL = my_field.speedmeter(VEL_TMP, gen)
