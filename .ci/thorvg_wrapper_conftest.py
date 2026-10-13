"""
Pytest bootstrap for the lightweight ThorVG wrapper gate.

This file is copied by ``.github/workflows/test_thorvg_wrapper.yml`` to the
repository root as ``conftest.py`` so that the stub ``kivy`` / ``kivy.lib`` /
``kivy.logger`` namespaces are registered *before* pytest collects
``kivy/tests/test_thorvg_wrapper.py`` and ``kivy/tests/bench_thorvg_wrapper.py``.

See ``.ci/thorvg_wrapper_bootstrap.py`` for rationale.
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))

# Repo root is usually the parent of the conftest's containing directory
# (this file is either dropped next to the tests in a CI scratch dir, or
# lives in the repo root). Probe upward until we find ``.ci``.
_repo_root = _here
for _ in range(4):
    if os.path.isdir(os.path.join(_repo_root, '.ci')):
        break
    _repo_root = os.path.dirname(_repo_root)

_ci_dir = os.path.join(_repo_root, '.ci')
if _ci_dir not in sys.path:
    sys.path.insert(0, _ci_dir)

import thorvg_wrapper_bootstrap  # noqa: F401,E402 - side-effectful import

thorvg_wrapper_bootstrap._bootstrap(_repo_root)
