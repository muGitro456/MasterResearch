"""粒子群の位置・速度・適合値をメモリに記録するモジュール。

record_writer.py が CSV 出力時にここのグローバル変数を参照する。
"""
import os

import numpy as np
import pandas as pd

LOG_POS: list = []
LOG_VEL: list = []
LOG_FIT: list = []
LOG_TRAJ: list = []


def reset_log() -> None:
    LOG_POS.clear()
    LOG_VEL.clear()
    LOG_FIT.clear()
    LOG_TRAJ.clear()


def store_trajectory(fit_gb: np.ndarray) -> None:
    LOG_TRAJ.append(fit_gb.copy())


def store(var: np.ndarray, target: str) -> None:
    match target:
        case 'p':
            LOG_POS.append(var)
        case 'v':
            LOG_VEL.append(var)
        case 'e':
            LOG_FIT.append(var)
        case _:
            print("該当なし")


def write4debug(target: str, maxgen: int, m_num: str, m_name: str, output_dir: str = 'backLog') -> None:
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
