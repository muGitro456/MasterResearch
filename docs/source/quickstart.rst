クイックスタート
================

MasterResearchを初めて動かす手順です。オプションの網羅的な一覧やツールの詳細は、リポジトリ直下の ``README.md`` を参照してください。

前提環境
--------

Python 3.10以上。

セットアップ
------------

.. code-block:: bash

   $ git clone https://github.com/muGitro456/MasterResearch.git
   $ cd MasterResearch
   $ python -m venv .venv
   $ source .venv/bin/activate  # Windowsは .venv\Scripts\activate
   $ pip install -e .

初回実行
--------

インタラクティブモードでは、手法・関数・トポロジーを対話形式で選択できる。

.. code-block:: bash

   $ masterresearch

出力先
------

- ``backLog/`` 以下: パレートフロントの座標・評価指標（CSV）
- ``execution_log.csv``: 実行条件・実行時刻の記録

出力先は ``--output-dir`` / ``--log-file`` オプションで変更できる。

次のステップ
------------

- マニュアルモード・各オプションの詳細: リポジトリ直下の ``README.md`` の「実行方法」
- 各手法の理論的背景: :doc:`algorithms/index`
