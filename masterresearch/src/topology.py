"""粒子群のトポロジー（近傍構造）の定義。"""
import numpy as np


class Topology:
    """粒子（またはサブ粒子群）間の近傍関係（トポロジー）を表すクラス。

    `topologies.yaml` の `name` に応じてリング型・ノイマン型・円筒型・
    六角形型・格子型のいずれかで近傍関係を構築する。

    Attributes:
        N: 要素数（粒子数またはサブ粒子群数）。
        N_SIZE: リング型トポロジーでの近傍数。
        relation: `relation[i]` が要素 `i` の近傍インデックスのリスト。
    """

    def __init__(self, N: int, N_SIZE: int, name: str) -> None:
        """指定されたトポロジー名で近傍関係を構築する。

        Args:
            N: 要素数（粒子数またはサブ粒子群数）。
            N_SIZE: リング型トポロジーでの近傍数。
            name: トポロジー名（`topologies.yaml` の `name`）。
        """
        self.N = N
        self.N_SIZE = N_SIZE
        self.relation = self.select_edge(name)

    def select_edge(self, name: str) -> list[list[int]]:
        """トポロジー名に応じて各要素の近傍インデックス一覧を構築する。

        リング型以外（ノイマン型・円筒型・六角形型・格子型）は `N` が
        平方数であることを前提に、格子状に配置した要素の上下左右
        （必要に応じてトーラス状にラップアラウンド）を近傍とする。

        Args:
            name: トポロジー名。

        Returns:
            `relation[i]` が要素 `i` の近傍インデックスのリストであるようなリスト。

        Raises:
            ValueError: `name` が未知の場合。
        """
        N_sqrt = np.sqrt(self.N)
        relation: list[list[int]] = [[] for _ in range(self.N)]  # 初期化

        match name:
            case "Ring_5" | "Ring_3" | "Ring_7": # リングトポロジーの場合
                for i in range(self.N):
                    edge = [-1] * self.N_SIZE
                    for m in range(self.N_SIZE):
                        edge[m] = (i + (m - (self.N_SIZE // 2))) % self.N
                    relation[i] = edge

            case "Neumann": # ノイマン型トポロジーの場合
                CENTER, UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3, 4
                for i in range(self.N):
                    edge = [-1] * self.N_SIZE
                    edge[CENTER] = i
                    edge[UP] = (i - N_sqrt) % self.N
                    edge[DOWN] = (i + N_sqrt) % self.N
                    edge[LEFT] = (i - 1) % N_sqrt
                    edge[RIGHT] = (i + 1) % N_sqrt
                    relation[i] = edge

            case "Cylinder":  # 円筒トポロジーの場合
                for i in range(self.N):
                    edge = []
                    edge.append(i)
                    edge.append((i - N_sqrt) % self.N)
                    edge.append((i + N_sqrt) % self.N)

                    if i % N_sqrt != 0:  # iが左端でなければ
                        edge.append(i - 1)

                    if (i + 1) % N_sqrt != 0:  # iが右端でなければ
                        edge.append(i + 1)

                    relation[i] = edge

            case "Hexagonal":  # 六角形トポロジーの場合
                for i in range(self.N):
                    edge = []
                    edge.append(i)  # 自分自身を追加

                    if i - N_sqrt >= 0:  # iが上端でなければ
                         edge.append(i - N_sqrt)  # 上の粒子を追加

                    if i + N_sqrt < self.N:  # iが下端でなければ
                         edge.append(i + N_sqrt)  # 下の粒子を追加

                    if i % N_sqrt != 0:  # iが左端でなければ
                        edge.append(i - 1)  # 左の粒子を追加

                    if (i + 1) % N_sqrt != 0:  # iが右端でなければ
                        edge.append(i + 1)  # 右の粒子を追加

                    if (i - N_sqrt >= 0) and ((i + 1) % N_sqrt != 0):  # iが上端でないかつ右端でない場合(iに右上が存在する場合)
                        edge.append(i + 1 - N_sqrt)  # 右上の粒子を追加

                    if (i + N_sqrt < self.N) and (i % N_sqrt != 0):  # iが下端でないかつ左端でない場合(iに左下が存在する場合)
                        edge.append(i - 1 + N_sqrt)  # 左下の粒子を追加

                    relation[i] = edge

            case "Grid":  # 格子状トポロジーの場合
                for  i in range(self.N):
                    edge = []
                    edge.append(i)

                    if i - N_sqrt >= 0:  # iが上端でなければ
                         edge.append((i - N_sqrt) % self.N)

                    if i + N_sqrt >= self.N:  # iが下端でなければ
                         edge.append((i + N_sqrt) % self.N)

                    if i % N_sqrt != 0:  # iが左端でなければ
                        edge.append(i - 1)

                    if (i + 1) % N_sqrt != 0:  # iが右端でなければ
                        edge.append(i + 1)

                    relation[i] = edge
            case _:
                raise ValueError(f"Unknown topology: {name}")
        return relation
