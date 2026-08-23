アルゴリズム解説
================

.. note::
   本セクションの内容は、著者（本リポジトリの作者）自身の修士論文を出典としてまとめたものです。外部の論文を直接引用したものではなく、著者本人が過去に執筆した論文の記述をベースにしています。

MasterResearchが実装しているアルゴリズム群について、基礎理論であるPSOから提案手法（MASTER_A/B/C）に至るまでの理論的な発展の流れに沿って解説します。

.. _algorithms-lineage:

発展の系統図
------------

.. code-block:: text

   PSO
     └─ MOPSO
          └─ FPO-MOPSO (+ FPO)
               └─ DFPO-MOPSO / SENIOR
                    └─ MASTER_A
                         ├─ MASTER_B（MASTER_Aと同一挙動、トポロジー比較実験用）
                         └─ MASTER_C（サブ粒子群単位のサブアーカイブ）

.. _algorithms-method-list:

手法一覧
--------

.. list-table::
   :header-rows: 1

   * - 手法
     - 要約
   * - :doc:`pso`
     - 基礎理論。PBest/GBestに引き寄せられて一点に収束する
   * - :doc:`mopso`
     - PSOの多目的拡張。アーカイブと混雑距離で多様性を確保する
   * - :doc:`fpo`
     - 捕食者モデル。GBestを使わず局所解回避に強い
   * - :doc:`fpo_mopso`
     - MOPSOとFPOの二群を統合する
   * - :doc:`dfpo_mopso`
     - FPO側の条件式を緩和し、PBestも考慮する（SENIOR）
   * - :doc:`master_a`
     - 粒子単位のサブアーカイブ＋トポロジー近傍（提案手法）
   * - :doc:`master_b`
     - MASTER_Aと同一挙動。トポロジー比較実験用
   * - :doc:`master_c`
     - サブ粒子群単位のサブアーカイブ（提案手法）

.. toctree::
   :maxdepth: 1
   :hidden:

   pso
   mopso
   fpo
   fpo_mopso
   dfpo_mopso
   master_a
   master_b
   master_c
