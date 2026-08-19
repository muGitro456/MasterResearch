# MasterResearch

修士研究で使用した多目的最適化アルゴリズムの実装・実験プログラム群です。  
粒子群最適化 (PSO) をベースに、捕食者行動 (FPO) やトポロジー構造を組み合わせた独自手法の提案と性能比較を行っています。

---

## ディレクトリ構成

```
MasterResearch/
├── src/                     # アルゴリズムコア
│   ├── main.py              # エントリポイント・実験制御
│   ├── field.py             # 探索空間・テスト問題の定義
│   ├── agent.py             # 粒子・粒子群クラス (Swarm, Predators, Neighborhood)
│   ├── agent_subs.py        # サブ粒子群クラス (MASTER_C用)
│   ├── archive.py           # パレートフロント管理 (Archive)
│   ├── topology.py          # 粒子間トポロジーの定義
│   ├── related.py           # 既存手法の実装 (MOPSO, FPO-MOPSO, SENIOR)
│   ├── proposed.py          # 提案手法の実装 (MASTER_A/B/C)
│   ├── metrics.py           # 評価指標計算 (被覆率・RNI)
│   ├── logger.py            # 粒子情報の記録
│   ├── record_writer.py     # 結果の CSV/Excel 出力
│   └── property/
│       ├── parameters.json  # アルゴリズムパラメータ
│       ├── methods.json     # 手法番号とクラス名のマッピング
│       ├── functions.json   # ベンチマーク関数の設定
│       └── topologies.json  # トポロジーの設定
└── tools/                   # 単独実行スクリプト
    ├── database.py          # メトリクス計算ツール (CLI)
    └── graph_drawer.py      # グラフ描画ツール
```

---

## 実装されている手法

| 番号 | クラス名 | 区分 | 概要 |
|:----:|---------|:----:|------|
| 1 | `MOPSO` | 既存 | 標準的な多目的粒子群最適化 |
| 2 | `FPOMOPSO` | 既存 | MOPSOに捕食者群 (FPO) を統合 |
| 3 | `SENIOR` | 既存 | FPO-MOPSOの捕食者に自己最善項を追加 |
| 4 | `MASTER_A` | **提案** | 近傍トポロジー＋FPO統合 (粒子単位の近傍) |
| 5 | `MASTER_B` | **提案** | MASTER_Aの別バリエーション |
| 6 | `MASTER_C` | **提案** | 群を複数のサブ群に分割しトポロジーで接続 |

### 手法の継承関係

```
MOPSO (既存)
  └─ FPOMOPSO (既存)  : + 捕食者群 (FPO) を並行稼働しアーカイブ統合
      └─ SENIOR (既存): 捕食者に自己最善項を追加
          └─ MASTER_A (提案): + 粒子単位の近傍トポロジーを導入
              └─ MASTER_B (提案): MASTER_Aの実験的変形
  MASTER_C (提案): 粒子群をサブ群に分割 → サブ群間をトポロジーで接続 + FPO
```

---

## 処理フロー

```
main.py
  ├─ JSONファイル読み込み (methods, functions, parameters, topologies)
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
       ├─ CSV : パレートフロントの座標 (../backLog/ 以下)
       ├─ Excel: 評価指標の統計 (平均・最大・最小・中央値)
       └─ LINE Notify: 完了通知
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

パラメータは [`src/property/parameters.json`](src/property/parameters.json) で変更できます。

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

```bash
cd src
python main.py
# オプション: コメントを付けて実行
python main.py -C "実験コメント"
```

`main.py` 内の `instruction_set` に手法番号・関数番号・トポロジー番号を指定します。

```python
# 例: MASTER_C (6) + 関数9 + トポロジー1
instruction_set = ["691"]

# 例: 複数条件を一括実行
instruction_set = ["41", "42", "43", "51", "52", "53"]
```

実行前に `プログラム実行記録管理シート.xlsx` が閉じられていることを確認してください。

---

## 依存ライブラリ

- `numpy`
- `pandas`
- `openpyxl`
- `tqdm`
- `requests`
