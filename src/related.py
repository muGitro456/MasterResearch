# Pythonでは、一つのファイルには一クラス!という哲学はない.
from typing import Any

from tqdm import tqdm

import logger as db
from agent import Predators, PredatorsSenior, Swarm
from archive import Archive
from field import Problem, SearchSpace


class MOPSO:
    def __init__(self, params: dict[str, Any], problem: Problem) -> None:
        self.N = params["N"]
        self.NA_MAX = params["N_ARCHIVE_MAX"]
        self.GEN_MAX = params["GENERATION_MAX"]

        self.field = SearchSpace(params, problem)
        self.sw_MOPSO = Swarm(self.N, self.field)
        self.arc_MOPSO = Archive(self.sw_MOPSO.POS, self.sw_MOPSO.FIT, self.NA_MAX, self.field.D, self.field.K)

    def simulation(self) -> Archive:
        for g in tqdm(range(self.GEN_MAX), desc="Generation", leave=False):
            leader = self.arc_MOPSO.select_leader()
            POS, FIT = self.sw_MOPSO.explore(g+1, leader)

            self.arc_MOPSO.update_archive(POS, FIT)
            db.store(self.arc_MOPSO.fit_gb, 'e')
            db.store_trajectory(self.arc_MOPSO.fit_gb)

        return self.arc_MOPSO

class FPOMOPSO(MOPSO):
    def __init__(self, params: dict[str, Any], problem: Problem) -> None:
        super().__init__(params, problem)

        self.sw_FPO = Predators(self.N, self.field)
        self.arc_FPO = Archive(self.sw_FPO.POS, self.sw_FPO.FIT, self.NA_MAX, self.field.D, self.field.K)
        self.arc_FPOMOPSO = Archive(self.sw_MOPSO.POS, self.sw_MOPSO.FIT, self.NA_MAX, self.field.D, self.field.K)

    def simulation(self) -> Archive:
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
    def __init__(self, params: dict[str, Any], problem: Problem) -> None:
        super().__init__(params, problem)

        # 上書き処理
        self.sw_FPO = PredatorsSenior(self.N, self.field)
        self.arc_FPO = Archive(self.sw_FPO.POS, self.sw_FPO.FIT, self.NA_MAX, self.field.D, self.field.K)
        self.arc_FPOMOPSO = Archive(self.sw_MOPSO.POS, self.sw_MOPSO.FIT, self.NA_MAX, self.field.D, self.field.K)

    def simulation(self) -> Archive:
        return super().simulation()
