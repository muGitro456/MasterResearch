import os
import sys
import pytest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools'))

sys.path.insert(0, _PROJECT_ROOT)
sys.path.insert(0, _TOOLS_DIR)


@pytest.fixture(autouse=True)
def isolate_cwd(tmp_path, monkeypatch):
    """Run each test from an empty temp directory.

    Phase E2 で record_writer.py / logger.py / simulation.py の出力先が
    CWD 基準で解決されるようになったため、テストを src/ 等の実ディレクトリに
    固定する必要はなくなった。むしろ空の tmp_path で実行することで、CWD
    非依存性が壊れた場合にテストが失敗するようにする。
    """
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def param_dict():
    return {
        "N": 5,
        "N_ARCHIVE_MAX": 10,
        "GENERATION_MAX": 1,
        "INERTIA": 0.7,
        "SELF_AWARENESS": 1.5,
        "SOCIAL_AWARENESS": 1.5,
        "RIVAL_AWARENESS": 1.5,
        "INERTIA_INITIAL": 0.9,
        "INERTIA_END": 0.4,
        "SELF_AWARENESS_OF_PREDATOR": 1.0,
        "LOCAL_AWARENESS": 0.5,
        "VMAX_INITIAL": 5.0,
        "VMAX_END": 10.0,
        "DAMP": 0.5,
        "N_SUB_SWARM": 2,
    }


@pytest.fixture
def zdt2_dict():
    return {"name": "ZDT2", "dimension": 3, "upper": 1.0, "lower": 0.0}


@pytest.fixture
def dtlz1_dict():
    return {"name": "DTLZ1", "dimension": 3, "upper": 1.0, "lower": 0.0}


@pytest.fixture
def ring5_topo_dict():
    return {"name": "Ring_5", "N_SIZE": 5}


@pytest.fixture
def master_c_param_dict():
    return {
        "N": 10,
        "N_ARCHIVE_MAX": 10,
        "GENERATION_MAX": 1,
        "INERTIA": 0.7,
        "SELF_AWARENESS": 1.5,
        "SOCIAL_AWARENESS": 1.5,
        "RIVAL_AWARENESS": 1.5,
        "INERTIA_INITIAL": 0.9,
        "INERTIA_END": 0.4,
        "SELF_AWARENESS_OF_PREDATOR": 1.0,
        "LOCAL_AWARENESS": 0.5,
        "VMAX_INITIAL": 5.0,
        "VMAX_END": 10.0,
        "DAMP": 0.5,
        "N_SUB_SWARM": 2,
    }
