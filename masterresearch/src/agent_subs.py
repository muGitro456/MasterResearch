"""提案手法 C（MASTER_C）で使用する近傍サブ粒子群の定義。"""
from __future__ import annotations

import copy
from typing import TYPE_CHECKING

import numpy as np

from ..utils import logger as db
from ..utils.config_loader import load_yaml

if TYPE_CHECKING:
    from .agent import Swarm
    from .field import SearchSpace
    from .topology import Topology

param_dict = load_yaml('parameters.yaml')

class SubSwarm:
    """MASTER_C において、粒子群を等分割したサブ粒子群の1つ。

    `agent.Swarm` と同じ PSO 更新式（慣性・自己認識・社会認識）に従うが、
    対象となる粒子は全体粒子群のうち自分の担当範囲のみ。

    Attributes:
        N_SUB_PARTICLE: このサブ粒子群を構成する粒子数。
        POS: 担当粒子の位置 (N_SUB_PARTICLE, D)。
        VEL: 担当粒子の速度 (N_SUB_PARTICLE, D)。
        FIT: 担当粒子の現在の評価値 (N_SUB_PARTICLE, K)。
        POS_PB: 担当粒子のパーソナルベスト位置 (N_SUB_PARTICLE, D)。
        FIT_PB: 担当粒子のパーソナルベスト評価値 (N_SUB_PARTICLE, K)。
    """

    # クラス変数
    W = param_dict["INERTIA"]
    """慣性係数（`parameters.yaml` の `INERTIA`）。`agent.Swarm.W` と同じ値。"""
    C1 = param_dict["SELF_AWARENESS"]
    """自己認識係数（`SELF_AWARENESS`）。パーソナルベストへ向かう強さ。"""
    C2 = param_dict["SOCIAL_AWARENESS"]
    """社会認識係数（`SOCIAL_AWARENESS`）。リーダー（グローバルベスト）へ向かう強さ。"""

    def __init__(self, N_SUB_PARTICLE: int, swarm: Swarm, index: int, field: SearchSpace) -> None:
        """全体粒子群 `swarm` から、`index` 番目のサブ粒子群分を切り出して初期化する。

        Args:
            N_SUB_PARTICLE: サブ粒子群を構成する粒子数。
            swarm: 参照元の全体粒子群。
            index: このサブ粒子群の番号（0始まり）。`swarm` 内での担当範囲は
                `[index * N_SUB_PARTICLE, (index + 1) * N_SUB_PARTICLE)`。
            field: 探索空間・目的関数を表す `SearchSpace`。
        """
        self.N_SUB_PARTICLE = N_SUB_PARTICLE
        self.POS = np.empty((N_SUB_PARTICLE, field.D))
        self.VEL = np.empty((N_SUB_PARTICLE, field.D))
        self.FIT = np.empty((N_SUB_PARTICLE, field.K))
        self.POS_PB = np.empty((N_SUB_PARTICLE, field.D))
        self.FIT_PB = np.empty((N_SUB_PARTICLE, field.K))

        for j in range(N_SUB_PARTICLE):
            self.POS[j] = swarm.POS[index * N_SUB_PARTICLE + j]
            self.VEL[j] = swarm.VEL[index * N_SUB_PARTICLE + j]
            self.FIT[j] = swarm.FIT[index * N_SUB_PARTICLE + j]
            self.POS_PB[j] = swarm.POS_PB[index * N_SUB_PARTICLE + j]
            self.FIT_PB[j] = swarm.FIT_PB[index * N_SUB_PARTICLE + j]

    def update_vel(self, gbL: np.ndarray, my_field: SearchSpace, gen: int) -> None:
        """慣性・自己認識・社会認識の3項からなる PSO 速度更新式で速度を更新する。

        Args:
            gbL: リーダー（グローバルベスト）の位置。
            my_field: 探索空間。速度の最大値制限に使用する。
            gen: 現在の世代番号。
        """
        VEL_TMP = SubSwarm.W * self.VEL \
                + SubSwarm.C1 * np.random.rand(self.N_SUB_PARTICLE, my_field.D) * (self.POS_PB - self.POS) \
                + SubSwarm.C2 * np.random.rand(self.N_SUB_PARTICLE, my_field.D) * (gbL - self.POS)

        self.VEL = my_field.speedmeter(VEL_TMP, gen)

    def update_pos(self, field: SearchSpace) -> None:
        """速度を加算して位置を更新し、探索空間の境界処理を適用する。

        Args:
            field: 境界チェック（`check_boundaries`）に使用する探索空間。
        """
        _POS_TMP = self.POS + self.VEL
        self.POS, self.VEL = field.check_boundaries(_POS_TMP, self.VEL)

    def update_pb(self) -> None:
        """各粒子のパーソナルベストを、現在の評価値が優越する場合に更新する。

        全目的で優越していれば必ず更新し、一部の目的のみで優越する場合は
        50%の確率で更新する（`agent.Swarm.update_pb` と同じルール）。
        """
        for i in range(self.N_SUB_PARTICLE):
            if all(self.FIT[i] < self.FIT_PB[i]):
                self.POS_PB[i] = copy.deepcopy(self.POS[i])
            elif any(self.FIT[i] < self.FIT_PB[i]):
                if np.random.rand() > 0.5:
                    self.POS_PB[i] = copy.deepcopy(self.POS[i])

class Neighborhood_C:
    """MASTER_C において、トポロジーで結ばれた近傍サブ粒子群のビュー。

    `agent.Neighborhood` のサブ粒子群版。近傍にある複数の `SubSwarm` の
    粒子をまとめて1つの配列として保持し、局所認識項を加えた PSO 更新を行う。
    """

    C5 = param_dict["LOCAL_AWARENESS"]
    """局所認識係数（`LOCAL_AWARENESS`）。近傍内のローカルリーダー（LBEST）へ向かう強さ。`agent.Neighborhood.C5` と同じ値。"""

    def __init__(self, sub_swarms: list[SubSwarm], index: int, field: SearchSpace, my_topology: Topology) -> None:
        """指定インデックスのサブ粒子群の近傍集合を構築する。

        Args:
            sub_swarms: 全サブ粒子群のリスト。
            index: 近傍の中心となるサブ粒子群のインデックス。
            field: 探索空間・目的関数を表す `SearchSpace`。
            my_topology: サブ粒子群間の近傍関係を定義するトポロジー。
        """
        self.N_SIZE = len(my_topology.relation[index])
        self.N_SUB_PARTICLE = sub_swarms[0].N_SUB_PARTICLE
        self.my_field = field
        self.my_swarm = sub_swarms
        self.index = index

        self.POS = np.empty((self.N_SIZE * self.N_SUB_PARTICLE, field.D))
        self.VEL = np.empty((self.N_SIZE * self.N_SUB_PARTICLE, field.D))
        self.FIT = np.empty((self.N_SIZE * self.N_SUB_PARTICLE, field.K))
        self.POS_PB = np.empty((self.N_SIZE * self.N_SUB_PARTICLE, field.D))
        self.FIT_PB = np.empty((self.N_SIZE * self.N_SUB_PARTICLE, field.K))

        for m in range(self.N_SIZE):
            idx_edge = int(my_topology.relation[index][m])
            for j in range(self.N_SUB_PARTICLE):
                self.POS[m * self.N_SUB_PARTICLE + j] = self.my_swarm[idx_edge].POS[j]
                self.VEL[m * self.N_SUB_PARTICLE + j] = self.my_swarm[idx_edge].VEL[j]
                self.FIT[m * self.N_SUB_PARTICLE + j] = self.my_swarm[idx_edge].FIT[j]
                self.POS_PB[m * self.N_SUB_PARTICLE + j] = self.my_swarm[idx_edge].POS_PB[j]
                self.FIT_PB[m * self.N_SUB_PARTICLE + j] = self.my_swarm[idx_edge].FIT_PB[j]

    def explore(self, generation: int, leader: np.ndarray, LBEST: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """1世代分、速度・位置・評価値・パーソナルベストを更新する。

        Args:
            generation: 現在の世代番号（1始まり）。
            leader: アーカイブから選ばれたグローバルリーダーの位置。
            LBEST: 近傍サブアーカイブから選ばれたローカルリーダーの位置。

        Returns:
            更新後の位置と評価値のタプル `(POS, FIT)`。
        """
        self.update_vel(leader, LBEST, self.my_field, generation)

        self.my_swarm[self.index].update_pos(self.my_field)
        self.FIT = self.my_field.update_fit(self.POS)

        db.store(self.POS, 'p')
        db.store(self.VEL, 'v')

        self.my_swarm[self.index].update_pb()
        self.my_field.update_fit(self.POS_PB)

        return self.POS, self.FIT

    def update_vel(self, gbL: np.ndarray, lb: np.ndarray, my_field: SearchSpace, gen: int) -> None:
        """慣性・自己認識・社会認識・局所認識の4項からなる速度更新式で速度を更新する。

        Args:
            gbL: グローバルリーダーの位置。
            lb: ローカルリーダー（LBEST）の位置。
            my_field: 探索空間。速度の最大値制限に使用する。
            gen: 現在の世代番号。
        """
        VEL_TMP = self.my_swarm[0].W * self.VEL \
                + self.my_swarm[0].C1 * np.random.rand(self.N_SIZE * self.N_SUB_PARTICLE, my_field.D) * (self.POS_PB - self.POS) \
                + self.my_swarm[0].C2 * np.random.rand(self.N_SIZE * self.N_SUB_PARTICLE, my_field.D) * (gbL - self.POS) \
                + self.C5          * np.random.rand(self.N_SIZE * self.N_SUB_PARTICLE, my_field.D) * (lb - self.POS)

        self.VEL = my_field.speedmeter(VEL_TMP, gen)
