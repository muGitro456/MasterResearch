"""ベンチマーク関数（ZDT / DTLZ 系）と探索空間の定義。"""
import copy
from typing import Any, Callable

import numpy as np


class SearchSpace:
    """探索空間（決定変数の範囲・速度制限・境界処理）を表すクラス。

    Attributes:
        fun: 目的関数（`Problem.fun`）。
        D: 決定変数の次元数。
        upper: 決定変数の上限 (D,)。
        lower: 決定変数の下限 (D,)。
        K: 目的関数の数。
        GEN_MAX: 最大世代数。
        VMAX: 世代 `g` を受け取り、その世代での最大速度を返す関数（指数的に減衰）。
        DAMP: 境界を超えた際の反射係数。
    """

    def __init__(self, params: dict[str, Any], problem: "Problem") -> None:
        """パラメータ辞書とテスト問題から探索空間を構築する。

        Args:
            params: `parameters.yaml` 由来のパラメータ辞書
                （`GENERATION_MAX`, `VMAX_INITIAL`, `VMAX_END`, `DAMP` を使用）。
            problem: 決定変数の範囲・目的関数を提供する `Problem`。
        """
        self.fun = problem.fun
        self.D = problem.D
        self.upper = problem.upper
        self.lower = problem.lower
        self.K = problem.K

        self.GEN_MAX = params["GENERATION_MAX"]
        VMAX_INI = (self.upper - self.lower) / params["VMAX_INITIAL"]
        VMAX_END = (self.upper - self.lower) / params["VMAX_END"]
        self.VMAX = lambda g: VMAX_INI * np.exp(((g-1) / self.GEN_MAX) * np.log(VMAX_END / VMAX_INI))  # noqa: E731
        self.DAMP = params["DAMP"]

    def update_fit(self, x: np.ndarray) -> np.ndarray:
        """位置 `x` に対する目的関数値を計算する。

        Args:
            x: 評価する位置の集合 (N, D)。

        Returns:
            評価値の配列 (N, K)。
        """
        return self.fun(x).T

    def check_boundaries(self, POS: np.ndarray, VEL: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """探索空間の境界を超えた粒子の位置・速度を反射させる。

        境界を超えた分だけ内側に折り返し（`DAMP` で減衰）、対応する速度成分の
        符号を反転させることで、境界へ張り付くのを防ぐ。

        Args:
            POS: 更新後の位置の候補。
            VEL: 更新後の速度の候補。

        Returns:
            境界処理を適用した後の位置と速度のタプル `(pos_new, vel_new)`。
        """
        for pos, vel in zip(POS, VEL):
            while any(pos < self.lower) or any(pos > self.upper):
                pos[pos > self.upper] = self.DAMP * (2 * self.upper[pos > self.upper] - pos[pos > self.upper])
                pos[pos < self.lower] = self.DAMP * (2 * self.lower[pos < self.lower] - pos[pos < self.lower])

                vel[pos > self.upper] = self.DAMP * (-1) * vel[pos > self.upper]
                vel[pos < self.lower] = self.DAMP * (-1) * vel[pos < self.lower]

        pos_new = copy.deepcopy(POS)
        vel_new = copy.deepcopy(VEL)
        return pos_new, vel_new

    def speedmeter(self, VEL: np.ndarray, gen: int) -> np.ndarray:
        """速度を、その世代における最大速度 `VMAX(gen)` でクリップする。

        Args:
            VEL: クリップ対象の速度。
            gen: 現在の世代番号。

        Returns:
            クリップ後の速度。
        """
        vmax = self.VMAX(gen)
        for vel in VEL:
            vel[vel > vmax] = vmax[vel > vmax]
            vel[vel < -vmax] = -vmax[vel < -vmax]
        VEL_NEW = copy.deepcopy(VEL)
        return VEL_NEW

class Problem:
    """ベンチマーク問題（ZDT / DTLZ 系・多峰性関数）の目的関数と決定変数範囲を定義する。

    `functions.yaml` の設定に基づき、`name` に応じた目的関数 `self.fun` を構築する。
    多峰性問題（Rastrigin 等）は共通の ZDT ライクな枠組みに `multimodel_func` の
    出力を `g(x)` として組み込むことで、2目的問題として扱う。

    Attributes:
        fun: 位置 `x (N, D)` を受け取り評価値 `(K, N)` を返す目的関数。
        D: 決定変数の次元数。
        upper: 決定変数の上限。
        lower: 決定変数の下限。
        K: 目的関数の数。
    """

    def __init__(self, func_dict: dict[str, Any]) -> None:
        """`functions.yaml` の1エントリから目的関数と決定変数範囲を構築する。

        Args:
            func_dict: `name`, `dimension`, `upper`, `lower` を持つ設定辞書。
        """
        name = func_dict["name"]
        dimension = func_dict["dimension"]
        upper = np.array([func_dict["upper"] for _ in range(dimension)])
        lower = np.array([func_dict["lower"] for _ in range(dimension)])

        match name:
            case "DTLZ1":  # DTLZ1を解く場合
                A = lambda x : np.sum((x[:, 2:] - 0.5) ** 2)  # noqa: E731
                B = lambda x : np.sum(np.cos(20 * np.pi * (x[:, 2:] - 0.5)))  # noqa: E731
                g = lambda x : 100 * (5 + A(x) - B(x))  # noqa: E731

                f1 = lambda x : 0.5 * x[:, 0] * x[:, 1] * (1 + g(x))  # noqa: E731
                f2 = lambda x : 0.5 * x[:, 0] * (1 - x[:, 1]) * (1 + g(x))  # noqa: E731
                f3 = lambda x : 0.5 * (1 - x[:, 0]) * (1 + g(x))  # noqa: E731

                self.fun = lambda x : np.array([f1(x), f2(x), f3(x)])  # noqa: E731
                self.D = dimension
                self.upper = upper
                self.lower = lower
                self.K = 3

            case "ZDT2":  # ZDT2を解く場合
                f = lambda x : x[:, 0]  # noqa: E731
                g = lambda x : 1 + (9 / (dimension - 1)) * np.sum(x[:, 2:])  # noqa: E731
                h = lambda x : 1 - (f(x) / g(x)) ** 2  # noqa: E731

                self.fun = lambda x : np.array([f(x), g(x) * h(x)])  # noqa: E731
                self.D = dimension
                self.upper = upper
                self.lower = lower
                self.K = 2

            case "ZDT6":  # ZDT6を解く場合
                f = lambda x : 1 - np.exp(-4 * x[:, 0]) * pow(np.sin(6 * np.pi * x[:, 0]), 6)  # noqa: E731
                g = lambda x : 1 + 9 * pow(np.sum(x[:, 1:], axis=1) / 9, 0.25)  # noqa: E731
                h = lambda x : 1 - (f(x) / g(x)) ** 2  # noqa: E731

                self.fun = lambda x : np.array([f(x), g(x) * h(x)])  # noqa: E731
                self.D = dimension
                self.upper = upper
                self.lower = lower
                self.K = 2

            case _:  # 多峰性問題を解く場合
                F = self.multimodel_func(func_dict["name"], dimension)
                f = lambda x : x[:, 0]  # noqa: E731
                g = lambda x : 1 + F(x)  # noqa: E731
                h = lambda x : 1 - np.sqrt(f(x) / g(x))  # noqa: E731

                self.fun = lambda x : np.array([f(x), g(x) * h(x)])  # noqa: E731
                self.D = dimension + 1
                self.upper = np.append(np.ones(1), upper)
                self.lower = np.append(np.zeros(1), lower)
                self.K = 2

    def multimodel_func(self, func_name: str, dimension: int) -> Callable[..., np.ndarray]:
        """多峰性ベンチマーク関数（Rastrigin 等）を、ZDT ライクな枠組みの `g(x)` として返す。

        Args:
            func_name: 関数名（`Rastrigin`, `Ackley`, `Griewank`, `Sphere`, `Booth`, `Alpine`）。
            dimension: 決定変数の次元数（先頭1次元は `f(x) = x[:, 0]` に使うため、
                残り `x[:, 1:]` に対して関数を評価する）。

        Returns:
            位置 `x` を受け取り `g(x)` の値を返す関数。

        Raises:
            ValueError: `func_name` が未知の場合。
        """
        match func_name:
            case "Rastrigin":
                A = lambda x : np.sum(x[:, 1:] ** 2, axis=1)  # noqa: E731
                B = lambda x : - 10 * np.sum(np.cos(2 * np.pi * x[:, 1:]), axis=1)  # noqa: E731
                F = lambda x : 10 * dimension + A(x) + B(x)  # noqa: E731

            case "Ackley":
                A = lambda x : -0.2 * np.sqrt((1.0 / dimension) * np.sum(x[:, 1:] ** 2, axis = 1))  # noqa: E731
                B = lambda x : (1.0 / dimension) * np.sum(np.cos(2 * np.pi * x[:, 1:]), axis=1)  # noqa: E731
                F = lambda x : 20 - 20 * np.exp(A(x)) + np.e - np.exp(B(x))  # noqa: E731

            case "Griewank":
                A = lambda x : (1.0 / 4000.0) * np.sum(x[:, 1:] ** 2, axis = 1)  # noqa: E731
                w = np.array([1.0 / np.sqrt(k + 1) for k in range(dimension)])
                B = lambda x : - np.prod(np.cos(x[:, 1:] * w), axis=1)  # noqa: E731
                F = lambda x : 1 + A(x) + B(x)  # noqa: E731

            case "Sphere":
                F = lambda x : np.sum(x[:, 1:]**2, axis=1)  # noqa: E731

            case "Booth":
                F = lambda x : (x[:, 1] + 2*x[:, 2] - 7)**2 + (2*x[:, 1] + x[:, 2] - 5)**2  # noqa: E731

            case "Alpine":
                F = lambda x : np.sum(np.abs(x[:, 1:] * np.sin(x[:, 1:]) + 0.1 * x[:, 1:]))  # noqa: E731

            case _: # defaultの場合
                raise ValueError(f"Unknown function: {func_name}")
        return F
