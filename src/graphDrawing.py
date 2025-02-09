"""
python .\graphDrawing.py
と打ち込むと実行される
"""
import matplotlib.pyplot as plt
import pandas as pd

colors = ["green", "blue", "orange", "cyan", "magenta", "purple", "red"]#, "black", "purple", "lime"]
#colors = ["red", "orange", "cyan", "magenta"]
markers = [",", "^", "o", "v", "D", "*", ","]
#markers = ["o", "v", "D", "*"]

def redraw(dataFileName):
    """
    グラフを再描画する。

    Parameters
    ----------
    dataFileName : filename(str)
        パレートフロントのパス名
    """
    
    for p, dFName in enumerate(dataFileName):
        df = pd.read_csv(dFName, index_col=0)
        solutions = df.values

        plt.scatter(solutions[:, 0], solutions[:, 1], c=colors[p], marker=markers[p])

    #plt.xlim(0.0, 1.0)
    #plt.ylim(0.0, 140.0)
    plt.grid()
    plt.xlabel("f1")
    plt.ylabel("f2")
    plt.legend(["FPO-MOPSO", "DFPO-MOPSO", "Proposed A1", "Proposed A2", "Proposed A3", "Proposed A4", "Proposed A5"])
    #plt.legend(["DFPO-MOPSO", "Grid", "Cylindrical", "Neumann", "Hexagonal", "Ring", "Nsub = 10", "Nsub = 20", "Nsub = 25", "Nsub = 50"])
    #plt.legend(["FPO-MOPSO", "DFPO-MOPSO", "Proposed Method A", "Neumann", "Cylinder", "Hexagonal", "Grid"])
    plt.show()

if __name__ == "__main__":
    numOfPF = int(input("出力したいパレートフロントの数を入力: "))
    pf_list = []
    
    for i in range(numOfPF):
        pf = input("{}つ目のパレートフロントを入力(色は{}): ".format(i+1, colors[i]))
        pf_list.append(pf)
    
    redraw(pf_list)