"""Sphinx configuration for MasterResearch."""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.normpath(os.path.join(_here, '../../src'))
_tools_dir = os.path.normpath(os.path.join(_here, '../../tools'))

sys.path.insert(0, _src_dir)
sys.path.insert(0, _tools_dir)
os.chdir(_src_dir)  # agent.py 等が ./property/*.json を開くため

project = 'MasterResearch'
copyright = '2026, muGitro456'
author = 'muGitro456'
release = '0.1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

html_theme = 'furo'
autodoc_member_order = 'bysource'
exclude_patterns = ['_build']


def setup(app: object) -> None:
    os.chdir(_src_dir)
