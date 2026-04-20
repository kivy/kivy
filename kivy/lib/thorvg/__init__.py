"""
:mod:`kivy.lib.thorvg`
======================

Minimal, internal Python binding to the ThorVG v1.0.4 C API, used by Kivy's
SVG, SVG-image and Lottie providers.

This module is a thin Cython wrapper around ``thorvg_capi.h`` - see
:mod:`kivy.lib.thorvg._thorvg` for the actual binding and
:doc:`../../guide/lottie-svg` for consumer-facing docs.

The ThorVG engine is initialised exactly once, the first time this package
is imported. No explicit ``term()`` is required - OS process teardown handles
that.

.. note::

    This package is an internal implementation detail of Kivy and its
    public surface is limited to what the built-in SVG / Lottie providers
    need. Users should not rely on the exact shape of this API.
"""

from kivy.lib.thorvg._thorvg import (  # noqa: F401
    Result,
    Paint,
    Picture,
    SwCanvas,
    Accessor,
    LottieAnimation,
    engine_version,
)

__all__ = (
    'Result',
    'Paint',
    'Picture',
    'SwCanvas',
    'Accessor',
    'LottieAnimation',
    'engine_version',
)
