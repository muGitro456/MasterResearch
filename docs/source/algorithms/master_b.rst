MASTER_B
========

``MASTER_B`` は、コード上のdocstringに明記されている通り、現状は :doc:`master_a` と完全に同一の挙動をする（:class:`~masterresearch.src.proposed.MASTER_A` を継承し、``simulation()`` もそのまま呼び出しているだけ）。

独自の理論的な変更点は無く、トポロジー種別を使い分けた比較実験を行う際に、MASTER_Aとは別の実行単位として扱えるように定義されたクラスという位置づけである。``MASTER_A`` が常にリングトポロジー固定で動作するのに対し、``MASTER_B`` は実行コードの3桁目で指定した以下のトポロジーをそのまま使用できる。

.. list-table:: 選択可能なトポロジー
   :header-rows: 1

   * - トポロジー
     - 近傍数 (N_SIZE)
     - 概要
   * - Ring
     - 3 / 5 / 7（設定による）
     - 全要素を環状に接続する
   * - Neumann
     - 5（自身含む）
     - 上下左右+自身の5点。左右は同じ行内でラップする
   * - Cylinder
     - 可変（3〜5）
     - 上下はトーラス状に接続し、左右は端で接続を持たない
   * - Hexagonal
     - 可変（3〜7）
     - 上下左右に加え、右上・左下の対角も接続する
   * - Grid
     - 可変（3〜5）
     - 上下左右のみを接続する（下端・右端はラップしない）

関連コード
----------

- :class:`masterresearch.src.proposed.MASTER_B` — MASTER_Aを継承するのみの実装
- :class:`masterresearch.src.topology.Topology` — 選択可能なトポロジーの一覧
