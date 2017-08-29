'''
GstGLPlayer
=========

.. versionadded:: 1.10.1

`GstGLPlayer` a media player based on `GstPlayer` but using Gstreamer's OpenGL
support, for smoother video playback

This player is automatically compiled if you have `pkg-config --libs --cflags
gstreamer-gl-1.0` working.

.. warning::

    This is an external library and Kivy does not provide any support for it.
    It might change in the future and we advise you don't rely on it in your
    code.
'''

import os
if 'KIVY_DOC' in os.environ:
    GstGLPlayer = get_gst_version = glib_iteration = None
else:
    from kivy.lib.gstglplayer._gstglplayer import (
        GstGLPlayer, get_gst_version, glib_iteration)
