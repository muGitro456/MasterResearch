"""python -m masterresearch のエントリポイント。"""
import argparse
import subprocess

from .simulation import file_is_locked, run_simulation
from .utils.config_loader import load_yaml
from .utils.paths import DEFAULT_LOG_FILE, DEFAULT_OUTPUT_DIR


def _select_interactive() -> list[str]:
    """対話形式で手法・ベンチマーク関数・トポロジーを選ばせ、実行コードを1件返す。"""
    methods = load_yaml('methods.yaml')
    functions = load_yaml('functions.yaml')
    topologies = load_yaml('topologies.yaml')

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
    """デスクトップ通知を送る。`notify-send` が使えない環境ではターミナルに出力する。"""
    try:
        subprocess.run(
            ['notify-send', 'MasterResearch', message],
            check=True, timeout=5
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        print(f"[通知] {message}")  # notify-send が使えない環境はターミナルに出力


def _non_empty_path(value: str) -> str:
    """argparse の type 関数。空文字列（および空白のみ）を拒否する。"""
    if not value.strip():
        raise argparse.ArgumentTypeError('空文字列は指定できません')
    return value


def _parse_args() -> argparse.Namespace:
    """コマンドライン引数をパースする。"""
    parser = argparse.ArgumentParser(
        description='MasterResearch MOPSO最適化シミュレーター'
    )
    parser.add_argument(
        '--manual', nargs='+', metavar='CODE',
        help='マニュアルモード: 実行コードを1つ以上指定 (例: --manual 691 27 37)'
    )
    parser.add_argument('--trial', type=int, default=100, help='試行回数 (デフォルト: 100)')
    parser.add_argument('--comment', '-C', default='特になし', help='実行コメント')
    parser.add_argument('--output-dir', type=_non_empty_path, default=DEFAULT_OUTPUT_DIR,
                         help=f'パレートフロント等の出力先ディレクトリ (デフォルト: {DEFAULT_OUTPUT_DIR})')
    parser.add_argument('--log-file', type=_non_empty_path, default=DEFAULT_LOG_FILE,
                         help=f'実行記録CSVのパス (デフォルト: {DEFAULT_LOG_FILE})')
    return parser.parse_args()


def cli() -> None:
    """`masterresearch` コマンドのエントリポイント。

    `--manual` が指定されていればその実行コード群を、指定がなければ
    対話モードで選択した1件を順に実行する。実行記録CSVがロックされている
    場合は実行前にエラー終了する。全実行が終わるとデスクトップ通知を送る。
    """
    args = _parse_args()

    if file_is_locked(args.log_file):
        print("ERROR: {} がロックされています。閉じてから実行してください".format(args.log_file))
        return

    if args.manual:
        instructions = args.manual
    else:
        instructions = _select_interactive()

    for instruction in instructions:
        run_simulation(instruction, trial=args.trial, comment=args.comment,
                        output_dir=args.output_dir, log_file=args.log_file)

    _notify("プログラムの実行が完了しました")


if __name__ == '__main__':  # pragma: no cover
    cli()
