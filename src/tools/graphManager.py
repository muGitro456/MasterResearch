"""
python .\src\tools\graphManager.py 出力したパレートフロントの個数
と打ち込むと実行される
"""
import matplotlib.pyplot as plt
import pandas as pd
import sys, json

colors = ["green", "blue", "red", "orange", "cyan"]
makers = [",", "^", "o"]

def redraw(dataFileName):#, methodName):
    for p, dFName in enumerate(dataFileName):
        df = pd.read_csv(dFName, index_col=0)
        solutions = df.values

        plt.scatter(solutions[:, 0], solutions[:, 1], c=colors[p], marker=makers[p])
    plt.grid()
    plt.xlabel("f1")
    plt.ylabel("f2")

    #plt.xlim(0.0, 1.0)
    #plt.ylim(0.0, 250.0)

    #str_title = "GBest in Archive by " + methodName
    #plt.title(str_title)
    plt.legend(["FPO-MOPSO", "Developed FPO-MOPSO", "Proposed Method"])
    plt.show()
    #plt.savefig(dataFileName + ".png")

if __name__ == "__main__":
    args = sys.argv # コマンドライン引数

    with open('function.json', 'r') as file1:
        functDict = json.load(file1)
    with open('method.json', 'r') as file2:
        methodDict = json.load(file2)

    if len(args) == 1:
        print("ERROR:図示したいパレートフロントの数を入力されてません.")
    else:
        #mNumber = input("メソッド番号を入力: ")
        pf_list = []
        
        for i in range(int(args[1])):
            pf = input("{}つ目のパレートフロントを入力(色は{}): ".format(i+1, colors[i]))
            pf_list.append(pf)
        
        redraw(pf_list)#, methodDict[mNumber]["title"])
        