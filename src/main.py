# Pythonパッケージのインポート
import numpy as np
import datetime, sys, json, requests, time, os
from tqdm import tqdm

# 自作パッケージのインポート
from related import MOPSO, FPOMOPSO, SENIOR
from proposed import MASTER_A, MASTER_B, MASTER_C
from field import Problem
import logger
import metrics
import record_writer

# VScodeでは文字選択→Ctrl+Shift+Pでコマンドパレット→upperと入力で大文字にできる"
sheet_name = "../プログラム実行記録管理シート.xlsx"  # Excelシートの名前

def main(instruction):
    TRIAL = 100         # 試行回数
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
    args = sys.argv  # コマンドライン引数
    
    if "-C" in args:  # -C が入力されていれば
        comment = args[args.index("-C")+1]  # その次の引数をコメントとして記録する
    else:
        comment = "ただのテスト"
    
    if len(instruction) == 3:  # MASTER_BまたはMASTER_Cメソッドを使用するのであれば
        METH_NUM, FUNC_NUM, TOPO_NUM = instruction  # メソッド番号、関数番号、トポロジー番号の３つに分離する
    else:
        METH_NUM, FUNC_NUM = instruction  # メソッド番号と関数番号の２つに分離する
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
    for t in tqdm(range(TRIAL), desc="Trial     "):
        if int(METH_NUM) <= 3:
            algorithm = eval(METH_NAME)(param_dict, problem)
        else:
            algorithm = eval(METH_NAME)(param_dict, problem, topo_dict[TOPO_NUM])

        start = time.time()
        archive = algorithm.simulation()
        processing_time[t] = time.time() - start

        numOfGBs[t] = archive.fit_gb.shape[0]
        cr[t] = archive.calc_cover_rate(archive.fit_gb.shape[0])

        if isDebugged:
            logger.write4debug('p', param_dict["GENERATION_MAX"], METH_NUM, METH_NAME)
            logger.write4debug('v', param_dict["GENERATION_MAX"], METH_NUM, METH_NAME)

        if isPlotted:
            log_dir = record_writer.write4plot(t + 1, (METH_NUM, FUNC_NUM), FUNC_NAME, METH_NAME, startTime)

    print("Finished!!")
    processing_time_ave = np.average(processing_time)
    print("平均実行時間は{}[s]".format(processing_time_ave))
    if isPlotted:
        metrics.evaluation(log_dir, numOfGBs, cr)
    record_writer.write_record(sheet_name, TRIAL, startTime, (FUNC_NAME, METH_NAME, TOPO_NAME), comment, processing_time_ave, param_dict["N_SUB_SWARM"], numOfGBs, cr)

# PythonからLINEへ通知を送る関数
# 参考にしたサイト: https://hiyokonoko.com/%E3%80%90%E5%88%9D%E5%BF%83%E8%80%85%E5%90%91%E3%81%91%E3%80%9110%E5%88%86%E3%81%A7%E3%81%A7%E3%81%8D%E3%82%8B%EF%BC%81python%E3%81%AE%E5%AE%9F%E8%A1%8C%E7%B5%90%E6%9E%9C%E3%82%92%E3%82%B9%E3%83%9E/862/
def line_notify(message):
    line_notify_token = os.environ.get("LINE_NOTIFY_TOKEN") # アクセストークン
    line_notify_api = 'https://notify-api.line.me/api/notify'
    payload = {'message': message} # 引数として自由に入力することができます
    headers = {'Authorization': 'Bearer ' + line_notify_token}
    requests.post(line_notify_api, data=payload, headers=headers)

# ファイルを追記モードで開けるかチェックする関数
def xlsx_is_open(filepath: str) -> bool:
    try:
        f = open(filepath, 'a')
        f.close()
    except:
        return True
    else:
        return False

if __name__ == "__main__":
    if not xlsx_is_open(sheet_name):
        instruction_set = ["691"]
        #instruction_set = ["27", "37", "47", "572", "573", "574", "575"]
        #instruction_set = ["515", "525", "535", "545", "555", "565"]
        #instruction_set = ["41", "42", "43", "44", "45", "46"]

        for instruction in instruction_set:
            main(instruction)
        text = "\nプログラムの実行を完了しました\n結果を確認してください"
        line_notify(text)
    else:
        print("ERROR: {}を閉じてから実行してください".format(sheet_name))