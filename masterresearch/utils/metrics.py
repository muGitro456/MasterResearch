"""パレートフロント評価指標（被覆率・RNI）の計算モジュール。

metrics_evaluator.py（tools/）および simulation.py から呼び出される。
"""
import glob

import numpy as np
import pandas as pd


def cover_rate(arcEval: np.ndarray, divNum: int) -> float:
    """パレートフロント（2目的）の被覆率を計算する。

    目的空間を `divNum` 分割したグリッドのうち、解が1つ以上存在する
    区画の割合を目的ごとに求め、その平均を返す。

    Args:
        arcEval: 評価対象のパレートフロント（列0, 1が各目的の評価値）。
        divNum: 各目的軸の分割数。

    Returns:
        被覆率（0〜1）。
    """
    K = arcEval.shape[1]
    min_f = np.array([np.min(arcEval[:, 0]), np.min(arcEval[:, 1])])
    max_f = np.array([np.max(arcEval[:, 0]), np.max(arcEval[:, 1])])

    width = np.array([max_f[0] - min_f[0], max_f[1] - min_f[1]]) / divNum

    region = np.zeros((K, divNum))
    cover = np.zeros(K)
    for k in range(K):
        for r in range(arcEval.shape[0]):
            for div in range(divNum):
                lowLim = min_f[k] + width[k] * div
                highLim = lowLim + width[k]
                if lowLim <= arcEval[r, k] and arcEval[r, k] <= highLim:
                    region[k, div] = region[k, div] + 1
                    break
        for div in range(divNum):
            if region[k, div] != 0:
                cover[k] = cover[k] + 1
        cover[k] = cover[k] / divNum
    return float(np.sum(cover) / K)


def display(pfs: list, idx: np.ndarray) -> None:
    """指標の平均・中央値・最大値・最小値（該当試行番号付き）を表示する。

    Args:
        pfs: 各試行に対応するパレートフロントファイル名のリスト（表示のみに使用）。
        idx: 試行ごとの指標値。
    """
    print("Average is {}".format(np.average(idx)))
    print("Median  is {}".format(np.median(idx)))
    print("Maximum is {}, No.{} ({})".format(np.max(idx), np.argmax(idx)+1, pfs[np.argmax(idx)]))
    print("Minimum is {}, No.{} ({})".format(np.min(idx), np.argmin(idx)+1, pfs[np.argmin(idx)]))


def evaluation(targetDir: str, *indicators: np.ndarray) -> None:
    """解の個数・被覆率の統計を計算して表示する。

    `indicators` が渡されない場合は `targetDir` 内の `front_*.csv` を
    読み込んで解の個数・被覆率を計算し直す（`tools/metrics_evaluator.py --val` 用）。
    渡された場合はその値をそのまま使う（`simulation.run_simulation` 用）。

    Args:
        targetDir: パレートフロントCSV（`front_*.csv`）が格納されたディレクトリ。
        *indicators: 省略可。`(numOfSols, cr)` の順で試行ごとの指標配列を渡す。
    """
    paretoFronts = sorted(glob.glob(targetDir + '/front_*.csv'))
    numOfSols = np.zeros(len(paretoFronts))
    cr = np.zeros(len(paretoFronts))

    if len(indicators) == 0:
        for t, pf in enumerate(paretoFronts):
            df = pd.read_csv(pf, index_col=0)
            solutions = df.values
            numOfSols[t] = solutions.shape[0]
            cr[t] = cover_rate(solutions, divNum=solutions.shape[0])
    else:
        numOfSols = indicators[0]
        cr = indicators[1]

    print("\n---Numerical Results---")
    print("THE NUMBER OF SOLS")
    display(paretoFronts, numOfSols)

    print("\nCOVER RATE")
    display(paretoFronts, cr)


def rni(dFName1: str, dFName2: str) -> tuple[float, float]:
    """2つのパレートフロントを統合したフロント中での、各手法由来の解の比率（RNI）を計算する。

    2つの解集合を結合してパレートフロントを再構築し、その中に生き残った
    解のうちどちらの手法由来かで比率を求める。値が大きい側がより優勢。

    Args:
        dFName1: 1つ目のパレートフロントCSVファイルのパス。
        dFName2: 2つ目のパレートフロントCSVファイルのパス。

    Returns:
        `(dFName1側の比率, dFName2側の比率)`。
    """
    df1 = pd.read_csv(dFName1, index_col=0)
    df2 = pd.read_csv(dFName2, index_col=0)
    n1 = df1.values
    n2 = df2.values
    S1 = np.hstack((n1, np.zeros((n1.shape[0], 1))))
    S2 = np.hstack((n2, np.ones((n2.shape[0], 1))))
    S_union = np.vstack((S1, S2))

    S_front_eval = np.zeros((1000, 3))
    indices_sorted = np.argsort(S_union[:, 0])
    S_union_sorted = S_union[indices_sorted]

    S_front_eval[0] = S_union_sorted[0]
    Na = 1
    n1_p = 0
    n2_p = 0
    for r in range(1, S_union_sorted.shape[0]):
        if S_union_sorted[r, 1] < S_front_eval[Na - 1, 1]:
            S_front_eval[Na] = S_union_sorted[r]
            if S_front_eval[Na, 2] == 0:
                n1_p += 1
            else:
                n2_p += 1
            Na += 1

    return (n1_p / (n1_p + n2_p), n2_p / (n1_p + n2_p))
