"""関連手法（MOPSO / FPOMOPSO / SENIOR）の実装。"""
from typing import Any

from tqdm import tqdm

from ..utils import logger as db
from .agent import Predators, PredatorsSenior, Swarm
from .archive import Archive
from .field import Problem, SearchSpace


class MOPSO:
    """基本的な多目的粒子群最適化（MOPSO）。

    単一の粒子群 `sw_MOPSO` のみで探索を行い、非劣解をアーカイブ `arc_MOPSO`
    に蓄積する、提案手法・他の関連手法すべての基底となる最小構成。
    """

    def __init__(self, params: dict[str, Any], problem: Problem) -> None:
        """探索空間・粒子群・アーカイブを初期化する。

        Args:
            params: `parameters.yaml` 由来のパラメータ辞書
                （`N`, `N_ARCHIVE_MAX`, `GENERATION_MAX` を使用）。
            problem: 解くべきベンチマーク問題。
        """
        self.N = params["N"]
        self.NA_MAX = params["N_ARCHIVE_MAX"]
        self.GEN_MAX = params["GENERATION_MAX"]

        self.field = SearchSpace(params, problem)
        self.sw_MOPSO = Swarm(self.N, self.field)
        self.arc_MOPSO = Archive(self.sw_MOPSO.POS, self.sw_MOPSO.FIT, self.NA_MAX, self.field.D, self.field.K)

    def simulation(self) -> Archive:
        """`GEN_MAX` 世代分、探索・アーカイブ更新を繰り返す。

        Returns:
            最終世代のアーカイブ。
        """
        for g in tqdm(range(self.GEN_MAX), desc="Generation", leave=False):
            leader = self.arc_MOPSO.select_leader()
            POS, FIT = self.sw_MOPSO.explore(g+1, leader)

            self.arc_MOPSO.update_archive(POS, FIT)
            db.store(self.arc_MOPSO.fit_gb, 'e')
            db.store_trajectory(self.arc_MOPSO.fit_gb)

        return self.arc_MOPSO

class FPOMOPSO(MOPSO):
    """MOPSO に FPO（捕食者行動最適化）の捕食者群を組み合わせたハイブリッド手法。

    MOPSO の粒子群と FPO の捕食者群を並行して探索させ、両者の非劣解を
    統合したアーカイブ `arc_FPOMOPSO` を最終結果とする。
    """

    def __init__(self, params: dict[str, Any], problem: Problem) -> None:
        """MOPSO の初期化に加え、FPO 捕食者群と統合アーカイブを初期化する。

        Args:
            params: `parameters.yaml` 由来のパラメータ辞書。
            problem: 解くべきベンチマーク問題。
        """
        super().__init__(params, problem)

        self.sw_FPO = Predators(self.N, self.field)
        self.arc_FPO = Archive(self.sw_FPO.POS, self.sw_FPO.FIT, self.NA_MAX, self.field.D, self.field.K)
        self.arc_FPOMOPSO = Archive(self.sw_MOPSO.POS, self.sw_MOPSO.FIT, self.NA_MAX, self.field.D, self.field.K)

    def simulation(self) -> Archive:
        """`GEN_MAX` 世代分、MOPSO と FPO の探索・アーカイブ統合を繰り返す。

        Returns:
            MOPSO と FPO の非劣解を統合した最終世代のアーカイブ。
        """
        for g in tqdm(range(self.GEN_MAX), desc="Generation", leave=False):
            # MOPSOの処理
            leader = self.arc_MOPSO.select_leader()
            POS, FIT = self.sw_MOPSO.explore(g+1, leader)
            self.arc_MOPSO.update_archive(POS, FIT)

            # FPOの処理
            POS_FPO, FIT_FPO = self.sw_FPO.explore(g+1)
            self.arc_FPO.update_archive(POS_FPO, FIT_FPO)

            # アーカイブの統合
            POS_COMB, FIT_COMB = self.arc_FPOMOPSO.union_archive(POS, FIT, POS_FPO, FIT_FPO)

            # 全体アーカイブの更新
            self.arc_FPOMOPSO.update_archive(POS_COMB, FIT_COMB)
            db.store(self.arc_FPOMOPSO.fit_gb, 'e')
            db.store_trajectory(self.arc_FPOMOPSO.fit_gb)

        return self.arc_FPOMOPSO

class SENIOR(FPOMOPSO):
    """FPOMOPSO の捕食者群を `PredatorsSenior` （自己認識項付き）に差し替えた手法。"""

    def __init__(self, params: dict[str, Any], problem: Problem) -> None:
        """FPOMOPSO の初期化後、捕食者群と関連アーカイブを `PredatorsSenior` 用に上書きする。

        Args:
            params: `parameters.yaml` 由来のパラメータ辞書。
            problem: 解くべきベンチマーク問題。
        """
        super().__init__(params, problem)

        # 上書き処理
        self.sw_FPO = PredatorsSenior(self.N, self.field)
        self.arc_FPO = Archive(self.sw_FPO.POS, self.sw_FPO.FIT, self.NA_MAX, self.field.D, self.field.K)
        self.arc_FPOMOPSO = Archive(self.sw_MOPSO.POS, self.sw_MOPSO.FIT, self.NA_MAX, self.field.D, self.field.K)

    def simulation(self) -> Archive:
        """`FPOMOPSO.simulation` と同じ流れで探索する（捕食者群のみ差し替え済み）。

        Returns:
            MOPSO と FPO（Senior版）の非劣解を統合した最終世代のアーカイブ。
        """
        return super().simulation()
