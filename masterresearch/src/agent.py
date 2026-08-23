"""多目的粒子群最適化（MOPSO）の基底エージェントクラス。"""
from __future__ import annotations

import copy
from typing import TYPE_CHECKING

import numpy as np

from ..utils import logger as db
from ..utils.config_loader import load_yaml

if TYPE_CHECKING:
    from .field import SearchSpace
    from .topology import Topology

param_dict = load_yaml('parameters.yaml')

class Swarm:
    """MOPSO の粒子群（PSO の基本更新式に従う）。

    Attributes:
        N: 粒子数。
        my_field: 探索空間・目的関数を表す `SearchSpace`。
        POS: 各粒子の位置 (N, D)。
        VEL: 各粒子の速度 (N, D)。
        FIT: 各粒子の現在の評価値 (N, K)。
        POS_PB: 各粒子のパーソナルベスト位置 (N, D)。
        FIT_PB: 各粒子のパーソナルベスト評価値 (N, K)。
    """

    # クラス変数
    W = param_dict["INERTIA"]
    """慣性係数（`parameters.yaml` の `INERTIA`）。前世代の速度をどれだけ引き継ぐかを決める。"""
    C1 = param_dict["SELF_AWARENESS"]
    """自己認識係数（`SELF_AWARENESS`）。パーソナルベストへ向かう強さ。"""
    C2 = param_dict["SOCIAL_AWARENESS"]
    """社会認識係数（`SOCIAL_AWARENESS`）。リーダー（グローバルベスト）へ向かう強さ。"""

    def __init__(self, N: int, field: SearchSpace) -> None:
        """粒子群をランダムな位置で初期化する。

        Args:
            N: 粒子数。
            field: 探索空間・目的関数を表す `SearchSpace`。
        """
        self.N = N
        self.my_field = field

        self.POS = field.lower + (field.upper - field.lower) * np.random.rand(self.N, field.D)
        self.VEL = np.zeros((self.N, field.D))
        self.FIT = field.update_fit(self.POS)
        self.POS_PB = copy.deepcopy(self.POS)
        self.FIT_PB = copy.deepcopy(self.FIT)

    def explore(self, generation: int, leader: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """1世代分、速度・位置・評価値・パーソナルベストを更新する。

        Args:
            generation: 現在の世代番号（1始まり）。
            leader: アーカイブから選ばれたリーダー（グローバルベスト）の位置。

        Returns:
            更新後の位置と評価値のタプル `(POS, FIT)`。
        """
        self.update_vel(leader, self.my_field, generation)

        self.update_pos(self.my_field)
        self.FIT = self.my_field.update_fit(self.POS)

        db.store(self.POS, 'p')
        db.store(self.VEL, 'v')

        self.update_pb()
        self.my_field.update_fit(self.POS_PB)

        return self.POS, self.FIT

    def update_vel(self, gbL: np.ndarray, my_field: SearchSpace, gen: int) -> None:
        """慣性・自己認識・社会認識の3項からなる PSO 速度更新式で速度を更新する。

        Args:
            gbL: リーダー（グローバルベスト）の位置。
            my_field: 探索空間。速度の最大値制限（`speedmeter`）に使用する。
            gen: 現在の世代番号。
        """
        VEL_TMP = Swarm.W * self.VEL \
                + Swarm.C1 * np.random.rand(self.N, my_field.D) * (self.POS_PB - self.POS) \
                + Swarm.C2 * np.random.rand(self.N, my_field.D) * (gbL - self.POS)
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
        50%の確率で更新する（多目的化に伴う確率的な採用ルール）。
        """
        for i in range(self.N):
            if all(self.FIT[i] < self.FIT_PB[i]):
                self.POS_PB[i] = copy.deepcopy(self.POS[i])
            elif any(self.FIT[i] < self.FIT_PB[i]):
                if np.random.rand() > 0.5:
                    self.POS_PB[i] = copy.deepcopy(self.POS[i])

class Predators(Swarm):
    """FPO（捕食者行動最適化）の捕食者群。ライバル（RIVALS）へ向かって移動する。

    Attributes:
        RIVALS: 各捕食者が追跡する対象（ライバル）の位置 (N, D)。
    """

    C3 = param_dict["RIVAL_AWARENESS"]
    """競合相手係数（`RIVAL_AWARENESS`）。ライバルへ向かう強さ。"""
    W_INI = param_dict["INERTIA_INITIAL"]
    """慣性係数の初期値（`INERTIA_INITIAL`）。"""
    W_END = param_dict["INERTIA_END"]
    """慣性係数の最終値（`INERTIA_END`）。世代が進むにつれて `W_INI` から `W_END` へ線形に変化する（`update_vel` 参照）。"""

    def __init__(self, N: int, field: SearchSpace) -> None:
        """捕食者群を初期化する。

        Args:
            N: 捕食者数。
            field: 探索空間・目的関数を表す `SearchSpace`。
        """
        super().__init__(N, field)
        self.RIVALS = np.zeros((self.N, field.D))

    def explore(self, generation: int) -> tuple[np.ndarray, np.ndarray]:  # type: ignore[override]
        """1世代分、ライバル選択・速度・位置・評価値を更新する。

        Args:
            generation: 現在の世代番号（1始まり）。

        Returns:
            更新後の位置と評価値のタプル `(POS, FIT)`。
        """
        self.update_rivals()
        self.update_vel(self.my_field, generation)

        super().update_pos(self.my_field)
        self.FIT = self.my_field.update_fit(self.POS)

        db.store(self.POS, 'p')
        db.store(self.VEL, 'v')

        return self.POS, self.FIT

    def update_vel(self, my_field: SearchSpace, gen: int) -> None:  # type: ignore[override]
        """ライバルへ向かう1項のみからなる FPO の速度更新式で速度を更新する。

        慣性重みは世代とともに `W_INI` から `W_END` へ線形に変化する。

        Args:
            my_field: 探索空間。速度の最大値制限に使用する。
            gen: 現在の世代番号。
        """
        W_FPO = Predators.W_INI + (Predators.W_END - Predators.W_INI) * (gen / my_field.GEN_MAX)

        VEL_TMP = W_FPO * Predators.C3 * np.random.rand(self.N, my_field.D) * (self.RIVALS - self.POS)
        self.VEL = my_field.speedmeter(VEL_TMP, gen)

    def update_rivals(self) -> None:
        """各捕食者のライバル（追跡対象）を確率的に再選択する。

        乗り換え確率は評価値から算出した「捕食適合度」`FIT_PRED[i]` に比例する
        （`calc_fit_predator` 参照）。捕食適合度が高いほど乗り換え確率が上がる点に注意。
        """
        FIT_PRED = self.calc_fit_predator()
        SUM_FIT_PRED = np.sum(FIT_PRED)
        for i in range(self.N):
            rival_idx: int = i
            if np.random.rand() < (FIT_PRED[i] / SUM_FIT_PRED) * np.random.rand():
                rivals = np.array([k for k in range(self.N) if k != i])
                rival_idx = int(np.random.choice(rivals, 1)[0])
            self.RIVALS[i] = self.POS[rival_idx]

    def calc_fit_predator(self) -> np.ndarray:
        """各捕食者の捕食適合度を、目的ごとに正規化した評価値の総和の逆数として算出する。

        Returns:
            捕食適合度の配列 (N,)。値が大きいほど「良い」捕食者。
        """
        K = self.FIT.shape[1]
        FIT_PRED: np.ndarray = np.zeros(self.N)
        for i in range(self.N):
            for k in range(K):
                FIT_PRED[i] += self.FIT[i, k] / (np.max(self.FIT[:, k]) - np.min(self.FIT[:, k]))

        FIT_PRED = 1 / FIT_PRED
        return FIT_PRED

class PredatorsSenior(Predators):
    """パーソナルベスト（自己認識項）を追加した SENIOR / MASTER 系手法向けの捕食者群。"""

    C4 = param_dict["SELF_AWARENESS_OF_PREDATOR"]
    """捕食者の自己認識係数（`SELF_AWARENESS_OF_PREDATOR`）。パーソナルベストへ向かう強さ（`Swarm.C1` の捕食者版）。"""

    def __init__(self, N: int, field: SearchSpace) -> None:
        """捕食者群を初期化する。

        Args:
            N: 捕食者数。
            field: 探索空間・目的関数を表す `SearchSpace`。
        """
        super().__init__(N, field)

    def explore(self, generation: int) -> tuple[np.ndarray, np.ndarray]:  # type: ignore[override]
        """1世代分、ライバル選択・速度・位置・評価値・パーソナルベストを更新する。

        Args:
            generation: 現在の世代番号（1始まり）。

        Returns:
            更新後の位置と評価値のタプル `(POS, FIT)`。
        """
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
        """各捕食者のライバルを確率的に再選択する（`Predators` より乗り換え確率が高い）。"""
        FIT_PRED = self.calc_fit_predator()
        SUM_FIT_PRED = np.sum(FIT_PRED)
        for i in range(self.N):
            rival_idx: int = i
            if np.random.rand() < (FIT_PRED[i] / SUM_FIT_PRED):
                rivals = np.array([k for k in range(self.N) if k != i])
                rival_idx = int(np.random.choice(rivals, 1)[0])
            self.RIVALS[i] = self.POS[rival_idx]

    def update_vel(self, my_field: SearchSpace, gen: int) -> None:  # type: ignore[override]
        """ライバル追跡項と自己認識項（パーソナルベストへの引力）を合成して速度を更新する。

        Args:
            my_field: 探索空間。速度の最大値制限に使用する。
            gen: 現在の世代番号。
        """
        W_FPO = Predators.W_INI + \
                (Predators.W_END - Predators.W_INI) * (gen / my_field.GEN_MAX)

        VEL_TMP = W_FPO * Predators.C3 * np.random.rand(self.N, my_field.D) * (self.RIVALS - self.POS) \
                        + PredatorsSenior.C4 * np.random.rand(self.N, my_field.D) * (self.POS_PB - self.POS)
        self.VEL = my_field.speedmeter(VEL_TMP, gen)

class Neighborhood:
    """トポロジーで結ばれた近傍粒子群のビュー（MASTER_A / MASTER_B が使用）。

    `swarm` の一部粒子（`my_topology.relation[index]` で指定される近傍）への
    参照的なスナップショットを保持し、局所認識項（LBEST）を加えた PSO 更新を行う。
    """

    C5 = param_dict["LOCAL_AWARENESS"]
    """局所認識係数（`LOCAL_AWARENESS`）。近傍内のローカルリーダー（LBEST）へ向かう強さ。"""

    def __init__(self, swarm: Swarm, index: int, field: SearchSpace, my_topology: Topology) -> None:
        """指定インデックスの粒子の近傍集合を、元の粒子群からコピーして構築する。

        Args:
            swarm: 参照元の粒子群全体。
            index: 近傍の中心となる粒子のインデックス。
            field: 探索空間・目的関数を表す `SearchSpace`。
            my_topology: 近傍関係を定義するトポロジー。
        """
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
        """1世代分、速度・位置・評価値・パーソナルベストを更新する。

        Args:
            generation: 現在の世代番号（1始まり）。
            leader: アーカイブから選ばれたグローバルリーダーの位置。
            LBEST: 近傍サブアーカイブから選ばれたローカルリーダーの位置。

        Returns:
            更新後の位置と評価値のタプル `(POS, FIT)`。
        """
        self.update_vel(leader, LBEST, self.my_field, generation)

        self.my_swarm.update_pos(self.my_field)
        self.FIT = self.my_field.update_fit(self.POS)

        db.store(self.POS, 'p')
        db.store(self.VEL, 'v')

        self.my_swarm.update_pb()
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
        VEL_TMP = self.my_swarm.W * self.VEL \
                + self.my_swarm.C1 * np.random.rand(self.N_SIZE, my_field.D) * (self.POS_PB - self.POS) \
                + self.my_swarm.C2 * np.random.rand(self.N_SIZE, my_field.D) * (gbL - self.POS) \
                + self.C5          * np.random.rand(self.N_SIZE, my_field.D) * (lb - self.POS)

        self.VEL = my_field.speedmeter(VEL_TMP, gen)
