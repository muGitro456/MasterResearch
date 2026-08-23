"""パレートフロントアーカイブの管理。"""
import numpy as np


class Archive:
    """非劣解（パレートフロント）を保持・更新するアーカイブ。

    容量が `NA_MAX` を超えた場合は、混雑度（crowding distance）が
    最小の解から順に間引かれる。

    Attributes:
        cr: 直近に計算された被覆率（`calc_cover_rate` を呼ぶまでは 0.0）。
        NA_MAX: アーカイブが保持できる解の最大数。
        D: 決定変数の次元数。
        K: 目的関数の数。
        pos_gb: アーカイブ中の非劣解の位置。
        fit_gb: アーカイブ中の非劣解の評価値。
    """

    def __init__(self, pos_swarm: np.ndarray, fit_swarm: np.ndarray, NA_MAX: int, D: int, K: int) -> None:
        """粒子群の現在の位置・評価値からパレートフロントを構築してアーカイブを初期化する。

        Args:
            pos_swarm: 初期集団の位置。
            fit_swarm: 初期集団の評価値。
            NA_MAX: アーカイブが保持できる解の最大数。
            D: 決定変数の次元数。
            K: 目的関数の数。
        """
        self.cr = 0.0 # 被覆率
        self.NA_MAX = NA_MAX
        self.D = D
        self.K = K

        self.pos_gb, self.fit_gb = self.make_pareto_front(pos_swarm, fit_swarm)

    def make_pareto_front(self, pos: np.ndarray, fit: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """候補解集合から非劣解のみを抽出し、`NA_MAX` を超える分は混雑度で間引く。

        目的数が2の場合はソート済み配列上を1回走査するだけで非劣解を判定できる
        ため専用の高速な経路を使い、3以上の場合は総当たりの優越判定を行う。

        Args:
            pos: 候補解の位置。
            fit: 候補解の評価値。

        Returns:
            非劣解の位置と評価値のタプル `(pos_gb, fit_gb)`。
        """
        pos_gb: np.ndarray = np.zeros((self.NA_MAX, self.D)) # アーカイブに保存されているGBestの位置
        fit_gb: np.ndarray = np.zeros((self.NA_MAX, self.K)) # アーカイブに保存されているGBestの評価値

        if self.K == 2:
            indices_sorted = np.argsort(fit[:, 0])
            pos_sorted = pos[indices_sorted]
            fit_sorted = fit[indices_sorted]

            pos_gb[0] = pos_sorted[0]
            fit_gb[0] = fit_sorted[0]
            NA = 1 # 解(GBest)の個数

            for r in range(1, fit.shape[0]):
                if fit_sorted[r, 1] < fit_gb[NA - 1, 1]:
                    if NA < self.NA_MAX:
                        pos_gb[NA] = pos_sorted[r]
                        fit_gb[NA] = fit_sorted[r]
                    else:
                        pos_gb = np.vstack((pos_gb, pos_sorted[r]))
                        fit_gb = np.vstack((fit_gb, fit_sorted[r]))
                    NA += 1
        else:
            NA = 0
            for r in range(fit.shape[0]):
                others = [j for j in range(fit.shape[0]) if j != r]
                for k in range(self.K):
                    for other in others:
                        if fit[other, k] <= fit[r, k]:
                            break
                    else:
                        if NA < self.NA_MAX:
                            pos_gb[NA] = pos[r]
                            fit_gb[NA] = fit[r]
                        else:
                            pos_gb = np.vstack((pos_gb, pos[r]))
                            fit_gb = np.vstack((fit_gb, fit[r]))
                        NA += 1

        while NA > self.NA_MAX:
            cd = self.calc_crowding_distance(fit_gb[:NA, :])
            minIdx = np.argmin(cd)
            pos_gb = np.delete(pos_gb, minIdx, axis = 0)
            fit_gb = np.delete(fit_gb, minIdx, axis = 0)
            NA -= 1

        return pos_gb[:NA, :], fit_gb[:NA, :]

    def update_archive(self, POS_current: np.ndarray, FIT_current: np.ndarray) -> None:
        """既存のアーカイブと新規候補解を統合し、パレートフロントを再構築する。

        Args:
            POS_current: 追加する候補解の位置。
            FIT_current: 追加する候補解の評価値。
        """
        tmp_pos_gb = np.vstack((self.pos_gb, POS_current))
        tmp_fit_gb = np.vstack((self.fit_gb, FIT_current))
        self.pos_gb, self.fit_gb = self.make_pareto_front(tmp_pos_gb, tmp_fit_gb)

    def select_leader(self) -> np.ndarray:
        """混雑度に応じた重み付きランダム選択でリーダー（GBest）を1つ選ぶ。

        混雑度が大きい（＝周囲の解が疎な）解ほど選ばれやすくすることで、
        パレートフロント上の多様性を維持する。

        Returns:
            選ばれたリーダーの位置。
        """
        cd = self.calc_crowding_distance()

        if len(cd) == 1:
            return self.pos_gb[0]  # type: ignore[no-any-return]
        elif len(cd) == 2:
            selected = self.pos_gb[0] if np.random.rand() > 0.5 else self.pos_gb[1]
            return selected  # type: ignore[no-any-return]
        else:
            weights = np.array( [cd[j] for j in range(len(cd)) if np.abs(cd[j]) != np.inf] )
            p_weights = np.array([weights[j] / np.sum(weights) for j in range(len(weights))])
            chosen = np.random.choice(weights, size=1, p=p_weights)
            leader = np.argwhere(cd == chosen)
            return self.pos_gb[leader[0,0]]  # type: ignore[no-any-return]

    def calc_crowding_distance(self, fit_gb: np.ndarray | None = None) -> np.ndarray:
        """各解の混雑度（NSGA-II 由来の crowding distance）を計算する。

        Args:
            fit_gb: 評価値集合。省略時は `self.fit_gb` を使う。

        Returns:
            各解の混雑度の配列。両端の解は最大値扱いとする。
        """
        if fit_gb is None:
            fit_gb = self.fit_gb
        NA = len(fit_gb)
        cd = np.zeros(NA)
        indices_sorted = np.argsort(fit_gb[:,0]) # f1軸に対して昇順ソート
        fit_gb_sorted = fit_gb[indices_sorted]

        if NA != 1:
            for k in range(self.K):
                front_up = np.append(fit_gb_sorted[1:, k], np.inf)
                front_down = np.append(np.inf, fit_gb_sorted[:-1, k])
                cd = cd + np.abs(front_up - front_down)
        if NA > 3:
            cd[0] = np.max(cd[1:-2])
        elif NA > 2:
            cd[0] = cd[1]
        else:
            cd[0] = 1
        cd[-1] = cd[0]
        return cd

    def calc_cover_rate(self, divNum: int) -> float:
        """アーカイブの被覆率（目的空間をグリッド分割した際の占有率の平均）を計算する。

        Args:
            divNum: 各目的軸の分割数。

        Returns:
            被覆率（0〜1）。
        """
        if self.K == 3:
            min_f = np.array([np.min(self.fit_gb[:, 0]), np.min(self.fit_gb[:, 1]), np.min(self.fit_gb[:, 2])])
            max_f = np.array([np.max(self.fit_gb[:, 0]), np.max(self.fit_gb[:, 1]), np.max(self.fit_gb[:, 2])])
            width = np.array([max_f[0] - min_f[0], max_f[1] - min_f[1], max_f[2] - min_f[2]]) / divNum
        else:
            min_f = np.array([np.min(self.fit_gb[:, 0]), np.min(self.fit_gb[:, 1])])
            max_f = np.array([np.max(self.fit_gb[:, 0]), np.max(self.fit_gb[:, 1])])
            width = np.array([max_f[0] - min_f[0], max_f[1] - min_f[1]]) / divNum

        region = np.zeros((self.K, divNum))
        cover = np.zeros(self.K)
        for k in range(self.K):
            for r in range(self.fit_gb.shape[0]):
                for div in range(divNum):
                    lowLim = min_f[k] + width[k] * div
                    highLim = lowLim + width[k]

                    if lowLim <= self.fit_gb[r, k] and self.fit_gb[r, k] <= highLim:
                        region[k, div] = region[k, div] + 1
                        break

            for div in range(divNum):
                if region[k, div] != 0:
                    cover[k] = cover[k] + 1
            cover[k] = cover[k] / divNum
        return np.sum(cover) / self.K

    def union_archive(self, POS1: np.ndarray, FIT1: np.ndarray, POS2: np.ndarray, FIT2: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """2つの解集合を単純に結合する（非劣解の絞り込みは行わない）。

        Args:
            POS1: 1つ目の解集合の位置。
            FIT1: 1つ目の解集合の評価値。
            POS2: 2つ目の解集合の位置。
            FIT2: 2つ目の解集合の評価値。

        Returns:
            結合後の位置と評価値のタプル `(POS_COMB, FIT_COMB)`。
        """
        POS_COMB = np.vstack((POS1, POS2))
        FIT_COMB = np.vstack((FIT1, FIT2))
        return POS_COMB, FIT_COMB
