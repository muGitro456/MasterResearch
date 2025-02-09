import numpy as np
import sys
sys.path.append('../')
from tools import database as db
from . import MOPSO, FPOMOPSO_senior

# 提案手法Cのプログラム。サブ粒子群の関係を表す行列を追加する？

def fpo_mopso_master_C(params, multiObj):
    # パラメータ設定
    N = params[0] # 粒子数
    MOPSO.setNAMAX(params[1]) # アーカイブ保存上限数
    MAXGEN = params[2] # 最大世代数
    W = params[3] # 慣性項
    C1 = params[4] # 自己認識項
    C2 = params[5] # 社会認識項
    N_SIZE = params[10] # 近傍サイズ
    N_SUBSWARM = params[11] # サブ粒子群の総数
    N_SUBPARTICLES = N // N_SUBSWARM  # サブ粒子群を構成する粒子の総数

    fun = multiObj[0] # 目的関数
    D = multiObj[1] # 次元数
    var_max = multiObj[2] # 探索空間の上界
    var_min = multiObj[3] # 探索空間の下界
    vel_min = np.zeros(D) # 最小速度
    vel_max = (var_max - var_min) / 2 # 最大速度
    V_INI = (var_max - var_min) / 2
    V_END = (var_max - var_min) / 5
    
    # 粒子の初期化
    POS, VEL, POS_EVAL, PBEST, PBEST_EVAL = MOPSO.init_particle(N, fun, var_max, var_min)
    #SWARM_MOPSO = POS, VEL, POS_EVAL, PBEST, PBEST_EVAL

    # トポロジーの初期化
    TOPOLOGIES = init_topologies(N_SUBSWARM, N_SIZE)
    #print(TOPOLOGIES)

    # S1の複製
    SWARM_FPO = POS, POS_EVAL, PBEST, PBEST_EVAL

    # アーカイブの初期化
    ARC_MOPSO = MOPSO.makeParetoFront(POS, POS_EVAL)
    ARC_FPO = ARC_MOPSO
    ARC = ARC_MOPSO

    # サブアーカイブの初期化関数作る
    """
    ARC_SUB = () # 空のタプル
    for i in range(N):
        RET = init_subArchive(POS, POS_EVAL, TOPOLOGIES[i])
        ARC_SUB = ARC_SUB + (RET, )
    """
    #print("ARC_SUB[0][0][0]:", ARC_SUB[0][0][0])
    # ARC_SUB[IDX][KIND][IDX_ARC, DIMENSION]
    # IDX:何番目のアーカイブか. KIND:POSなら0, POS_EVALなら1.
    # IDX_ARC:アーカイブ内で何番目の粒子か. DIMENSION:何列目か.
    ARC_SUB = [None] * N_SUBSWARM
    for i in range(N_SUBSWARM):
        ARC_SUB[i] = init_subArchive(POS, POS_EVAL, TOPOLOGIES[i], N_SUBPARTICLES)      
    #print(type(ARC_SUB))

    g = 1
    stopCondition = False
    COLLISION = []
    while not stopCondition:
        GBEST_L = MOPSO.select_leader(ARC_MOPSO)
        LBEST = select_LBEST(ARC_SUB, TOPOLOGIES, POS_EVAL)

        # 粒子の移動
        for i in range(N):
            VEL[i] = W * VEL[i] + C1 * np.random.rand(D) * (PBEST[i] - POS[i]) \
                                + C2 * np.random.rand(D) * (LBEST[i // N_SUBSWARM] - POS[i])\
                                + C2 * np.random.rand(D) * (GBEST_L - POS[i])
            POS[i] = POS[i] + VEL[i]
        #VEL = np.around(VEL, 3)

        # 制約条件の確認
        #POS, VEL = MOPSO.checkBoundaries(POS, VEL, var_max, var_min, vel_min)
        POS, VEL, collision = MOPSO.checkBoundaries_new(POS, VEL, var_max, var_min)

        vel_max_2 = V_INI * np.exp(((g-1) / MAXGEN) * np.log(V_END / V_INI))
        #print("maxVel = ", vel_max_2)
        VEL = MOPSO.speedometer(VEL, g, MAXGEN, V_INI, V_END)
        #print("POS[0] = ", POS)
        #print("VEL[0] = ", VEL)
        db.store(POS, 'p')
        db.store(VEL, 'v')

        POS_EVAL = fun(POS).T

        PBEST = MOPSO.update_PBEST(POS, POS_EVAL, PBEST, PBEST_EVAL)
        PBEST_EVAL = fun(PBEST).T

        # サブアーカイブの更新
        for i in range(N_SUBSWARM):
            ARC_SUB[i] = update_sub_archive(ARC_SUB[i], POS, POS_EVAL, TOPOLOGIES[i], N_SUBPARTICLES)
        # サブアーカイブを一つに統合する
        mopsoFront = union_front(ARC_SUB)
        ARC_MOPSO = MOPSO.update_archive(ARC_MOPSO, mopsoFront)

        # FPOの処理
        SWARM_FPO = FPOMOPSO_senior.fpo_senior(g, params, multiObj, SWARM_FPO)
        fpoFront = MOPSO.makeParetoFront(SWARM_FPO[0], SWARM_FPO[1])
        ARC_FPO = MOPSO.update_archive(ARC_FPO, fpoFront)

        # 二つのアーカイブの統合
        POS_COMB = np.vstack([ARC_MOPSO[0], ARC_FPO[0]])
        POS_EVAL_COMB = np.vstack([ARC_MOPSO[1], ARC_FPO[1]])
        ARC_COMB = MOPSO.makeParetoFront(POS_COMB, POS_EVAL_COMB)

        # アーカイブの更新
        combFront = MOPSO.makeParetoFront(ARC_COMB[0], ARC_COMB[1])
        ARC = MOPSO.update_archive(ARC, combFront)

        print("MASTER:g = {:3}, GBest = {:3}, COL = {:3}".format(g, ARC[1].shape[0],collision))
        db.store(ARC[1], 'e')
        COLLISION.append(collision)

        # 終了条件の判定
        g = g + 1
        if g > MAXGEN:
            stopCondition = True
            #print("壁に沿っていた粒子の平均(個/世代) ", np.sum(COLLISION)/MAXGEN)
        
    return ARC

def init_topologies(N, N_SIZE):
    topologies = np.zeros((N, N_SIZE))
    idx_particle = np.arange(0, N)
    for i in range(N):
        for m in range(N_SIZE):
            topologies[i, m] = (i + idx_particle[m - (N_SIZE // 2)]) % N
    return topologies

# topology:1行N_SIZE列の行列
def init_subArchive(pos, posEval, topology, N_SUBPARTICLES):
    subArc_pos = np.empty((len(topology) * N_SUBPARTICLES, pos.shape[1]))
    subArc_posEval = np.empty((len(topology) * N_SUBPARTICLES, posEval.shape[1]))
    
    # 2023/10/16　変更 サブ粒子を構成に加える処理を追加
    for m in range(len(topology)):
        for i in range(N_SUBPARTICLES):
            subArc_pos[m * N_SUBPARTICLES + i, :] = pos[int(topology[m]) * N_SUBPARTICLES + i, :]
            subArc_posEval[m * N_SUBPARTICLES + i, :] = posEval[int(topology[m]) * N_SUBPARTICLES + i, :]
    
    return MOPSO.makeParetoFront(subArc_pos, subArc_posEval)
    
def select_LBEST(subarc, topologies, posEval):
    N = len(subarc)
    D = subarc[0][0].shape[1]
    #print("N , D = {}, {}".format(N, D)) 100,4
    LBEST = np.zeros((N, D))

    # トポロジーに基づいてシグマ法によりLBESTを決定する
    for i in range(N):
        front_temp = union_archive(i, subarc, topologies)
        """
        arc_temp = subarc[int(topologies[i, 0])]
        front_temp = MOPSO.makeParetoFront(arc_temp[0], arc_temp[1])
        print("front_temp = ", front_temp)
        for m in range(1, topologies.shape[1]):
            print("subarc[{}][0] = {}".format(int(topologies[i, m]), subarc[int(topologies[i, m])][0]))
            print("subarc[{}][1] = {}".format(int(topologies[i, m]), subarc[int(topologies[i, m])][1]))
            front_temp = MOPSO.update_archive(front_temp, (subarc[int(topologies[i, m])][0], subarc[int(topologies[i, m])][1]))
            print("front_temp = ", front_temp)
        """
        #print("i = ", i)
        #LBEST[i, :] = sigma_method(front_temp, posEval[i])
        LBEST[i, :] = MOPSO.select_leader(front_temp)
        
    return LBEST

def update_sub_archive(subArc, pos, posEval, topology, N_SUBPARTICLES):
    subFront = init_subArchive(pos, posEval, topology, N_SUBPARTICLES)
    return MOPSO.update_archive(subArc, subFront)

def union_archive(i, subarc, topologies):
    #print("i = ", i)
    front_temp_pos = subarc[int(topologies[i, 0])][0]
    front_temp_posEval = subarc[int(topologies[i, 0])][1]
    #print("front_temp_pos = ", front_temp_pos)
    #print("front_temp_posEval = ", front_temp_posEval)

    for m in range(1, topologies.shape[1]):
        #print("m = ", m)
        front_temp_pos = np.vstack((front_temp_pos, subarc[int(topologies[i, m])][0]))
        front_temp_posEval = np.vstack((front_temp_posEval, subarc[int(topologies[i, m])][1]))
    
    #print("front_temp_pos = ", front_temp_pos)
    #print("front_temp_posEval = ", front_temp_posEval)
    unique_pos, indices = np.unique(front_temp_pos, axis = 0, return_index=True)
    #unique_posEval = np.unique(front_temp_posEval, axis = 0)
    unique_posEval = front_temp_posEval[indices]
    #print("unique_pos = ", unique_pos)
    #print("unique_posEval = ", unique_posEval)
    front_temp = MOPSO.makeParetoFront(unique_pos, unique_posEval)
    #print("front_temp = ", front_temp)

    return front_temp

def sigma_method(front, posEval):
    F = front[1]
    #print("F = ", F)
    sigma_front = (F[:, 0] ** 2 - F[:, 1] ** 2) / (F[:, 0] ** 2 + F[:, 1] ** 2)

    #print("sigma_front = {}".format(sigma_front))
    sigma_particle = (posEval[0] ** 2 - posEval[1] ** 2) / (posEval[0] ** 2 + posEval[1] ** 2)

    #print("sigma_particle = {}".format(sigma_particle))

    near = np.argmin(np.abs(sigma_particle - sigma_front))
    #print("near = ", near)
    return front[0][near, :]

def union_front(subArc):
    front_temp_pos = subArc[0][0]
    front_temp_posEval = subArc[0][1]
    #print("length subArc = ", len(subArc))
    for i in range(1, len(subArc)): # len(subArc) = N
        #print("i = ", i)
        front_temp_pos = np.vstack((front_temp_pos, subArc[i][0])) 
        front_temp_posEval = np.vstack((front_temp_posEval, subArc[i][1]))
    
    unique_pos, indices = np.unique(front_temp_pos, axis = 0, return_index=True)
    #unique_posEval = np.unique(front_temp_posEval, axis = 0) # 行の重複を無くす
    unique_posEval = front_temp_posEval[indices]
    #print("unique_pos = ", unique_pos)
    #print("unique_posEval = ", unique_posEval)
    front_temp = MOPSO.makeParetoFront(unique_pos, unique_posEval)
    #print("front_temp = ", front_temp)

    return front_temp