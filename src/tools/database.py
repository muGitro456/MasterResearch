import numpy as np
import pandas as pd
import os

LOG_POS = []
LOG_VEL = []
LOG_EVAL = []

def store(var, target):
    match target:
        case 'p':
            LOG_POS.append(var)
        case 'v':
            LOG_VEL.append(var)
        case 'e':
            LOG_EVAL.append(var)
        case _:
            print("該当なし")
            return -1

def write4Debug(target, maxgen, mNum, mName):
    # 新しいディレクトリの作成
    new_dir_path = 'backLog/' + mNum + '_' + mName + '/'
    os.makedirs(new_dir_path, exist_ok=True)

    match target:
        case 'p':
            col = ['x' + str(d) for d in range(LOG_POS[0].shape[1])]
            row = [str(d % LOG_POS[0].shape[0]) for d in range(LOG_POS[0].shape[0] * maxgen)]
            tmp = np.array(LOG_POS) # listをnumpy.ndarrayに変換
            tmp = (tmp.flatten()).reshape(LOG_POS[0].shape[0] * maxgen, LOG_POS[0].shape[1]).copy() # copy()を付けて値を反映!

            df = pd.DataFrame(tmp, index=row, columns=col)
            df.to_csv(os.path.join(new_dir_path,  mName + '_pos_SP.csv'), header=True, index=True)
        case 'v':
            col = ['v' + str(d) for d in range(LOG_VEL[0].shape[1])]
            row = [str(d % LOG_VEL[0].shape[0]) for d in range(LOG_VEL[0].shape[0] * maxgen)]
            tmp = np.array(LOG_VEL) # listをnumpy.ndarrayに変換
            tmp = (tmp.flatten()).reshape(LOG_VEL[0].shape[0] * maxgen, LOG_VEL[0].shape[1]).copy() # copy()を付けて値を反映!

            df = pd.DataFrame(tmp, index=row, columns=col)
            df.to_csv(os.path.join(new_dir_path, mName + '_vel_SP.csv'), header=True, index=True)
        case _:
            print("Error : database")
            return -1

def write4Plot(trial, nums, fName, mName, sTime):
    new_dir_path_log = 'backLog/' + nums[0] + '_' + mName + '/' + nums[1] + '_' + fName + '/' + sTime.strftime('%Y%m%d')
    os.makedirs(new_dir_path_log, exist_ok=True)

    col = ['f1', 'f2']
    row = [str(r) for r in range(LOG_EVAL[-1].shape[0])]
    df = pd.DataFrame(LOG_EVAL[-1], index=row, columns=col)
    df.to_csv(os.path.join(new_dir_path_log, 'front_' + sTime.strftime('%Y%m%d_%H%M%S') + '_' + str(trial).zfill(3)) + '.csv')