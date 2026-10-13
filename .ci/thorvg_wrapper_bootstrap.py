"""
CI-only bootstrap for the lightweight ``kivy.lib.thorvg`` wrapper gate.

The wrapper lives at ``kivy/lib/thorvg/`` inside the main Kivy package, but
for the lightweight gate we do **not** want to pay the cost of a full
``pip install -e .`` (which would build every Cython extension and pull
in SDL3, GStreamer, and all the image/audio providers).

Running ``import kivy.lib.thorvg`` would normally execute
``kivy/__init__.py``, which imports ``kivy.core`` and friends. To avoid
that, this module pre-registers empty namespace modules for ``kivy`` and
``kivy.lib`` in ``sys.modules`` with their ``__path__`` pointing into the
real source tree. Python then treats them as already-imported, skips the
real ``kivy/__init__.py``, and only executes
``kivy/lib/thorvg/__init__.py`` (which only imports from its own
``._thorvg`` Cython extension).

The wrapper's exception path (``_accessor_trampoline``) lazily imports
``kivy.logger`` - we stub that too with a thin wrapper over
``logging.getLogger``.

Use this module either by importing it explicitly before any
``kivy.lib.thorvg`` import, or by placing it on ``PYTHONPATH`` as
``sitecustomize.py`` (CI workflow does the former via ``conftest.py``).
"""
import logging
import os
import sys
import types


def _bootstrap(repo_root: str) -> None:
    repo_root = os.path.abspath(repo_root)

    if 'kivy' not in sys.modules:
        kivy_mod = types.ModuleType('kivy')
        kivy_mod.__path__ = [os.path.join(repo_root, 'kivy')]
        sys.modules['kivy'] = kivy_mod

    if 'kivy.lib' not in sys.modules:
        kivy_lib_mod = types.ModuleType('kivy.lib')
        kivy_lib_mod.__path__ = [os.path.join(repo_root, 'kivy', 'lib')]
        sys.modules['kivy.lib'] = kivy_lib_mod

    if 'kivy.logger' not in sys.modules:
        kivy_logger_mod = types.ModuleType('kivy.logger')
        kivy_logger_mod.Logger = logging.getLogger('kivy')
        kivy_logger_mod.LOG_LEVELS = {
            'trace': logging.DEBUG,
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL,
        }
        sys.modules['kivy.logger'] = kivy_logger_mod


if __name__ != '__main__':
    _bootstrap(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
