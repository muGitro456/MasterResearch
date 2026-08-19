"""RNI・被覆率などのメトリクスをコマンドラインから計算するツール。

Usage:
    python tools/metrics_evaluator.py --rni    # 2つのパレートフロントの RNI を比較
    python tools/metrics_evaluator.py --val    # ディレクトリ内全パレートフロントの被覆率を評価
    python tools/metrics_evaluator.py --rniall # 1つのパレートフロントと複数の RNI を比較
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from masterresearch.utils.metrics import evaluation, rni


def print_rni_result(pf1_name: str, pf2_name: str, result: tuple[float, float]) -> None:
    rni1, rni2 = result
    print("\n---RNI 比較結果---")
    print("【{}】: RNI = {:.3f} ({:.1f}%)".format(pf1_name, rni1, rni1 * 100))
    print("【{}】: RNI = {:.3f} ({:.1f}%)".format(pf2_name, rni2, rni2 * 100))
    if rni1 > rni2:
        print("→ 前者が優勢")
    elif rni1 < rni2:
        print("→ 後者が優勢")
    else:
        print("→ 同率（互角）")


if __name__ == "__main__":
    args = sys.argv

    try:
        option = args[1]
    except IndexError:
        print("オプションを指定してください.\n(--rni: RNI計算, --val: 個数と被覆率計算, --rniall: 複数RNI計算)")
    else:
        if option == '--rni':
            pf1_name = input("1つ目のパレートフロントのファイル名を入力:")
            pf2_name = input("2つ目のパレートフロントのファイル名を入力:")
            result = rni(pf1_name, pf2_name)
            print_rni_result(pf1_name, pf2_name, result)

        elif option == '--val':
            dir_name = input("ディレクトリ名を入力：")
            print("【{}】内のパレートフロントを評価".format(dir_name))
            try:
                evaluation(dir_name)
            except ValueError:
                print("ディレクトリ名に誤りがあります.")

        elif option == '--rniall':
            pf1_name = input("1つ目のパレートフロントのファイル名を入力:")
            numOfPF = 9
            pf2_list = []
            for i in range(numOfPF):
                pf = input("2-{}つ目のパレートフロントを入力: ".format(i+1))
                pf2_list.append(pf)
            for pf2_name in pf2_list:
                result = rni(pf1_name, pf2_name)
                print_rni_result(pf1_name, pf2_name, result)

        else:
            print("不正なオプションです.")
