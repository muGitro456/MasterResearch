import numpy as np
import copy, json
import logger as db

with open('./property/parameters.json', 'r') as f:
    param_dict = json.load(f)
    
class SubSwarm:
    # クラス変数
    W = param_dict["INERTIA"]
    C1 = param_dict["SELF_AWARENESS"]
    C2 = param_dict["SOCIAL_AWARENESS"]

    def __init__(self, N_SUB_PARTICLE, swarm, index, field) -> None:
        self.N_SUB_PARTICLE = N_SUB_PARTICLE
        self.POS = np.empty((N_SUB_PARTICLE, field.D))
        self.VEL = np.empty((N_SUB_PARTICLE, field.D))
        self.FIT = np.empty((N_SUB_PARTICLE, field.K))
        self.POS_PB = np.empty((N_SUB_PARTICLE, field.D))
        self.FIT_PB = np.empty((N_SUB_PARTICLE, field.K))

        for j in range(N_SUB_PARTICLE):
            self.POS[j] = swarm.POS[index * N_SUB_PARTICLE + j]
            self.VEL[j] = swarm.VEL[index * N_SUB_PARTICLE + j]
            self.FIT[j] = swarm.FIT[index * N_SUB_PARTICLE + j]
            self.POS_PB[j] = swarm.POS_PB[index * N_SUB_PARTICLE + j]
            self.FIT_PB[j] = swarm.FIT_PB[index * N_SUB_PARTICLE + j]
    
    def update_vel(self, gbL, my_field, gen):
        VEL_TMP = SubSwarm.W * self.VEL \
                + SubSwarm.C1 * np.random.rand(self.N_SUB_PARTICLE, my_field.D) * (self.POS_PB - self.POS) \
                + SubSwarm.C2 * np.random.rand(self.N_SUB_PARTICLE, my_field.D) * (gbL - self.POS)

        self.VEL = my_field.speedmeter(VEL_TMP, gen)

    def update_pos(self, field):
        _POS_TMP = self.POS + self.VEL
        self.POS, self.VEL = field.check_boundaries(_POS_TMP, self.VEL)
    
    def update_pb(self):
        for i in range(self.N_SUB_PARTICLE):
            if all(self.FIT[i] < self.FIT_PB[i]):
                self.POS_PB[i] = copy.deepcopy(self.POS[i])
            elif any(self.FIT[i] < self.FIT_PB[i]):
                if np.random.rand() > 0.5:
                    self.POS_PB[i] = copy.deepcopy(self.POS[i])

class Neighborhood_C:
    C5 = param_dict["LOCAL_AWARENESS"]

    def __init__(self, sub_swarms, index, field, my_topology) -> None:
        self.N_SIZE = len(my_topology.relation[index])
        self.N_SUB_PARTICLE = sub_swarms[0].N_SUB_PARTICLE
        self.my_field = field
        self.my_swarm = sub_swarms
        self.index = index

        #print("self.N_SIZE = ", self.N_SIZE)
        self.POS = np.empty((self.N_SIZE * self.N_SUB_PARTICLE, field.D))
        self.VEL = np.empty((self.N_SIZE * self.N_SUB_PARTICLE, field.D))
        self.FIT = np.empty((self.N_SIZE * self.N_SUB_PARTICLE, field.K))
        self.POS_PB = np.empty((self.N_SIZE * self.N_SUB_PARTICLE, field.D))
        self.FIT_PB = np.empty((self.N_SIZE * self.N_SUB_PARTICLE, field.K))

        for m in range(self.N_SIZE):
            idx_edge = int(my_topology.relation[index][m])
            for j in range(self.N_SUB_PARTICLE):
                #print("m = {}, j = {}".format(m,j))
                #print("idx_egde = ", idx_edge)
                self.POS[m * self.N_SUB_PARTICLE + j] = self.my_swarm[idx_edge].POS[j]
                self.VEL[m * self.N_SUB_PARTICLE + j] = self.my_swarm[idx_edge].VEL[j]
                self.FIT[m * self.N_SUB_PARTICLE + j] = self.my_swarm[idx_edge].FIT[j]
                self.POS_PB[m * self.N_SUB_PARTICLE + j] = self.my_swarm[idx_edge].POS_PB[j]
                self.FIT_PB[m * self.N_SUB_PARTICLE + j] = self.my_swarm[idx_edge].FIT_PB[j]

    def explore(self, generation, leader, LBEST):
        self.update_vel(leader, LBEST, self.my_field, generation)

        self.my_swarm[self.index].update_pos(self.my_field)
        self.FIT = self.my_field.update_fit(self.POS)

        db.store(self.POS, 'p')
        db.store(self.VEL, 'v')

        self.my_swarm[self.index].update_pb()
        self.my_field.update_fit(self.POS_PB)

        return self.POS, self.FIT
    
    def update_vel(self, gbL, lb, my_field, gen):
        VEL_TMP = self.my_swarm[0].W * self.VEL \
                + self.my_swarm[0].C1 * np.random.rand(self.N_SIZE * self.N_SUB_PARTICLE, my_field.D) * (self.POS_PB - self.POS) \
                + self.my_swarm[0].C2 * np.random.rand(self.N_SIZE * self.N_SUB_PARTICLE, my_field.D) * (gbL - self.POS) \
                + self.C5          * np.random.rand(self.N_SIZE * self.N_SUB_PARTICLE, my_field.D) * (lb - self.POS)

        self.VEL = my_field.speedmeter(VEL_TMP, gen)