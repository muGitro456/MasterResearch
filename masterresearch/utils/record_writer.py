"""実験結果（パレートフロント座標・評価指標統計）を CSV に書き出すモジュール。

logger.py のグローバル変数（LOG_POS, LOG_VEL, LOG_FIT）を読み取って出力する。
"""
import datetime
import os

import numpy as np
import pandas as pd

from . import logger
from .paths import DEFAULT_OUTPUT_DIR


def write4plot(trial: int, nums: tuple[str, str], f_name: str, m_name: str, s_time: datetime.datetime,
                output_dir: str = DEFAULT_OUTPUT_DIR) -> str:
    """直近の試行で得られたパレートフロントを `front_*.csv` として出力する。

    出力先は `{output_dir}/{手法番号}_{手法名}/{関数番号}_{関数名}/{開始時刻}/` で、
    存在しなければ作成する。

    Args:
        trial: 試行番号（ファイル名のサフィックスに使用）。
        nums: `(手法番号, 関数番号)`。
        f_name: ベンチマーク関数名。
        m_name: 手法名。
        s_time: 実行開始時刻（出力ディレクトリ名に使用）。
        output_dir: 出力先ルートディレクトリ。

    Returns:
        作成した出力先ディレクトリのパス（末尾に `/` 付き）。
    """
    dir_path = os.path.join(
        output_dir,
        nums[0] + '_' + m_name,
        nums[1] + '_' + f_name,
        s_time.strftime('%Y%m%d_%H%M%S'),
    ) + '/'
    os.makedirs(dir_path, exist_ok=True)

    col = ['f1', 'f2', 'f3'] if f_name == "DTLZ1" else ['f1', 'f2']
    row = [str(r) for r in range(logger.LOG_FIT[-1].shape[0])]
    df = pd.DataFrame(logger.LOG_FIT[-1], index=row, columns=col)
    df.to_csv(os.path.join(dir_path, 'front_' + nums[0] + nums[1] + '_' + str(trial).zfill(3)) + '.csv')

    return dir_path


def write_trajectory(log_dir: str, func_name: str) -> None:
    """世代ごとのアーカイブ内評価値の推移を `trajectory_best.csv` として出力する。

    `logger.LOG_TRAJ` （`simulation.run_simulation` の追加実行で記録される）を
    世代・解インデックスごとに1行のロング形式に整形して書き出す。
    `tools/graph_drawer.py` のアニメーション表示の入力として使う。

    Args:
        log_dir: `write4plot` が返した出力先ディレクトリ。
        func_name: ベンチマーク関数名（列数の決定に使用）。
    """
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
    """1回の実行（`trial` 試行分）の概要を実行記録CSVに1行追記する。

    ファイルが存在しない、または空の場合はヘッダー行も書き込む。

    Args:
        csv_path: 実行記録CSVのパス。
        trial: 試行回数。
        start_time: 実行開始時刻。
        names: `(関数名, 手法名, トポロジー名)`。
        comment: 実行コメント。
        processing_time: 1試行あたりの平均処理時間 [s]。
        n_sub: サブ粒子群数（`N_SUB_SWARM`）。MASTER_C以外では未使用でも記録される。
        *indicators: 試行ごとの指標配列（可変長）。各指標について平均・最大・最小・
            中央値・最大/最小を取った試行番号を列として記録する。
    """
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

    dir_name = os.path.dirname(csv_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    pd.DataFrame([row]).to_csv(csv_path, mode='a', header=write_header, index=False)
    print("Save Successed!")
