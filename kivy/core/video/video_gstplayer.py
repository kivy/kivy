'''
Video Gstplayer
===============

.. versionadded:: 1.8.0

Implementation of a VideoBase with Kivy :class:`~kivy.lib.gstplayer.GstPlayer`
This player is the preferred player, using Gstreamer 1.0, working on both
Python 2 and 3.
'''

from kivy.lib.gstplayer import GstPlayer, get_gst_version
from kivy.graphics.texture import Texture
from kivy.core.video import VideoBase
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.compat import PY2
from threading import Lock
from functools import partial
from os.path import realpath
from weakref import ref

if PY2:
    from urllib import pathname2url
else:
    from urllib.request import pathname2url

Logger.info('VideoGstplayer: Using Gstreamer {}'.format(
    '.'.join(map(str, get_gst_version()))))


def _on_gstplayer_buffer(video, width, height, data):
    video = video()
    # if we still receive the video but no more player, remove it.
    if not video:
        return
    with video._buffer_lock:
        video._buffer = (width, height, data)


def _on_gstplayer_message(mtype, message):
    if mtype == 'error':
        Logger.error('VideoGstplayer: {}'.format(message))
    elif mtype == 'warning':
        Logger.warning('VideoGstplayer: {}'.format(message))
    elif mtype == 'info':
        Logger.info('VideoGstplayer: {}'.format(message))


class VideoGstplayer(VideoBase):

    def __init__(self, **kwargs):
        self.player = None
        self._buffer = None
        self._buffer_lock = Lock()
        super(VideoGstplayer, self).__init__(**kwargs)

    def _on_gst_eos_sync(self):
        Clock.schedule_once(self._do_eos, 0)

    def load(self):
        Logger.debug('VideoGstplayer: Load <{}>'.format(self._filename))
        uri = self._get_uri()
        wk_self = ref(self)
        self.player_callback = partial(_on_gstplayer_buffer, wk_self)
        self.player = GstPlayer(uri, self.player_callback,
                                self._on_gst_eos_sync, _on_gstplayer_message)
        self.player.load()

    def unload(self):
        if self.player:
            self.player.unload()
            self.player = None
        with self._buffer_lock:
            self._buffer = None
        self._texture = None

    def stop(self):
        super(VideoGstplayer, self).stop()
        self.player.stop()

    def pause(self):
        super(VideoGstplayer, self).pause()
        self.player.pause()

    def play(self):
        super(VideoGstplayer, self).play()
        self.player.set_volume(self.volume)
        self.player.play()

    def seek(self, percent, precise=True):
        self.player.seek(percent)

    def _get_position(self):
        return self.player.get_position()

    def _get_duration(self):
        return self.player.get_duration()

    def _set_volume(self, value):
        self._volume = value
        if self.player:
            self.player.set_volume(self._volume)

    def _update(self, dt):
        buf = None
        with self._buffer_lock:
            buf = self._buffer
            self._buffer = None
        if buf is not None:
            self._update_texture(buf)
            self.dispatch('on_frame')

    def _update_texture(self, buf):
        width, height, data = buf

        # texture is not allocated yet, create it first
        if not self._texture:
            self._texture = Texture.create(size=(width, height),
                                           colorfmt='rgb')
            self._texture.flip_vertical()
            self.dispatch('on_load')

        if self._texture:
            self._texture.blit_buffer(
                data, size=(width, height), colorfmt='rgb')

    def _get_uri(self):
        uri = self.filename
        if not uri:
            return
        if '://' not in uri:
            uri = 'file:' + pathname2url(realpath(uri))
        return uri
