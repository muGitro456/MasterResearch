import numpy as np

class Archive:
    def __init__(self, pos_swarm, fit_swarm, NA_MAX, D, K) -> None:
        self.cr = 0.0 # 被覆率
        self.NA_MAX = NA_MAX
        self.D = D
        self.K = K

        self.pos_gb, self.fit_gb = self.make_pareto_front(pos_swarm, fit_swarm)
    
    def make_pareto_front(self, pos, fit):
        pos_gb = np.zeros((self.NA_MAX, self.D)) # アーカイブに保存されているGBestの位置
        fit_gb = np.zeros((self.NA_MAX, self.K)) # アーカイブに保存されているGBestの評価値

        if self.K == 2:
            indices_sorted = np.argsort(fit[:, 0])
            pos_sorted = pos[indices_sorted]
            fit_sorted = fit[indices_sorted]

            pos_gb[0] = pos_sorted[0]
            fit_gb[0] = fit_sorted[0]
            NA = 1 # 解(GBest)の個数

            for r in range(1, fit.shape[0]):
                if fit_sorted[r, 1] < fit_gb[NA - 1, 1]:
                    if NA < self.NA_MAX:
                        pos_gb[NA] = pos_sorted[r]
                        fit_gb[NA] = fit_sorted[r]
                    else:
                        pos_gb = np.vstack((pos_gb, pos_sorted[r]))
                        fit_gb = np.vstack((fit_gb, fit_sorted[r]))
                    NA += 1
        else:
            #print("Now is K = 3 in archive.py")
            NA = 0
            for r in range(fit.shape[0]):
                others = [j for j in range(fit.shape[0]) if j != r]
                for k in range(self.K):
                    for other in others:
                        if fit[other, k] <= fit[r, k]:
                            break
                    else:
                        if NA < self.NA_MAX:
                            pos_gb[NA] = pos[r]
                            fit_gb[NA] = fit[r]
                        else:
                            pos_gb = np.vstack((pos_gb, pos[r]))
                            fit_gb = np.vstack((fit_gb, fit[r]))
                        NA += 1
        
        while NA > self.NA_MAX:
            cd = self.calc_crowding_distance()
            minIdx = np.argmin(cd)
            pos_gb = np.delete(pos_gb, minIdx, axis = 0)
            fit_gb = np.delete(fit_gb, minIdx, axis = 0)
            NA -= 1
        
        return pos_gb[:NA, :], fit_gb[:NA, :]

    def update_archive(self, POS_current, FIT_current):
        tmp_pos_gb = np.vstack((self.pos_gb, POS_current))
        tmp_fit_gb = np.vstack((self.fit_gb, FIT_current))
        self.make_pareto_front(tmp_pos_gb, tmp_fit_gb)
    
    def select_leader(self):
        cd = self.calc_crowding_distance()

        if len(cd) == 1:
            #print("アーカイブ内の解が1個")
            return self.pos_gb[0]
        elif len(cd) == 2:
            #print("アーカイブ内の解が2個")
            selected = self.pos_gb[0] if np.random.rand() > 0.5 else self.pos_gb[1]
            return selected
        else:
            weights = np.array( [cd[j] for j in range(len(cd)) if np.abs(cd[j]) != np.Inf] )
            p_weights = np.array([weights[j] / np.sum(weights) for j in range(len(weights))])
            chosen = np.random.choice(weights, size=1, p=p_weights)
            leader = np.argwhere(cd == chosen)
            #print(type(leader))
            return self.pos_gb[leader[0,0]]
    
    def calc_crowding_distance(self):
        NA = len(self.fit_gb)
        cd = np.zeros(NA)
        indices_sorted = np.argsort(self.fit_gb[:,0]) # f1軸に対して昇順ソート
        fit_gb_sorted = self.fit_gb[indices_sorted]
        
        if NA != 1:
            for k in range(self.K):
                front_up = np.append(fit_gb_sorted[1:, k], np.Inf)
                #print(front_up)
                front_down = np.append(np.Inf, fit_gb_sorted[:-1, k])
                #print(front_down)
                cd = cd + np.abs(front_up - front_down) #/ (np.max(fit_gb_sorted[:, k]) - np.min(fit_gb_sorted[:, k])) # 2022/10/28追加　下駄をはかせる 11/6 下駄やめた
        #cd = cd / K # 目的関数の個数で割る
        if NA > 3:
            cd[0] = np.max(cd[1:-2])
        elif NA > 2:
            cd[0] = cd[1]
        else:
            cd[0] = 1
        cd[-1] = cd[0]
        #print(cd) 
        return cd
    
    def calc_cover_rate(self, divNum) -> float:
        if self.K == 3:
            min_f = np.array([np.min(self.fit_gb[:, 0]), np.min(self.fit_gb[:, 1]), np.min(self.fit_gb[:, 2])])
            max_f = np.array([np.max(self.fit_gb[:, 0]), np.max(self.fit_gb[:, 1]), np.max(self.fit_gb[:, 2])])
            width = np.array([max_f[0] - min_f[0], max_f[1] - min_f[1], max_f[2] - min_f[2]]) / divNum
        else:
            min_f = np.array([np.min(self.fit_gb[:, 0]), np.min(self.fit_gb[:, 1])])
            max_f = np.array([np.max(self.fit_gb[:, 0]), np.max(self.fit_gb[:, 1])])
            width = np.array([max_f[0] - min_f[0], max_f[1] - min_f[1]]) / divNum

        region = np.zeros((self.K, divNum))
        cover = np.zeros(self.K)
        for k in range(self.K):
            for r in range(self.fit_gb.shape[0]):
                for div in range(divNum):
                    lowLim = min_f[k] + width[k] * div
                    highLim = lowLim + width[k]

                    if lowLim <= self.fit_gb[r, k] and self.fit_gb[r, k] <= highLim:
                        region[k, div] = region[k, div] + 1
                        break
            
            for div in range(divNum):
                if region[k, div] != 0:
                    cover[k] = cover[k] + 1
            cover[k] = cover[k] / divNum
        return np.sum(cover) / self.K

    def union_archive(self, POS1, FIT1, POS2, FIT2):
        POS_COMB = np.vstack((POS1, POS2))
        FIT_COMB = np.vstack((FIT1, FIT2))
        return POS_COMB, FIT_COMB