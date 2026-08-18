"""PSO シミュレーションのコアロジック。"""
# Pythonパッケージのインポート
import datetime
import json
import time

import numpy as np
from tqdm import tqdm

import logger
import metrics
import record_writer
from field import Problem
from proposed import MASTER_A, MASTER_B, MASTER_C

# 自作パッケージのインポート
from related import FPOMOPSO, MOPSO, SENIOR

# VScodeでは文字選択→Ctrl+Shift+Pでコマンドパレット→upperと入力で大文字にできる"
sheet_name = "../プログラム実行記録管理シート.csv"

def main(instruction: str, trial: int = 100, comment: str = 'ただのテスト') -> None:
    TRIAL = trial       # 試行回数
    isDebugged = False  # 粒子の動きを確認したいか
    isPlotted = True    # パレートフロントの情報を記録したいか

    # JSONファイルのロード
    with open('./property/methods.json', 'r') as file1:
        meth_dict = json.load(file1)  # メソッドに関する辞書
    with open('./property/functions.json', 'r') as file2:
        func_dict = json.load(file2)  # ベンチマーク関数に関する辞書
    with open('./property/parameters.json', 'r') as file3:
        param_dict = json.load(file3)  # パラメータに関する辞書
    with open('./property/topologies.json') as file4:
        topo_dict = json.load(file4)  # トポロジーに関する辞書

    startTime = datetime.datetime.now()  # プログラムの開始時間

    if len(instruction) == 3:  # MASTER_BまたはMASTER_Cメソッドを使用するのであれば
        METH_NUM, FUNC_NUM, TOPO_NUM = instruction[0], instruction[1], instruction[2]  # メソッド番号、関数番号、トポロジー番号の３つに分離する
    else:
        METH_NUM, FUNC_NUM = instruction[0], instruction[1]  # メソッド番号と関数番号の２つに分離する
        if METH_NUM == "4":  # MASTER_Aメソッドであれば
            TOPO_NUM = "1"  # リングトポロジー(近傍数5)
        else:
            TOPO_NUM = "0"  # トポロジーなし

    METH_NAME = meth_dict[METH_NUM]["name"]  # 使用メソッドの名前
    TOPO_NAME = topo_dict[TOPO_NUM]["name"]  # トポロジーの名前

    FUNC_NAME = func_dict[FUNC_NUM]["name"]  # 関数の名前
    problem = Problem(func_dict[FUNC_NUM])   # テスト問題を生成

    numOfGBs = np.zeros(TRIAL)  # アーカイブに保存されたGBの個数
    cr = np.zeros(TRIAL)        # 被覆率
    print("Start time:", startTime.strftime('%Y/%m/%d %H:%M:%S'))
    print("Method    : ", METH_NAME)
    print("Function  : ", FUNC_NAME)
    print("Topology  : ", TOPO_NAME)

    if METH_NUM == "6":
        print("N_SUBSWARM: ", param_dict["N_SUB_SWARM"])

    processing_time = np.zeros(TRIAL)
    log_dir = ""
    _algorithm_map: dict[str, type] = {
        "MOPSO": MOPSO, "FPOMOPSO": FPOMOPSO, "SENIOR": SENIOR,
        "MASTER_A": MASTER_A, "MASTER_B": MASTER_B, "MASTER_C": MASTER_C,
    }
    for t in tqdm(range(TRIAL), desc="Trial     "):
        if int(METH_NUM) <= 3:
            algorithm = _algorithm_map[METH_NAME](param_dict, problem)
        else:
            algorithm = _algorithm_map[METH_NAME](param_dict, problem, topo_dict[TOPO_NUM])

        start = time.time()
        archive = algorithm.simulation()
        processing_time[t] = time.time() - start

        numOfGBs[t] = archive.fit_gb.shape[0]
        cr[t] = archive.calc_cover_rate(archive.fit_gb.shape[0])

        if isDebugged:  # pragma: no cover
            logger.write4debug('p', param_dict["GENERATION_MAX"], METH_NUM, METH_NAME)
            logger.write4debug('v', param_dict["GENERATION_MAX"], METH_NUM, METH_NAME)

        if isPlotted:
            log_dir = record_writer.write4plot(t + 1, (METH_NUM, FUNC_NUM), FUNC_NAME, METH_NAME, startTime)

    print("Finished!!")
    processing_time_ave = float(np.average(processing_time))
    print("平均実行時間は{}[s]".format(processing_time_ave))
    if isPlotted and log_dir:
        # 追加実行して軌跡を記録
        logger.reset_log()
        best_algorithm = _algorithm_map[METH_NAME](
            param_dict, problem, topo_dict[TOPO_NUM]
        ) if int(METH_NUM) > 3 else _algorithm_map[METH_NAME](param_dict, problem)
        best_algorithm.simulation()
        record_writer.write_trajectory(log_dir, FUNC_NAME)
        print(f"Trajectory saved to {log_dir}trajectory_best.csv")
    if isPlotted:
        metrics.evaluation(log_dir, numOfGBs, cr)
    record_writer.write_record(sheet_name, TRIAL, startTime, (FUNC_NAME, METH_NAME, TOPO_NAME), comment, processing_time_ave, param_dict["N_SUB_SWARM"], numOfGBs, cr)

def file_is_locked(filepath: str) -> bool:
    try:
        f = open(filepath, 'a')
        f.close()
    except OSError:
        return True
    else:
        return False

if __name__ == "__main__":  # pragma: no cover
    if not file_is_locked(sheet_name):
        instruction_set = ["691"]
        #instruction_set = ["27", "37", "47", "572", "573", "574", "575"]
        #instruction_set = ["515", "525", "535", "545", "555", "565"]
        #instruction_set = ["41", "42", "43", "44", "45", "46"]

        for instruction in instruction_set:
            main(instruction)
    else:
        print("ERROR: {} がロックされています。閉じてから実行してください".format(sheet_name))
