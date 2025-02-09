import numpy as np
from . import MOPSO

# グローバル変数
def setNAMAX(val):
    global Na_MAX
    Na_MAX = val

def getNAMAX():
    global Na_MAX
    return Na_MAX

def fpo_mopso(params, multiObj):
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

        # MOPSOアーカイブの更新
        mopsoFront = MOPSO.makeParetoFront(POS, POS_EVAL)
        ARC_MOPSO = MOPSO.update_archive(ARC_MOPSO, mopsoFront)
        #print("ARC_MOPSO = ", ARC_MOPSO)

        # FPOの処理
        #print("g={} FPO実行!".format(g))
        SWARM_FPO = fpo(g, params, multiObj, SWARM_FPO)

        # FPOアーカイブの更新
        fpoFront = MOPSO.makeParetoFront(SWARM_FPO[0], SWARM_FPO[1])
        ARC_FPO = MOPSO.update_archive(ARC_FPO, fpoFront)
        #print("ARC_FPO = ", ARC_FPO)

        # 二つのアーカイブの統合
        POS_COMB = np.vstack([ARC_MOPSO[0], ARC_FPO[0]])
        POS_EVAL_COMB = np.vstack([ARC_MOPSO[1], ARC_FPO[1]])
        ARC_COMB = MOPSO.makeParetoFront(POS_COMB, POS_EVAL_COMB)
        #print("ARC_COMB = ", ARC_COMB)

        # 全体アーカイブの更新
        combFront = MOPSO.makeParetoFront(ARC_COMB[0], ARC_COMB[1])
        ARC = MOPSO.update_archive(ARC, combFront)
        #print("ARC = ", ARC)

        print("FPO-MOPSO:g = {:3}, GBest = {:3}".format(g, ARC[1].shape[0]))
        # 終了条件の判定
        g = g + 1
        if g > MAXGEN:
            stopCondition = True
    
    return ARC

def fpo(gen, params, multiObj, swarm):
    POS, POS_EVAL, PBEST, PBEST_EVAL = swarm
    N, MAXGEN, C3, W_INI, W_END = params[0], params[2], params[6], params[7], params[8]
    fun, D, var_max, var_min = multiObj
    vel_min = np.zeros(D) # 最小速度

    W_FPO = (W_INI - W_END) * ((MAXGEN - gen) / MAXGEN) + W_END
    NEW_POS = POS
    NEW_POS_EVAL = POS_EVAL
    NEW_PBEST = PBEST
    NEW_PBEST_EVAL = PBEST_EVAL
    FIT = fitness(POS_EVAL)
    SUM_FIT = np.sum(FIT)
    
    """
    for i in range(N):
        if np.random.rand() < (FIT[i] / SUM_FIT) * np.random.rand():
            neighbors = np.array([k for k in range(N) if k != i])
            neighbor = np.random.choice(neighbors, 1)
            newVel = W_FPO * C3 * np.random.rand(1, D) * (pos[neighbor, :] - pos[i, :])
            newPos[i, :] = pos[i, :] + newVel
            
            newPos[i, :] = checkBoundaries_fpo(newPos[i,:],newVel,var_max,var_min,vel_min)
            
            print(newPos[i, :])
            newPosEval[i, :] = fun(newPos[i, :]).T

            newPb[i, :] = MOPSO.update_PBEST(newPos[i,:], newPosEval[i, :], pbest, pbestEval)
            newPbEval[i, :] = fun(newPb[i,:]).T
    """
    NEIGHBORS = np.zeros((N, D))
    for i in range(N):
        neighbor = i
        if np.random.rand() < (FIT[i] / SUM_FIT) * np.random.rand():
            neighbors = np.array([k for k in range(N) if k != i])
            neighbor = np.random.choice(neighbors, 1)
        NEIGHBORS[i, :] = POS[neighbor, :]

    newVel = W_FPO * C3 * np.random.rand(N, D) * (NEIGHBORS - POS)
    #NEW_POS = POS + newVel
    NEW_POS, newVel = MOPSO.checkBoundaries(NEW_POS, newVel, var_max, var_min, vel_min)
    NEW_POS_EVAL = fun(NEW_POS).T
    NEW_PBEST = MOPSO.update_PBEST(NEW_POS, NEW_POS_EVAL, NEW_PBEST, NEW_PBEST_EVAL)
    NEW_PBEST_EVAL = fun(NEW_PBEST).T

    return NEW_POS, NEW_POS_EVAL, NEW_PBEST, NEW_PBEST_EVAL
            
# 粒子の適応度を計算する関数
def fitness(posEval):
    (N, K) = posEval.shape # ローカル変数
    FIT = np.zeros(N)
    for i in range(N):
        for k in range(K):
            FIT[i] = FIT[i] + (posEval[i, k] / (np.max(posEval[:, k]) - np.min(posEval[:, k])))
        #print("FITNESS[{}] = {}".format(i, FIT[i]))
    FIT = 1 / FIT
    return FIT

"""
def checkBoundaries_fpo(pos, vel, var_max, var_min, vel_min):
    pos[pos > var_max] = var_max[pos > var_max]
    pos[pos < var_min] = var_min[pos < var_min]
    #vel[pos > var_max] = vel_min[pos > var_max]
    #vel[pos < var_min] = vel_min[pos < var_min]
    return pos
"""    