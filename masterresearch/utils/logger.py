"""粒子群の位置・速度・適合値をメモリに記録するモジュール。

record_writer.py が CSV 出力時にここのグローバル変数を参照する。
"""
import os

import numpy as np
import pandas as pd

from .paths import DEFAULT_OUTPUT_DIR

LOG_POS: list = []
LOG_VEL: list = []
LOG_FIT: list = []
LOG_TRAJ: list = []


def reset_log() -> None:
    """全てのログ用グローバル変数（位置・速度・評価値・軌跡）を空にする。

    `simulation.run_simulation` が軌跡記録用の追加実行を行う前に呼び出す。
    """
    LOG_POS.clear()
    LOG_VEL.clear()
    LOG_FIT.clear()
    LOG_TRAJ.clear()


def store_trajectory(fit_gb: np.ndarray) -> None:
    """1世代分のアーカイブ評価値を軌跡ログ `LOG_TRAJ` に追記する。

    Args:
        fit_gb: その世代のアーカイブ内評価値。
    """
    LOG_TRAJ.append(fit_gb.copy())


def store(var: np.ndarray, target: str) -> None:
    """位置・速度・評価値のいずれかをログ用グローバル変数に追記する。

    Args:
        var: 記録する配列。
        target: 記録先を表すキー（`'p'`: 位置, `'v'`: 速度, `'e'`: 評価値）。
            それ以外の値の場合は何も記録せずメッセージを表示する。
    """
    match target:
        case 'p':
            LOG_POS.append(var)
        case 'v':
            LOG_VEL.append(var)
        case 'e':
            LOG_FIT.append(var)
        case _:
            print("該当なし")


def write4debug(target: str, maxgen: int, m_num: str, m_name: str, output_dir: str = DEFAULT_OUTPUT_DIR) -> None:
    """デバッグ用に、記録済みの位置または速度の全世代分を CSV に書き出す。

    `simulation.run_simulation` の `isDebugged` フラグが `True` の場合のみ呼ばれる。

    Args:
        target: 出力対象（`'p'`: 位置, `'v'`: 速度）。
        maxgen: 記録されている世代数（`LOG_POS`/`LOG_VEL` の長さ）。
        m_num: 手法番号（出力先ディレクトリ名に使用）。
        m_name: 手法名（出力先ディレクトリ・ファイル名に使用）。
        output_dir: 出力先ルートディレクトリ。
    """
    new_dir_path = os.path.join(output_dir, m_num + '_' + m_name) + '/'
    os.makedirs(new_dir_path, exist_ok=True)

    match target:
        case 'p':
            col = ['x' + str(d) for d in range(LOG_POS[0].shape[1])]
            row = [str(d % LOG_POS[0].shape[0]) for d in range(LOG_POS[0].shape[0] * maxgen)]
            tmp = np.array(LOG_POS)
            tmp = (tmp.flatten()).reshape(LOG_POS[0].shape[0] * maxgen, LOG_POS[0].shape[1]).copy()
            df = pd.DataFrame(tmp, index=row, columns=col)
            df.to_csv(os.path.join(new_dir_path, m_name + '_pos_SP.csv'), header=True, index=True)
        case 'v':
            col = ['v' + str(d) for d in range(LOG_VEL[0].shape[1])]
            row = [str(d % LOG_VEL[0].shape[0]) for d in range(LOG_VEL[0].shape[0] * maxgen)]
            tmp = np.array(LOG_VEL)
            tmp = (tmp.flatten()).reshape(LOG_VEL[0].shape[0] * maxgen, LOG_VEL[0].shape[1]).copy()
            df = pd.DataFrame(tmp, index=row, columns=col)
            df.to_csv(os.path.join(new_dir_path, m_name + '_vel_SP.csv'), header=True, index=True)
        case _:
            print("Error : logger")
