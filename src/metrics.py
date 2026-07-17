"""パレートフロント評価指標（被覆率・RNI）の計算モジュール。

database.py（tools/）および main.py から呼び出される。
"""
import numpy as np
import pandas as pd
import glob


def cover_rate(arcEval: np.ndarray, divNum: int) -> float:
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
    print("Average is {}".format(np.average(idx)))
    print("Median  is {}".format(np.median(idx)))
    print("Maximum is {}, No.{} ({})".format(np.max(idx), np.argmax(idx)+1, pfs[np.argmax(idx)]))
    print("Minimum is {}, No.{} ({})".format(np.min(idx), np.argmin(idx)+1, pfs[np.argmin(idx)]))


def evaluation(targetDir: str, *indicators) -> None:
    paretoFronts = sorted(glob.glob(targetDir + '/*.csv'))
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
