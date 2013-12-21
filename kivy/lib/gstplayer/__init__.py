'''
Gstplayer
=========

.. versionadded:: 1.8.0

`GstPlayer` is an media player, implemented specifically for Kivy with Gstreamer
1.0. It doesn't use Gi at all, and are focused to do the work we want: ability
to read video and stream the image in a callback, or read audio file.
Don't use it directly, use our Core providers instead.

This player is automatically compiled if you have `pkg-config --libs --cflags
gstreamer-1.0` working.

'''

import os
if 'KIVY_DOC' in os.environ:
    GstPlayer = get_gst_version = glib_iteration = None
else:
    from _gstplayer import GstPlayer, get_gst_version, glib_iteration
