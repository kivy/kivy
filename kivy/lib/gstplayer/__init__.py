'''
GstPlayer
=========

.. versionadded:: 1.8.0

`GstPlayer` is a media player implemented specifically for Kivy with Gstreamer
1.0. It doesn't use Gi at all and is focused on what we want: the ability
to read video and stream the image in a callback, or read an audio file.
Don't use it directly but use our Core providers instead.

This player is automatically compiled if you have `pkg-config --libs --cflags
gstreamer-1.0` working.

'''

import os
if 'KIVY_DOC' in os.environ:
    GstPlayer = get_gst_version = glib_iteration = None
else:
    from kivy.lib.gstplayer._gstplayer import (
        GstPlayer, get_gst_version, glib_iteration)
