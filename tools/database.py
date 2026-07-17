"""RNI・被覆率などのメトリクスをコマンドラインから計算するツール。

Usage:
    python tools/database.py -rni    # 2つのパレートフロントの RNI を比較
    python tools/database.py -val    # ディレクトリ内全パレートフロントの被覆率を評価
    python tools/database.py -rniall # 1つのパレートフロントと複数の RNI を比較
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from metrics import evaluation, rni


if __name__ == "__main__":
    args = sys.argv

    try:
        option = args[1]
    except IndexError:
        print("オプションを指定してください.\n(-rni: RNI計算, -val: 個数と被覆率計算)")
    else:
        if option == '-rni':
            pf1_name = input("1つ目のパレートフロントのファイル名を入力:")
            pf2_name = input("2つ目のパレートフロントのファイル名を入力:")
            print("【{}】と\n【{}】のRNIは...\n".format(pf1_name, pf2_name))
            result = rni(pf1_name, pf2_name)
            print("RNI = ", result)
            if result[0] > result[1]:
                print("前者の方がイイ!")
            elif result[0] < result[1]:
                print("後者の方がイイ!")
            else:
                print("同率!")

        elif option == '-val':
            dir_name = input("ディレクトリ名を入力：")
            print("【{}】内のパレートフロントを評価".format(dir_name))
            try:
                evaluation(dir_name)
            except ValueError:
                print("ディレクトリ名に誤りがあります.")

        elif option == '-rniall':
            pf1_name = input("1つ目のパレートフロントのファイル名を入力:")
            numOfPF = 9
            pf2_list = []
            for i in range(numOfPF):
                pf = input("2-{}つ目のパレートフロントを入力: ".format(i+1))
                pf2_list.append(pf)
            for pf2_name in pf2_list:
                result = rni(pf1_name, pf2_name)
                print(result)

        else:
            print("不正なオプションです.")
