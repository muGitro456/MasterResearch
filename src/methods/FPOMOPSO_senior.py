import numpy as np
import sys
sys.path.append('../')
from tools import database as db
from . import MOPSO, FPOMOPSO

def fpo_mopso_senior(params, multiObj):
    # パラメータ設定
    N = params[0] # 粒子数
    MOPSO.setNAMAX(params[1]) # アーカイブ保存上限数
    MAXGEN = params[2] # 最大世代数
    W = params[3] # 慣性項
    C1 = params[4] # 自己認識項
    C2 = params[5] # 社会認識項

    fun = multiObj[0] # 目的関数
    D = multiObj[1] # 次元数
    var_max = multiObj[2] # 探索空間の上界
    var_min = multiObj[3] # 探索空間の下界
    vel_min = np.zeros(D) # 最小速度

    # 粒子の初期化
    POS, VEL, POS_EVAL, PBEST, PBEST_EVAL = MOPSO.init_particle(N, fun, var_max, var_min)
    #SWARM_MOPSO = POS, VEL, POS_EVAL, PBEST, PBEST_EVAL

    # S1の複製
    SWARM_FPO = POS, POS_EVAL, PBEST, PBEST_EVAL

    # アーカイブの初期化
    ARC_MOPSO = MOPSO.makeParetoFront(POS, POS_EVAL)
    ARC_FPO = ARC_MOPSO
    ARC = ARC_MOPSO

    g = 1
    stopCondition = False
    while not stopCondition:
        GBEST_L = MOPSO.select_leader(ARC_MOPSO)

        # 粒子の移動
        VEL = W * VEL + C1 * np.random.rand(N, D) * (PBEST - POS) \
                        + C2 * np.random.rand(N, D) * (GBEST_L - POS)
        #POS = POS + VEL

        # 制約条件の確認
        POS, VEL = MOPSO.checkBoundaries(POS, VEL, var_max, var_min, vel_min)

        POS_EVAL = fun(POS).T

        PBEST = MOPSO.update_PBEST(POS, POS_EVAL, PBEST, PBEST_EVAL)
        PBEST_EVAL = fun(PBEST).T

        # アーカイブの更新
        mopsoFront = MOPSO.makeParetoFront(POS, POS_EVAL)
        ARC_MOPSO = MOPSO.update_archive(ARC_MOPSO, mopsoFront)

        # FPOの処理
        SWARM_FPO = fpo_senior(g, params, multiObj, SWARM_FPO)
        fpoFront = MOPSO.makeParetoFront(SWARM_FPO[0], SWARM_FPO[1])
        ARC_FPO = MOPSO.update_archive(ARC_FPO, fpoFront)

        # 二つのアーカイブの統合
        POS_COMB = np.vstack([ARC_MOPSO[0], ARC_FPO[0]])
        POS_EVAL_COMB = np.vstack([ARC_MOPSO[1], ARC_FPO[1]])
        ARC_COMB = MOPSO.makeParetoFront(POS_COMB, POS_EVAL_COMB)

        # アーカイブの更新
        combFront = MOPSO.makeParetoFront(ARC_COMB[0], ARC_COMB[1])
        ARC = MOPSO.update_archive(ARC, combFront)

        print("SENIOR:g = {:3}, GBest = {:3}".format(g, ARC[1].shape[0]))
        # 終了条件の判定
        g = g + 1
        if g > MAXGEN:
            stopCondition = True
    
    return ARC

def fpo_senior(gen, params, multiObj, swarm):
    POS, POS_EVAL, PBEST, PBEST_EVAL = swarm
    N, MAXGEN, C3, W_INI, W_END, C4 = params[0], params[2], params[6], params[7], params[8], params[9]
    fun, D, var_max, var_min = multiObj
    vel_min = np.zeros(D) # 最小速度

    W_FPO = (W_INI - W_END) * ((MAXGEN - gen) / MAXGEN) + W_END
    NEW_POS = POS
    NEW_POS_EVAL = POS_EVAL
    NEW_PBEST = PBEST
    NEW_PBEST_EVAL = PBEST_EVAL
    FIT = FPOMOPSO.fitness(POS_EVAL)
    SUM_FIT = np.sum(FIT)
    
    NEIGHBORS = np.zeros((N, D))
    for i in range(N):
        neighbor = i
        if np.random.rand() < (FIT[i] / SUM_FIT):
            neighbors = np.array([k for k in range(N) if k != i])
            neighbor = np.random.choice(neighbors, 1)
        NEIGHBORS[i, :] = POS[neighbor, :]

    newVel = W_FPO * C3 * np.random.rand(N, D) * (NEIGHBORS - POS) \
        + C4 * np.random.rand(N, D) * (PBEST - POS)
    #NEW_POS = POS + newVel
    NEW_POS, newVel = MOPSO.checkBoundaries(NEW_POS, newVel, var_max, var_min, vel_min)
    NEW_POS_EVAL = fun(NEW_POS).T
    NEW_PBEST = MOPSO.update_PBEST(NEW_POS, NEW_POS_EVAL, NEW_PBEST, NEW_PBEST_EVAL)
    NEW_PBEST_EVAL = fun(NEW_PBEST).T

    return NEW_POS, NEW_POS_EVAL, NEW_PBEST, NEW_PBEST_EVAL