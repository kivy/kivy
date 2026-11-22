'''
GstPlayer
=========

.. versionadded:: 1.8.0

.. versionchanged:: 3.0.0
    Rewritten. GStreamer is loaded at run time instead of linked, so the
    module is built without GStreamer and uses the runtime the machine
    has. It drives ``playbin3`` from Kivy's thread (no GLib main loop and
    no callbacks from GStreamer's threads) and can share GL textures with
    Kivy. ``glib_iteration`` and the callback-based constructor are gone.

`GstPlayer` is the GStreamer core used by Kivy's ``gstplayer`` video and
audio providers. Don't use it directly; use the core providers instead.

The compiled core, which opens GStreamer, is imported on first use of one
of the names below; importing it raises ``ImportError`` when no usable
GStreamer is found.

.. warning::

    This is an internal library and Kivy does not provide any support for
    it. It might change in the future and we advise you don't rely on it in
    your code.
'''

import os

_PUBLIC = frozenset((
    'GstPlayer', 'GLShare', 'get_gst_version', 'get_runtime_info', 'has_gl',
    'init_start', 'init_status', 'init_wait', 'init_seconds',
    'filename_to_uri', 'element_available', 'run_pipeline', 'STATE_NULL',
    'STATE_READY', 'STATE_PAUSED', 'STATE_PLAYING', 'STATE_CHANGE_FAILURE',
    'STATE_CHANGE_SUCCESS', 'STATE_CHANGE_ASYNC', 'STATE_CHANGE_NO_PREROLL',
    'MIN_VERSION'))

__all__ = tuple(sorted(_PUBLIC))

if 'KIVY_DOC' in os.environ:
    GstPlayer = GLShare = get_gst_version = None


def __getattr__(name):
    # Lazy, so the pure-Python helpers (_policy, _runtime) import without
    # GStreamer.
    if name not in _PUBLIC:
        raise AttributeError(name)
    # _runtime is imported by the compiled _gstplayer, where PyInstaller's
    # import scan can't see it; naming it here gets it bundled.
    from kivy.lib.gstplayer import _gstplayer, _runtime  # noqa: F401
    return getattr(_gstplayer, name)
