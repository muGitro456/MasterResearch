import os
import sys
import pytest

_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
_TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools'))
os.chdir(_SRC_DIR)
sys.path.insert(0, _SRC_DIR)
sys.path.insert(0, _TOOLS_DIR)


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
