# MasterResearch

修士研究で使用した多目的最適化アルゴリズムの実装・実験プログラム群です。  
多目的粒子群最適化 (MOPSO) をベースに、捕食者行動 (FPO) やトポロジー構造を組み合わせた独自手法の提案と性能比較を行っています。

---

## ディレクトリ構成

```
MasterResearch/
├── masterresearch/            # アルゴリズム本体パッケージ
│   ├── __main__.py             # CLI エントリポイント (masterresearch コマンド)
│   ├── simulation.py            # 実験制御 (run_simulation)
│   ├── src/                    # MOPSO アルゴリズムのコアロジック
│   │   ├── field.py             # 探索空間・テスト問題の定義
│   │   ├── agent.py             # 粒子・粒子群クラス (Swarm, Predators, Neighborhood)
│   │   ├── agent_subs.py        # サブ粒子群クラス (MASTER_C用)
│   │   ├── archive.py           # パレートフロント管理 (Archive)
│   │   ├── topology.py          # 粒子間トポロジーの定義
│   │   ├── related.py           # 関連手法の実装 (MOPSO, FPO-MOPSO, SENIOR)
│   │   └── proposed.py          # 提案手法の実装 (MASTER_A/B/C)
│   ├── utils/                  # 設定読み込み・記録・評価指標などの共通ユーティリティ
│   │   ├── config_loader.py     # configs/*.yaml の読み込み (importlib.resources)
│   │   ├── metrics.py           # 評価指標計算 (被覆率・RNI)
│   │   ├── logger.py            # 粒子情報の記録
│   │   ├── record_writer.py     # 結果の CSV 出力
│   │   └── paths.py             # 出力先ディレクトリ・ログファイルのデフォルトパス
│   └── configs/
│       ├── parameters.yaml      # アルゴリズムパラメータ
│       ├── methods.yaml         # 手法番号とクラス名のマッピング
│       ├── functions.yaml       # ベンチマーク関数の設定
│       └── topologies.yaml      # トポロジーの設定
├── tools/                      # 単独実行スクリプト
│   ├── metrics_evaluator.py     # メトリクス計算ツール (CLI)
│   └── graph_drawer.py          # 粒子軌跡アニメーション描画ツール
└── docs/                       # Sphinx ドキュメント (docs/source 配下がソース、APIリファレンス以外にクイックスタート・アルゴリズム解説・実験結果の読み方なども含む)
```

---

## 実装されている手法

| 番号 | クラス名 | 区分 | 概要 |
|:----:|---------|:----:|------|
| 1 | `MOPSO` | 関連 | 標準的な多目的粒子群最適化 |
| 2 | `FPOMOPSO` | 関連 | MOPSOに捕食者群 (FPO) を統合 |
| 3 | `SENIOR` | 関連 | FPO-MOPSOの捕食者に自己最善項を追加 |
| 4 | `MASTER_A` | **提案** | 近傍トポロジー＋FPO統合 (粒子単位の近傍) |
| 5 | `MASTER_B` | **提案** | MASTER_Aの別バリエーション |
| 6 | `MASTER_C` | **提案** | 粒子群を複数のサブ粒子群に分割しトポロジーで接続 |

### 手法の継承関係

```
MOPSO
  └─ FPOMOPSO : + 捕食者群 (FPO) を並行稼働しアーカイブ統合
      └─ SENIOR : 捕食者に自己最善項を追加
          └─ MASTER_A (提案): + 粒子単位の近傍トポロジーを導入
              └─ MASTER_B (提案): MASTER_Aの実験的変形
  MASTER_C (提案): 粒子群をサブ粒子群に分割 → サブ粒子群間をトポロジーで接続 + FPO
```

---

## 処理フロー

```
masterresearch (CLI) → simulation.run_simulation()
  ├─ YAMLファイル読み込み (methods, functions, parameters, topologies)
  ├─ Problem生成 (ベンチマーク関数の設定)
  └─ TRIAL=100回ループ
       ├─ アルゴリズムオブジェクト生成
       │    ├─ SearchSpace 初期化
       │    ├─ Swarm 初期化 (粒子をランダム配置)
       │    ├─ Archive 初期化 (初期パレートフロント構築)
       │    └─ [提案手法] Topology, 近傍群, FPO群 初期化
       │
       └─ simulation() 実行 (世代ループ GENERATION_MAX=200)
            ├─ アーカイブからリーダーを選択 (混雑距離ベース)
            ├─ 粒子群の速度・位置更新
            ├─ 評価値計算 & 個人最善更新
            ├─ アーカイブ更新 (パレートフロント再構築)
            └─ [提案手法] FPO群の更新 & アーカイブ統合

  └─ 結果記録
       ├─ CSV : パレートフロントの座標・評価指標の統計 (デフォルト backLog/ 以下)
       ├─ CSV : 実行記録 (デフォルト execution_log.csv)
       └─ notify-send: 完了通知 (未対応環境ではターミナル出力にフォールバック)
```

---

## パラメータ

| パラメータ | デフォルト値 | 意味 |
|-----------|:-----------:|------|
| `N` | 100 | 粒子数 |
| `N_SUB_SWARM` | 50 | サブ群数 (MASTER_C用) |
| `N_ARCHIVE_MAX` | 150 | アーカイブ最大サイズ |
| `GENERATION_MAX` | 200 | 最大世代数 |
| `INERTIA` | 0.9 | 慣性係数 W |
| `SELF_AWARENESS` | 2.0 | 自己最善係数 C1 |
| `SOCIAL_AWARENESS` | 2.0 | 社会的係数 C2 |
| `RIVAL_AWARENESS` | 2.0 | 競合相手係数 C3 (FPO) |
| `LOCAL_AWARENESS` | 2.0 | 近傍最善係数 C5 |

パラメータは [`masterresearch/configs/parameters.yaml`](masterresearch/configs/parameters.yaml) で変更できます。

---

## 対応ベンチマーク関数

| 関数名 | 目的数 |
|--------|:------:|
| ZDT2 | 2 |
| ZDT6 | 2 |
| DTLZ1 | 3 |
| Rastrigin (多峰性) | 2 |
| Ackley (多峰性) | 2 |
| Griewank (多峰性) | 2 |
| Sphere / Booth / Alpine | 2 |

---

## 対応トポロジー

| トポロジー名 | 特徴 |
|-------------|------|
| Ring_3 / Ring_5 / Ring_7 | リング型 (近傍数 3/5/7) |
| Neumann | ノイマン型 (上下左右4近傍) |
| Cylinder | 円筒型 |
| Hexagonal | 六角形型 |
| Grid | 格子型 |

---

## 評価指標

- **被覆率 (Cover Rate)**: パレートフロントが目的関数空間を均等に覆う割合
- **GB数 (解の個数)**: アーカイブに蓄積された非劣解の数
- **RNI**: 2手法のパレートフロントを合併し、各手法が占める非劣解の割合で優劣を比較

---

## 実行方法

`masterresearch` パッケージをインストールすると `masterresearch` コマンドが使えます（`python -m masterresearch` でも同様に実行可能）。

```bash
$ python -m venv .venv
$ source .venv/bin/activate  # Windows は .venv\Scripts\activate
$ pip install -e .

# インタラクティブモード: 手法・関数・トポロジーを対話式に選択
$ masterresearch

# マニュアルモード: 実行コード（手法番号+関数番号[+トポロジー番号]）を直接指定
# 例: MASTER_C (6) + 関数9 + トポロジー1
# 注意: MASTER_A (4) は常にリングトポロジー固定のため、
#       3桁目でトポロジーを指定しても無視される
$ masterresearch --manual 691

# 複数条件を一括実行
$ masterresearch --manual 41 42 43 51 52 53

# オプション: 試行回数・コメント・出力先を指定
$ masterresearch --manual 691 --trial 50 --comment "実験コメント" --output-dir backLog --log-file execution_log.csv
```

| オプション | デフォルト | 意味 |
|-----------|:----------:|------|
| `--manual CODE [CODE ...]` | なし（省略時はインタラクティブモード） | 実行コード（手法番号+関数番号[+トポロジー番号]）を1つ以上指定 |
| `--trial` | 100 | 試行回数 |
| `--comment`, `-C` | `特になし` | 実行コメント |
| `--output-dir` | `backLog` | パレートフロント等の出力先ディレクトリ |
| `--log-file` | `execution_log.csv` | 実行記録CSVのパス |

実行前に `--log-file` で指定したCSV（デフォルト `execution_log.csv`）が他プロセスで開かれていないことを確認してください。ロックされている場合はエラーを表示して終了します。

---

## ツール

### メトリクス計算 (`tools/metrics_evaluator.py`)

```bash
$ python tools/metrics_evaluator.py --rni    # 2つのパレートフロントの RNI を比較
$ python tools/metrics_evaluator.py --val    # ディレクトリ内全パレートフロントの被覆率を評価
$ python tools/metrics_evaluator.py --rniall # 1つのパレートフロントと複数の RNI を比較
```

### 粒子軌跡アニメーション (`tools/graph_drawer.py`)

```bash
$ python tools/graph_drawer.py <trajectory_best.csv のパス> [フレーム間隔ms]
```

`masterresearch` 実行時に自動保存される `trajectory_best.csv`（出力先ディレクトリ配下）を読み込み、世代ごとの粒子位置を `matplotlib.animation` でアニメーション再生します。

---

## ドキュメント (Sphinx)

各モジュールの API リファレンスに加え、クイックスタート・アルゴリズムの理論的解説（PSOから提案手法MASTER_A/B/Cまで）・実験結果の読み方といったページも Sphinx で生成しています。ソースは `docs/source/`、
ビルド成果物は `docs/_build/`（gitignore 対象、コミットしない）です。

```bash
# 「実行方法」で作成した仮想環境を有効化した状態で実行してください
$ pip install -e ".[docs]"   # sphinx, furo をインストール
$ sphinx-build -b html docs/source docs/_build/html
```

生成された `docs/_build/html/index.html` をブラウザで開くと閲覧できます。

---

## 依存ライブラリ

- `numpy`
- `pandas`
- `tqdm`
- `matplotlib`
- `pyyaml`

開発用（ドキュメントビルド）:

- `sphinx`
- `furo`
