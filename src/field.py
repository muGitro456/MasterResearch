import numpy as np
import copy

class SearchSpace:
    def __init__(self, params, problem) -> None:
        self.fun = problem.fun
        self.D = problem.D
        self.upper = problem.upper
        self.lower = problem.lower
        self.K = problem.K

        self.GEN_MAX = params["GENERATION_MAX"]
        VMAX_INI = (self.upper - self.lower) / params["VMAX_INITIAL"]
        VMAX_END = (self.upper - self.lower) / params["VMAX_END"]
        self.VMAX = lambda g: VMAX_INI * np.exp(((g-1) / self.GEN_MAX) * np.log(VMAX_END / VMAX_INI))
        self.DAMP = params["DAMP"]

    def update_fit(self, x):
        return self.fun(x).T
    
    def check_boundaries(self, POS, VEL):
        for pos, vel in zip(POS, VEL):
            while any(pos < self.lower) or any(pos > self.upper):
                pos[pos > self.upper] = self.DAMP * (2 * self.upper[pos > self.upper] - pos[pos > self.upper])
                pos[pos < self.lower] = self.DAMP * (2 * self.lower[pos < self.lower] - pos[pos < self.lower])
                
                vel[pos > self.upper] = self.DAMP * (-1) * vel[pos > self.upper]
                vel[pos < self.lower] = self.DAMP * (-1) * vel[pos < self.lower]
        
        pos_new = copy.deepcopy(POS)
        vel_new = copy.deepcopy(VEL)
        return pos_new, vel_new
    
    def speedmeter(self, VEL, gen):
        vmax = self.VMAX(gen)
        #print("In speedmeter VEL.shape = ",VEL.shape)
        for vel in VEL:
            vel[vel > vmax] = vmax[vel > vmax]
            vel[vel < -vmax] = -vmax[vel < -vmax]
        VEL_NEW = copy.deepcopy(VEL)
        return VEL_NEW

class Problem:
    def __init__(self, func_dict) -> None:
        name = func_dict["name"]
        dimension = func_dict["dimension"]
        upper = np.array([func_dict["upper"] for _ in range(dimension)])
        lower = np.array([func_dict["lower"] for _ in range(dimension)])

        match name:
            case "DTLZ1":  # DTLZ1を解く場合
                A = lambda x : np.sum((x[:, 2:] - 0.5) ** 2)
                B = lambda x : np.sum(np.cos(20 * np.pi * (x[:, 2:] - 0.5)))
                g = lambda x : 100 * (5 + A(x) - B(x))

                f1 = lambda x : 0.5 * x[:, 0] * x[:, 1] * (1 + g(x))
                f2 = lambda x : 0.5 * x[:, 0] * (1 - x[:, 1]) * (1 + g(x))
                f3 = lambda x : 0.5 * (1 - x[:, 0]) * (1 + g(x))

                self.fun = lambda x : np.array([f1(x), f2(x), f3(x)])
                self.D = dimension
                self.upper = upper
                self.lower = lower
                self.K = 3
            
            case "ZDT2":  # ZDT2を解く場合
                f = lambda x : x[:, 0]
                g = lambda x : 1 + (9 / (dimension - 1)) * np.sum(x[:, 2:])
                h = lambda x : 1 - (f(x) / g(x)) ** 2

                self.fun = lambda x : np.array([f(x), g(x) * h(x)])
                self.D = dimension
                self.upper = upper
                self.lower = lower
                self.K = 2

            case "ZDT6":  # ZDT6を解く場合
                f = lambda x : 1 - np.exp(-4 * x[:, 0]) * pow(np.sin(6 * np.pi * x[:, 0]), 6)
                g = lambda x : 1 + 9 * pow(np.sum(x[:, 1:], axis=1) / 9, 0.25)
                h = lambda x : 1 - (f(x) / g(x)) ** 2

                self.fun = lambda x : np.array([f(x), g(x) * h(x)])
                self.D = dimension
                self.upper = upper
                self.lower = lower
                self.K = 2

            case _:  # 多峰性問題を解く場合
                F = self.multimodel_func(func_dict["name"], dimension)
                f = lambda x : x[:, 0]
                g = lambda x : 1 + F(x)
                h = lambda x : 1 - np.sqrt(f(x) / g(x))

                self.fun = lambda x : np.array([f(x), g(x) * h(x)])
                self.D = dimension + 1
                self.upper = np.append(np.ones(1), upper)
                self.lower = np.append(np.zeros(1), lower)
                self.K = 2
    
    def multimodel_func(self, func_name, dimension):
        match func_name:
            case "Rastrigin":
                A = lambda x : np.sum(x[:, 1:] ** 2, axis=1)
                B = lambda x : - 10 * np.sum(np.cos(2 * np.pi * x[:, 1:]), axis=1)
                F = lambda x : 10 * dimension + A(x) + B(x)
            
            case "Ackley":
                A = lambda x : -0.2 * np.sqrt((1.0 / dimension) * np.sum(x[:, 1:] ** 2, axis = 1))
                B = lambda x : (1.0 / dimension) * np.sum(np.cos(2 * np.pi * x[:, 1:]), axis=1)
                F = lambda x : 20 - 20 * np.exp(A(x)) + np.e - np.exp(B(x))
                #upper = np.array([32.768 for d in range(dimension)])
            
            case "Griewank":
                A = lambda x : (1.0 / 4000.0) * np.sum(x[:, 1:] ** 2, axis = 1)
                w = np.array([1.0 / np.sqrt(k + 1) for k in range(dimension)])
                B = lambda x : - np.prod(np.cos(x[:, 1:] * w), axis=1)
                F = lambda x : 1 + A(x) + B(x)
                #upper = np.array([600.0 for d in range(dimension)])
            
            case "Sphere":
                F = lambda x : np.sum(x[:, 1:]**2, axis=1)
            
            case "Booth":
                F = lambda x : (x[:, 1] + 2*x[:, 2] - 7)**2 + (2*x[:, 1] + x[:, 2] - 5)**2
            
            case "Alpine":
                F = lambda x : np.sum(np.abs(x[:, 1:] * np.sin(x[:, 1:]) + 0.1 * x[:, 1:]))
        
            case _: # defaultの場合
                print("ERROR")
                return -1
        return F