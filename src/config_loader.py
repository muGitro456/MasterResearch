"""configs/ ディレクトリの YAML 設定ファイルを CWD 非依存に読み込むユーティリティ。"""
from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

_PACKAGE = 'src'  # NOTE: src パッケージ名を変更する場合はここも更新すること


def load_yaml(filename: str) -> dict[str, Any]:
    path = resources.files(_PACKAGE).joinpath('configs').joinpath(filename)
    with path.open('r', encoding='utf-8') as f:
        data: dict[str, Any] = yaml.safe_load(f)
    return data
