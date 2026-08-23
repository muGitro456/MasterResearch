"""configs/ ディレクトリの YAML 設定ファイルを CWD 非依存に読み込むユーティリティ。"""
from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

_PACKAGE = 'masterresearch'  # NOTE: トップレベルパッケージ名を変更する場合はここも更新すること


def load_yaml(filename: str) -> dict[str, Any]:
    """`masterresearch/configs/` 配下の YAML ファイルを読み込む。

    `importlib.resources` を使うため、カレントディレクトリに依存せず、
    インストール済みパッケージ（wheel 経由も含む）からでも読み込める。

    Args:
        filename: `configs/` ディレクトリ内のファイル名
            （例: `'parameters.yaml'`, `'methods.yaml'`）。

    Returns:
        YAML の内容を変換した辞書。
    """
    path = resources.files(_PACKAGE).joinpath('configs').joinpath(filename)
    with path.open('r', encoding='utf-8') as f:
        data: dict[str, Any] = yaml.safe_load(f)
    return data
