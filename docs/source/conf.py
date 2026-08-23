"""Sphinx configuration for MasterResearch."""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.normpath(os.path.join(_here, '../..'))
_tools_dir = os.path.normpath(os.path.join(_here, '../../tools'))

sys.path.insert(0, _project_root)
sys.path.insert(0, _tools_dir)

project = 'MasterResearch'
copyright = '2026, muGitro456'
author = 'muGitro456'
with open(os.path.join(_project_root, 'VERSION.txt'), encoding='utf-8') as _f:
    release = _f.read().strip()  # pyproject.toml (dynamic version) と同じ VERSION.txt を参照

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

html_theme = 'furo'
autodoc_member_order = 'bysource'
exclude_patterns = ['_build']
