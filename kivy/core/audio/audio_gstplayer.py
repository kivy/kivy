'''
Audio Gstplayer
===============

Implementation of a VideoBase with Kivy :class:`~kivy.lib.gstplayer.GstPlayer`
This player is the prefered player, using Gstreamer 1.0, working on both Python
2 and 3.
'''

from kivy.lib.gstplayer import GstPlayer, get_gst_version
from kivy.graphics.texture import Texture
from kivy.core.audio import Sound, SoundLoader
from kivy.logger import Logger
from kivy.compat import PY2
from threading import Lock
from functools import partial
from os.path import realpath
from weakref import ref

if PY2:
    from urllib import pathname2url
else:
    from urllib.request import pathname2url


Logger.info('AudioGstplayer: Using Gstreamer {}'.format(
    '.'.join(map(str, get_gst_version()))))


class SoundGstplayer(Sound):

    @staticmethod
    def extensions():
        return ('wav', 'ogg', 'mp3')

    def __init__(self, **kwargs):
        self.player = None
        super(SoundGstplayer, self).__init__(**kwargs)

    def load(self):
        self.unload()
        uri = self._get_uri()
        self.player = GstPlayer(uri, None)
        self.player.set_volume(self.volume)
        self.player.load()

    def play(self):
        self.player.play()
        super(SoundGstplayer, self).play()

    def stop(self):
        self.player.stop()
        super(SoundGstplayer, self).stop()

    def unload(self):
        if self.player:
            self.player.unload()
            self.player = None

    def seek(self, position):
        self.player.seek(position / self.duration)

    def get_pos(self):
        return self.player.get_position()

    def get_length(self):
        return self.player.get_duration()

    def on_volume(self, instance, volume):
        self.player.set_volume(volume)

    def _get_uri(self):
        uri = self.filename
        if not uri:
            return
        if not '://' in uri:
            uri = 'file:' + pathname2url(realpath(uri))
        return uri

SoundLoader.register(SoundGstplayer)
