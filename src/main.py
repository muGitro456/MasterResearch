import numpy as np
import matplotlib.pyplot as plt
import json, datetime, sys, time

from methods.MOPSO import mopso as MOPSO
from methods.FPOMOPSO import fpo_mopso as FPO_MOPSO
from methods.FPOMOPSO_senior import fpo_mopso_senior as SENIOR
from methods.FPOMOPSO_master import fpo_mopso_master as MASTER
from methods.FPOMOPSO_master_C import fpo_mopso_master_C as MASTER_C
from tools import database as db
from tools import resultsManager as rm

TRIAL = 100 # 試行回数
"""
meth_dict = {
    "1":{"name":"MOPSO", "title":"MOPSO"}, 
    "2":{"name":"FPO_MOPSO", "title":"FPO MOPSO"},
    "3":{"name":"SENIOR", "title":"Senior Method"},
    "4":{"name":"MASTER", "title":"Proposed Method A"}
}
func_dict = {
    "1":{"name":"Rastrigin", "dimension":10}, 
    "2":{"name":"Ackley", "dimension":10},
    "3":{"name":"Griewank", "dimension":10},
    "4":{"name":"Sphere", "dimension":10},
    "5":{"name":"Booth", "dimension":10},
    "6":{"name":"Alpine", "dimension":10}
}

python .\src\main.py メソッド番号関数番号 と入力. 
(ex) python .\src\main.py 41 : メソッド"MASTER"で関数"Rastrigin"を実行
"""

processing_time = np.zeros(TRIAL) # 各試行における実行時間を格納する配列

def simulation(trial, numbers):
    with open('./src_ver2/property/methods.json', 'r') as file1:
        meth_dict = json.load(file1)
    with open('./src_ver2/property/functions.json', 'r') as file2:
        func_dict = json.load(file2)
    with open('./src_ver2/property/parameters.json', 'r') as file3:
        param_dict = json.load(file3)
    
    METH_NUM, FUNC_NUM = numbers  # メソッド番号, 関数番号(str型)
    METH_NAME = meth_dict[METH_NUM]["name"] # メソッドの名前
    FUNC_NAME = func_dict[FUNC_NUM]["name"] # 関数の名前
    
    params = init_parameters()
    multiObj = select_MOPs(FUNC_NAME, dim = func_dict[FUNC_NUM]["dimension"])
    
    # 2023-09-21 追記：時間計測のコードを記入.
    start = time.time()
    archive = eval(METH_NAME)(params[int(METH_NUM)-1], multiObj) # eval(文字列)で, 文字列を関数名にみなすという処理ができる
    #archive = MASTER(params[int(METH_NUM)-1], multiObj)
    processing_time[trial-1] = time.time() - start
    
    #archive = eval(METH_NAME)(param_dict, multiObj)
    #plot_archive(archive[1], FUNC_NAME, method_dict[str(METH_NUM)]["title"])
    cr = rm.cover_rate(archive[1], archive[1].shape[0])

    print("Method : ", METH_NAME)
    print("Multi Function : ", FUNC_NAME)
    print("Number of Solutions : ", len(archive[1]))
    print("Cover Rate : ", cr)
    
    # 粒子の動きを見たいときだけ(ファイルサイズがデカいから)
    #db.write4Debug('p', params[int(METH_NUM)][2], METH_NUM, METH_NAME)
    #db.write4Debug('v', params[int(METH_NUM)][2], METH_NUM, METH_NAME)

    global startTime
    db.write4Plot(trial, numbers, FUNC_NAME, METH_NAME, startTime)

def init_parameters():
    """
    パラメータを設定する関数
    """
    N = 100 # 粒子数
    Na_MAX = int(1.5 * N) # アーカイブ保存上限数
    MAXGEN = 200 # 最大世代数
    W = 0.9 # 慣性項
    C1 = 2.0 # 自己認識項
    C2 = 2.0 # 社会認識項
    params_MOPSO = N, Na_MAX, MAXGEN, W, C1, C2

    C3 = 2.0 # 他己認識項
    W_INI = 0.9 # 慣性項の初期値
    W_END = 0.4 # 慣性項の終了値
    params_FPO_MOPSO = params_MOPSO + (C3, W_INI, W_END)

    C4 = 2.0 # 自己認識項(卒研)
    params_SENIOR = params_FPO_MOPSO + (C4,) # 要素数が1のタプルには,が必要

    N_SIZE = 5 # 近傍サイズ
    params_MASTER = params_SENIOR + (N_SIZE, )

    N_SUBSWARM = 10 # サブ粒子群の総数
    params_MASTER_C = params_MASTER + (N_SUBSWARM, )

    return params_MOPSO, params_FPO_MOPSO, params_SENIOR, params_MASTER, params_MASTER, params_MASTER_C

def select_MOPs(funcName, dim) -> tuple:
    match funcName:
        case "Rastrigin": # Rastrigin関数の場合
            A = lambda x : np.sum(x[:, 1:] ** 2, axis=1)
            B = lambda x : - 10 * np.sum(np.cos(2 * np.pi * x[:, 1:]), axis=1)
            F = lambda x : 10 * dim + A(x) + B(x)
            upper = np.array([5.12 for d in range(dim)])
        
        case "Ackley": # Ackley関数の場合
            A = lambda x : -0.2 * np.sqrt((1.0 / dim) * np.sum(x[:, 1:] ** 2, axis = 1))
            B = lambda x : (1.0 / dim) * np.sum(np.cos(2 * np.pi * x[:, 1:]), axis=1)
            F = lambda x : 20 - 20 * np.exp(A(x)) + np.e - np.exp(B(x))
            #upper = np.array([32.768 for d in range(dim)])
            upper = np.array([5.0 for d in range(dim)])
        
        case "Griewank": # Griewank関数の場合
            A = lambda x : (1.0 / 4000.0) * np.sum(x[:, 1:] ** 2, axis = 1)
            w = np.array([1.0 / np.sqrt(k + 1) for k in range(dim)])
            B = lambda x : - np.prod(np.cos(x[:, 1:] * w), axis=1)
            F = lambda x : 1 + A(x) + B(x)
            #upper = np.array([600.0 for d in range(dim)])
            upper = np.array([5.0 for d in range(dim)])
        
        case "Sphere":
            F = lambda x : np.sum(x[:, 1:]**2, axis=1)
            upper = np.array([5.0 for d in range(dim)])
        
        case "Golden":
            A = lambda x : (x[:, 1] + x[:, 2] + 1) ** 2
            B = lambda x : 19 - 14*x[:, 1] + 3*(x[:, 1]**2) - 14*x[:, 2] + 6*x[:, 1]*x[:, 2] + 3*(x[:, 2])**2
            C = lambda x : (2*x[:, 1] - 3*x[:, 2])**2
            D = lambda x : 18 - 32*x[:, 1] + 12*(x[:, 1])**2 + 48*x[:, 2] - 36*x[:, 1]*x[:, 2] + 27*(x[:, 2])**2
            F = lambda x : (1 + A(x) * B(x)) * (30 + C(x) * D(x)) - 3
            upper = np.array([2.0 for d in range(dim)])
        
        case "Booth":
            F = lambda x : (x[:, 1] + 2*x[:, 2] - 7)**2 + (2*x[:, 1] + x[:, 2] - 5)**2
            upper = np.array([10.0 for d in range(dim)])
        
        case "Alpine":
            F = lambda x : np.sum(np.abs(x[:, 1:] * np.sin(x[:, 1:]) + 0.1 * x[:, 1:]))
            upper = np.array([10.0 for d in range(dim)])
        
        case "Eggholder":
            A = lambda x : np.sqrt(np.abs(x[:, 2] + 0.5*x[:, 1] + 47))
            B = lambda x : np.sqrt(np.abs(x[:, 1] - (x[:, 2] + 47)))
            F = lambda x : -(x[:, 2] + 47) * np.sin(A(x)) - x[:, 1] * np.sin(B(x))
            upper = np.array([512.0 for d in range(dim)])
        
        case _: # defaultの場合
            print("ERROR")
            return -1
    
    f = lambda x : x[:, 0]
    g = lambda x : 1 + F(x)
    h = lambda x : 1 - np.sqrt(f(x) / g(x))
    obj_fun = lambda x : np.array([f(x), g(x) * h(x)])
    var_max = np.append(np.ones(1), upper)
    var_min = np.append(np.zeros(1), (-1) * upper)

    return obj_fun, dim + 1, var_max, var_min

# アーカイブ内のパレートフロントを表示する関数
def plot_archive(front, funcName, gName):
    plt.scatter(front[:, 0], front[:, 1], c="red")
    plt.grid()
    plt.xlabel("f1")
    plt.ylabel("f2")
    str_title = "GBest in Archive by " + gName
    plt.title(str_title)

    match funcName:
        case "Ackley":
            plt.ylim([0, np.max(front[:, 1]) + 1])
        case "Griewank":
            plt.ylim([0, np.max(front[:, 1]) + 1])
        case "Rastrigin":
            plt.ylim([0, np.max(front[:, 1]) + 1])
        case _:
            plt.ylim([0, np.max(front[:, 1]) + 1])
    
    """
    new_dir_path_graph = 'graphs' + '/' + methodName + '/' + funcName + '/' + now.strftime('%Y%m%d')
    os.makedirs(new_dir_path_graph, exist_ok=True)
    figName = methodName + '_' + funcName + '_' + 'front_' + now.strftime('%Y%m%d_%H%M%S') + '_' + str(trial) + '.png'
    plt.savefig(os.path.join(new_dir_path_graph, figName))
    """
    #plt.show()

if __name__ == "__main__":
    global startTime
    startTime = datetime.datetime.now()
    args = sys.argv

    for t in range(TRIAL):
        print("Trial #", t+1)
        simulation(t+1, numbers=args[1])
    
    print("Finished!!")
    processing_time_ave = np.average(processing_time)
    print("平均実行時間は{}[s]".format(processing_time_ave))