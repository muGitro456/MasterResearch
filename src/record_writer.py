"""実験結果（パレートフロント座標・評価指標統計）を CSV に書き出すモジュール。

logger.py のグローバル変数（LOG_POS, LOG_VEL, LOG_FIT）を読み取って出力する。
"""
import datetime
import os

import numpy as np
import pandas as pd

import logger


def write4plot(trial: int, nums: tuple[str, str], f_name: str, m_name: str, s_time: datetime.datetime) -> str:
    dir_path = (
        '../backLog/'
        + nums[0] + '_' + m_name + '/'
        + nums[1] + '_' + f_name + '/'
        + s_time.strftime('%Y%m%d_%H%M%S') + '/'
    )
    os.makedirs(dir_path, exist_ok=True)

    col = ['f1', 'f2', 'f3'] if f_name == "DTLZ1" else ['f1', 'f2']
    row = [str(r) for r in range(logger.LOG_FIT[-1].shape[0])]
    df = pd.DataFrame(logger.LOG_FIT[-1], index=row, columns=col)
    df.to_csv(os.path.join(dir_path, 'front_' + nums[0] + nums[1] + '_' + str(trial).zfill(3)) + '.csv')

    return dir_path


def write_trajectory(log_dir: str, func_name: str) -> None:
    col = ['f1', 'f2', 'f3'] if func_name == "DTLZ1" else ['f1', 'f2']
    rows = []
    for gen, fit_snapshot in enumerate(logger.LOG_TRAJ):
        for idx, point in enumerate(fit_snapshot):
            row = {'generation': gen, 'point_idx': idx}
            for k, c in enumerate(col):
                row[c] = point[k]
            rows.append(row)
    pd.DataFrame(rows).to_csv(os.path.join(log_dir, 'trajectory_best.csv'), index=False)


def write_record(csv_path: str, trial: int, start_time: datetime.datetime, names: tuple[str, str, str],
                 comment: str, processing_time: float, n_sub: int, *indicators: np.ndarray) -> None:
    row: dict[str, object] = {
        'year': start_time.year,
        'month': start_time.month,
        'day': start_time.day,
        'time': start_time.strftime('%H:%M:%S'),
        'func_name': names[0],
        'meth_name': names[1],
        'topo_name': names[2],
        'trial': trial,
        'comment': comment,
        'processing_time': processing_time,
        'n_sub': n_sub,
    }
    for i, indicator in enumerate(indicators):
        prefix = f'ind{i}'
        row[f'{prefix}_avg'] = np.average(indicator)
        row[f'{prefix}_max'] = np.max(indicator)
        row[f'{prefix}_min'] = np.min(indicator)
        row[f'{prefix}_median'] = np.median(indicator)
        row[f'{prefix}_argmax'] = f'No.{np.argmax(indicator) + 1}'
        row[f'{prefix}_argmin'] = f'No.{np.argmin(indicator) + 1}'

    write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    pd.DataFrame([row]).to_csv(csv_path, mode='a', header=write_header, index=False)
    print("Save Successed!")
