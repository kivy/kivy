"""
Standalone in-place build of the :mod:`kivy.lib.thorvg._thorvg` Cython
extension.

This helper is shared by:

* The lightweight CI gate
  (``.github/workflows/test_thorvg_wrapper.yml``) which builds and tests
  only the ThorVG wrapper without paying for a full
  ``pip install -e .``.
* Developers who want a fast inner loop on wrapper changes without
  rebuilding every Kivy Cython extension.

ThorVG v1.0.4 must already be built as a static library. The include /
library directories are resolved in this order:

1. ``$KIVY_THORVG_INCLUDE_DIR`` / ``$KIVY_THORVG_LIB_DIR`` if both are
   set (CI sets these explicitly after the ThorVG meson build).
2. ``<repo>/.thorvg_build/dist/include/thorvg-1`` and
   ``<repo>/.thorvg_build/dist/lib`` (the local dev convention).

Usage (from the repo root; on Windows, inside a VS dev-cmd shell so
``cl.exe`` is on PATH)::

    python .ci/thorvg_wrapper_build.py build_ext --inplace

The output is ``kivy/lib/thorvg/_thorvg.<abi>.pyd|so`` sitting next to
``__init__.py``.
"""

import os
import sys
from pathlib import Path

from Cython.Build import cythonize
from setuptools import Extension, setup


REPO = Path(__file__).resolve().parent.parent
DIST = REPO / ".thorvg_build" / "dist"

include_dir = os.environ.get(
    "KIVY_THORVG_INCLUDE_DIR", str(DIST / "include" / "thorvg-1"))
lib_dir = os.environ.get(
    "KIVY_THORVG_LIB_DIR", str(DIST / "lib"))

extra_link_args = []
if sys.platform == "darwin":
    extra_link_args.append("-lc++")
elif sys.platform not in ("win32",):
    extra_link_args.append("-lstdc++")

ext = Extension(
    name="kivy.lib.thorvg._thorvg",
    sources=["kivy/lib/thorvg/_thorvg.pyx"],
    include_dirs=[include_dir],
    library_dirs=[lib_dir],
    libraries=["thorvg"],
    language="c++",
    extra_link_args=extra_link_args,
    # TVG_STATIC flips the ThorVG C API macros from __declspec(dllimport)
    # to plain extern, which is required when linking against the static
    # archive produced by meson --default-library=static.
    define_macros=[("TVG_STATIC", "1")],
)

setup(
    name="kivy-thorvg-wrapper",
    ext_modules=cythonize(
        [ext],
        compiler_directives={
            "language_level": 3,
            "embedsignature": True,
        },
    ),
)
