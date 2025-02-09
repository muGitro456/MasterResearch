import numpy as np
import sys, copy
sys.path.append('../')
from tools import database as db

# グローバル変数
def setNAMAX(val):
    global Na_MAX
    Na_MAX = val

def getNAMAX():
    global Na_MAX
    return Na_MAX

# メイン関数
def mopso(params, multiObj):
    # パラメータ設定
    N = params["N"] # 粒子数
    setNAMAX(params["N_ARCHIVE_MAX"]) # アーカイブ保存上限数
    MAXGEN = params["GENERATION_MAX"] # 最大世代数
    W = params["INERTIA"] # 慣性項
    C1 = params["SELF_AWARENESS"] # 自己認識項
    C2 = params["SOCIAL_AWARENESS"] # 社会認識項

    fun = multiObj[0] # 目的関数
    D = multiObj[1] # 次元数
    var_max = multiObj[2] # 探索空間の上界
    var_min = multiObj[3] # 探索空間の下界
    vel_min = np.zeros(D) # 最小速度
    vel_max = (var_max - var_min) / 2
    V_INI = (var_max - var_min) / 2
    V_END = (var_max - var_min) / 5
    
    # 粒子の初期化
    POS, VEL, POS_EVAL, PBEST, PBEST_EVAL = init_particle(N, fun, var_max, var_min)
    #print("POS = ", POS)
    #print("POS EVAL = ", POS_EVAL)

    # アーカイブの初期化 アーカイブにはパレートフロントに属している粒子の位置、評価値が入る
    #ARC = init_archive(POS, POS_EVAL)
    ARC = makeParetoFront(POS, POS_EVAL)
    #print("ARC[0] = ", ARC[0]) # pos
    #print("ARC[1] = ", ARC[1]) # eval

    g = 1 # 現在の世代数
    stopCondition = False # 終了条件
    while not stopCondition:
        # リーダーの選出
        GBEST_L = select_leader(ARC)
        #print("GBEST_L = ", GBEST_L)
        
        # 粒子の移動
        VEL = W * VEL + C1 * np.random.rand(N, D) * (PBEST - POS) \
                        + C2 * np.random.rand(N, D) * (GBEST_L - POS)
        
        VEL = speedometer(VEL, g, MAXGEN, V_INI, V_END) # 速度を抑制
        POS = POS + VEL

        # 制約条件の確認
        #POS, VEL = checkBoundaries(POS, VEL, var_max, var_min, vel_min)
        #POS = checkBoundaries_new(POS, var_max, var_min)
        #VEL = speedometer(VEL, vel_max)
        POS, VEL, collision = checkBoundaries_new(POS, VEL, var_max, var_min)

        #print("POS = ", POS)
        #print("VEL = ", VEL)
        db.store(POS, 'p')
        db.store(VEL, 'v')

        # 探索点の評価
        POS_EVAL = fun(POS).T

        # PBestの更新
        PBEST = update_PBEST(POS, POS_EVAL, PBEST, PBEST_EVAL)
        PBEST_EVAL = fun(PBEST).T
        
        # アーカイブの更新
        nowFront = makeParetoFront(POS, POS_EVAL)
        ARC = update_archive(ARC, nowFront)
        #print("ARC[0] = ", ARC[0]) # pos
        #print("ARC[1] = ", ARC[1]) # eval

        print("MOPSO:g = {:3}, GBest = {:3}".format(g, ARC[1].shape[0]))
        db.store(ARC[1], 'e')
        
        # 終了条件の判定
        g = g + 1
        if g > MAXGEN:
            stopCondition = True
    
    return ARC

# 粒子を初期化する関数
def init_particle(N, fun, var_max, var_min):
    D = len(var_max)
    position = var_min + (var_max - var_min) * np.random.rand(N, D)
    position = np.around(position, 5) # 小数点5位まで
    velocity = np.zeros((N, D))
    pos_evaluation = fun(position).T
    #print("評価値配列のサイズ：", pos_evaluation.shape)
    pbest = position
    pbest_evaluation = pos_evaluation

    return position, velocity, pos_evaluation, pbest, pbest_evaluation # タプルを返す

"""
def init_archive(pos, posEval):
    front_pos = np.zeros((N, D))
    front_posEval = np.zeros((N, K))
    RANK = ranking(posEval)
    print("RANK = ", RANK)
    global Na # グローバル変数のNaを使う
    
    # 全粒子のランクを計算し、ランクが1の粒子を混雑距離が大きい順にフロントに入れる
    for i in range(N):
        if(RANK[i] == 1):
            if Na < Na_MAX:
                plt.scatter(posEval[i,0], posEval[i,1], color="red")
                front_pos[Na] = pos[i]
                front_posEval[Na] = posEval[i]
                Na = Na + 1
            else:
                print("capacity over")
    
    # 余った要素を消す
    return front_pos[:Na, :], front_posEval[:Na, :]
"""

# 粒子をランク付けする関数
def ranking(posEval):
    num = posEval.shape[0] # ローカル変数
    RANK = np.empty(num) # i番目の粒子のランクを格納する配列
    
    for i in range(num):
        dominated = 0 # 支配されている粒子の数
        for j in range(num):
            if j != i:
                #print("all(j,i) = ", all(posEval[j, :] < posEval[i, :]))
                #print("any(j,i) = ", any(posEval[j, :] == posEval[i, :]))
                #if all(posEval[j, :] < posEval[i, :]) or any(posEval[j, :] == posEval[i, :]):
                if all(posEval[j, :] < posEval[i, :]):
                    # 2022/10/28に変更　同一線上に重なった解に支配関係はない
                    dominated = dominated + 1
        RANK[i] = 1 + dominated
    
    return RANK

# リーダーを選択する関数
def select_leader(archive):
    frontPos, frontEval = archive
    # ルーレット選択
    CD = crowding_distance(frontEval)
    #print("CD = ", CD)

    if len(CD) == 1:
        print("アーカイブ内の解が1個")
        return frontPos[0]
    elif len(CD) == 2:
        print("アーカイブ内の解が2個")
        selected = frontPos[0] if np.random.rand() > 0.5 else frontPos[1]
        return selected
    else:
        weights = np.array([CD[idx] for idx in range(len(CD)) if np.abs(CD[idx]) != np.Inf])
        #print("weights = ", weights)
        norm_weights = np.array([weights[idx] / np.sum(weights) for idx in range(len(weights))])
        #print("norm_weights = ", norm_weights)
        chosen = np.random.choice(weights, size=1, p=norm_weights)
        L = np.argwhere(CD == chosen)
        #print("chosen particle:", chosen)
        #print("L = ", L[0,0])
        #print("pos[{}] = {}".format(L[0,0], frontPos[L[0,0]]))
        return frontPos[L[0,0]]

# 混雑距離を計算する関数
def crowding_distance(frontEval):
    (Na, K) = frontEval.shape
    CD = np.zeros(Na) # r番目の混雑距離を格納する配列
    #print(frontEval)
    #frontEval_sorted = np.sort(frontEval, axis=0) # 行(縦)に対して昇順ソートする
    indices_sorted = np.argsort(frontEval[:,0]) # f1軸に対して昇順ソート
    #print(indices_sorted)
    frontEval_sorted = frontEval[indices_sorted]
    #print(frontEval_sorted)
    if Na != 1:
        for k in range(K):
            front_up = np.append(frontEval_sorted[1:, k], np.Inf)
            #print(front_up)
            front_down = np.append(np.Inf, frontEval_sorted[:-1, k])
            #print(front_down)
            CD = CD + np.abs(front_up - front_down) #/ (np.max(frontEval_sorted[:, k]) - np.min(frontEval_sorted[:, k])) # 2022/10/28追加　下駄をはかせる 11/6 下駄やめた
    #CD = CD / K # 目的関数の個数で割る
    if Na > 3:
        CD[0] = np.max(CD[1:-2])
    elif Na > 2:
        CD[0] = CD[1]
    else:
        CD[0] = 1
    CD[-1] = CD[0]
    #print(CD) 
    return CD

# 境界条件を確認する関数
def checkBoundaries(POS, VEL, var_max, var_min, vel_min):

    """
    for pos in POS:
        pos[pos > var_max] = var_max[pos > var_max]
        pos[pos < var_min] = var_min[pos < var_min]

    for vel in VEL:
        vel[pos > var_max] = vel_min[pos > var_max]
        vel[pos < var_min] = vel_min[pos < var_min]
    return POS, VEL
    """
    
    newVEL = VEL
    for i in range(POS.shape[0]):
        if any(POS[i] + VEL[i] < var_min) or any(POS[i] + VEL[i] > var_max):
            newVEL[i] = vel_min
    newPOS = POS + newVEL
    return newPOS, newVEL
    
    #for d in range(len(var_max)):   
#if POS[i][d] + VEL[i][d] < var_min[d] or POS[i][d] + VEL[i][d] > var_max[d]:
            #newVEL[i][d] = vel_min

def checkBoundaries_new(POS, VEL, var_max, var_min):
    collision = 0
    damp = 1.0 # 壁にぶつかる度にどれだけ減衰するか
    
    for i, pos in enumerate(POS):
        while any(pos < var_min) or any(pos > var_max):
            #print("max_壁ぶつかった", pos)
            collision += 1
            #pos[pos > var_max] = var_max[pos > var_max]
            pos[pos > var_max] = \
                damp * (2 * var_max[pos > var_max] - pos[pos > var_max]) #研究ノート参照
            #print("max_反射後", pos)

            pos[pos < var_min] = \
                damp * (2 * var_min[pos < var_min] - pos[pos < var_min]) #研究ノート参照
            #print("min_反射後", pos)

            #VEL[i][pos > var_max] = -VEL[i][pos > var_max] #2023/03/06追記
            #VEL[i][pos < var_min] = -VEL[i][pos < var_min] #2023/03/06追記

            # 壁にぶつかった分、速度を減衰させる。さらに方向を転換させる
            VEL[i][pos > var_max] = -damp * VEL[i][pos > var_max]
            VEL[i][pos < var_min] = -damp * VEL[i][pos < var_min]
            #VEL[i][pos > var_max] = 0 # 制約違反した要素だけ速度を0にする 2023/03/13追記
        
        """
        if any(pos > var_max):
            print("max_壁ぶつかった", pos)
            collision += 1
            #pos[pos > var_max] = var_max[pos > var_max]
            pos[pos > var_max] = \
                2 * var_max[pos > var_max] - pos[pos > var_max] #研究ノート参照
            print("max_反射後", pos)

            VEL[i][pos > var_max] = -VEL[i][pos > var_max] #2023/03/06追記
            # 壁にぶつかった分、速度を減衰させる
            VEL[i][pos > var_max] = 0.5 * VEL[i][pos > var_max]

            #VEL[i][pos > var_max] = 0 # 制約違反した要素だけ速度を0にする 2023/03/13追記
        
        if any(pos < var_min):
            print("min_壁ぶつかった", pos)
            collision += 1
            #pos[pos < var_min] = var_min[pos < var_min]
            pos[pos < var_min] = \
                2 * var_min[pos < var_min] - pos[pos < var_min] #研究ノート参照
            print("min_反射後", pos)

            VEL[i][pos < var_min] = -VEL[i][pos < var_min] #2023/03/06追記
            # 壁にぶつかった分、速度を減衰させる
            VEL[i][pos < var_min] = 0.5 * VEL[i][pos < var_min]

            #VEL[i][pos < var_min] = 0 # 速度を0にする 2023/03/13追記
        """
        if any(pos > var_max):
            print("max_まだ出とるやんけ!")
            return -1
        if any(pos < var_min):
            print("min_まだ出とるやんけ!")
            return -1
        
    newPOS = copy.deepcopy(POS)
    newVEL = copy.deepcopy(VEL)
    return newPOS, newVEL, collision

def speedometer(VEL, gen, maxgen, vIni, vEnd):
    vel_max = vIni * np.exp(((gen-1) / maxgen) * np.log(vEnd / vIni))
    for vel in VEL:
        #print(vel > vel_max)
        vel[vel > vel_max] = vel_max[vel > vel_max]
        vel[vel < -vel_max] = -vel_max[vel < -vel_max]
    newVEL = copy.deepcopy(VEL)
    return newVEL

# PBestを更新する関数    
def update_PBEST(pos, posEval, pb, pbEval):
    (N, D) = pos.shape
    newPb = pb
    for i in range(N):
        if all(posEval[i,:] < pbEval[i,:]):
            newPb[i,:] = pos[i,:]
        elif any(posEval[i,:] < pbEval[i,:]):
            if np.random.rand() > 0.5: 
                newPb[i,:] = pos[i,:]
    return newPb

# アーカイブの情報からパレートフロントを作成する関数
def makeParetoFront(pos, posEval):
    Na_MAX = getNAMAX()
    front_pos = np.zeros((Na_MAX, pos.shape[1]))
    front_posEval = np.zeros((Na_MAX, posEval.shape[1]))
    RANK = ranking(posEval)
    indices_sorted = np.argsort(posEval[:,0]) # f1軸に対して昇順ソート
    #print(indices_sorted)
    posEval_sorted = posEval[indices_sorted]
    pos_sorted = pos[indices_sorted]
    #print(frontEval_sorted)

    front_pos[0] = pos_sorted[0]
    front_posEval[0] = posEval_sorted[0]
    localNa = 1 # ローカル変数
    

    for r in range(1, posEval.shape[0]):
        #if RANK[i] == 1:
        if posEval_sorted[r, 1] < front_posEval[localNa - 1, 1]:
            if localNa < Na_MAX:
                front_pos[localNa] = pos_sorted[r]
                front_posEval[localNa] = posEval_sorted[r]
            else:
                front_pos = np.vstack((front_pos, pos_sorted[r]))
                front_posEval = np.vstack((front_posEval, posEval_sorted[r]))
            localNa = localNa + 1
            """
            else:
                print("-----------capa over--------------")
                #既に保存されている解の混雑距離を計算し、最小のものを消してそこに入れる
                CD = crowding_distance(front_posEval)
                minIdx = np.argmin(CD)
                front_pos[minIdx] = pos_sorted[r]
                front_posEval[minIdx] = posEval_sorted[r]
            """
    while localNa > Na_MAX:
        #print("{}個超過".format(localNa - Na_MAX))
        CD = crowding_distance(front_posEval)
        minIdx = np.argmin(CD)
        front_pos = np.delete(front_pos, minIdx, axis = 0)
        front_posEval = np.delete(front_posEval, minIdx, axis = 0)
        localNa = localNa - 1

    return front_pos[:localNa, :], front_posEval[:localNa, :]

# アーカイブを更新する関数
def update_archive(prevFront, nowFront):
    tmpFrontPos = np.vstack( (prevFront[0], nowFront[0]) )
    tmpFrontEval = np.vstack( (prevFront[1], nowFront[1]) )
    newFrontPos, newFrontEval = makeParetoFront(tmpFrontPos, tmpFrontEval)
    return newFrontPos, newFrontEval