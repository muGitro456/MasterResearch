"""python -m masterresearch のエントリポイント。"""
import argparse
import json
import os
import subprocess
import sys
from typing import Any

_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SRC_DIR)
os.chdir(_SRC_DIR)

from main import main as run_main  # noqa: E402


def _load_json(name: str) -> dict[str, Any]:
    path = os.path.join(_SRC_DIR, 'property', name)
    with open(path, encoding='utf-8') as f:
        data: dict[str, Any] = json.load(f)
    return data


def _select_interactive() -> list[str]:
    methods = _load_json('methods.json')
    functions = _load_json('functions.json')
    topologies = _load_json('topologies.json')

    print("\n=== MasterResearch Interactive Mode ===\n")

    # メソッド選択
    print("使用するメソッドを選択してください:")
    for k, v in methods.items():
        print(f"  {k}: {v['name']}")
    meth_num = input("番号を入力 > ").strip()

    # ベンチマーク関数選択
    print("\n使用するベンチマーク関数を選択してください:")
    for k, v in functions.items():
        print(f"  {k}: {v['name']}")
    func_num = input("番号を入力 > ").strip()

    # トポロジー選択（MASTER_B/C のみ）
    meth_name = methods[meth_num]['name']
    if meth_name in ('MASTER_B', 'MASTER_C'):
        print("\n使用するトポロジーを選択してください:")
        for k, v in topologies.items():
            if k != '0':  # トポロジーなしは除外
                print(f"  {k}: {v['name']}")
        topo_num = input("番号を入力 > ").strip()
        instruction = meth_num + func_num + topo_num
    else:
        instruction = meth_num + func_num

    return [instruction]


def _notify(message: str) -> None:
    try:
        subprocess.run(
            ['notify-send', 'MasterResearch', message],
            check=True, timeout=5
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        print(f"[通知] {message}")  # notify-send が使えない環境はターミナルに出力


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='MasterResearch PSO最適化シミュレーター'
    )
    parser.add_argument(
        '--manual', nargs='+', metavar='CODE',
        help='マニュアルモード: 実行コードを1つ以上指定 (例: --manual 691 27 37)'
    )
    parser.add_argument('--trial', type=int, default=100, help='試行回数 (デフォルト: 100)')
    parser.add_argument('--comment', '-C', default='ただのテスト', help='実行コメント')
    return parser.parse_args()


def cli() -> None:
    args = _parse_args()

    if args.manual:
        instructions = args.manual
    else:
        instructions = _select_interactive()

    for instruction in instructions:
        run_main(instruction, trial=args.trial, comment=args.comment)

    _notify("プログラムの実行が完了しました")


if __name__ == '__main__':
    cli()
