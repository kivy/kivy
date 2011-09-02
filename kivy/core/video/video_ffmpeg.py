'''
FFmpeg video abstraction
========================

.. versionadded:: 1.0.8

This abstraction require ffmpeg python extensions. We made a special extension
that is used for android platform, but can also be used on x86 platform. The
project is available at::

    http://github.com/tito/ffmpeg-android

The extension is designed to implement a video player, what we need here.
Refer to the documentation of ffmpeg-android project for more information about
the requirement.
'''

try:
    import ffmpeg
except:
    raise

from . import VideoBase
from kivy.graphics.texture import Texture


class VideoFFMpeg(VideoBase):

    __slots__ = ('_do_load', '_player')

    def __init__(self, **kwargs):
        self._do_load = False
        self._player = None
        super(VideoFFMpeg, self).__init__(**kwargs)

    def unload(self):
        if self._player:
            self._player.stop()
            self._player = None
        self._state = ''
        self._do_load = False

    def load(self):
        self.unload()

    def play(self):
        if self._player:
            self.unload()
        self._player = ffmpeg.FFVideo(self._filename)
        self._do_load = True

    def stop(self):
        self.unload()

    def seek(self, percent):
        if self._player is None:
            return
        self._player.seek(percent)

    def _do_eos(self):
        self.unload()
        self.dispatch('on_eos')
        super(VideoFFMpeg, self)._do_eos()

    def _update(self, dt):
        if self._do_load:
            self._player.open()
            self._do_load = False
            return

        player = self._player
        if player is None:
            return
        if player.is_open is False:
            self._do_eos()
            return

        frame = player.get_next_frame()
        if frame is None:
            return

        # first time we got a frame, we know that video is readed now.
        if self._texture is None:
            self._texture = Texture.create(size=(
                player.get_width(), player.get_height()),
                colorfmt='rgb')
            self._texture.flip_vertical()
            self.dispatch('on_load')

        self._texture.blit_buffer(frame)
        self.dispatch('on_frame')

    def _get_duration(self):
        if self._player is None:
            return 0
        return self._player.get_duration()

    def _get_position(self):
        if self._player is None:
            return 0
        return self._player.get_position()

    def _get_volume(self):
        if self._player is None:
            return 0
        self._volume = self._player.get_volume()
        return self._volume

    def _set_volume(self, volume):
        if self._player is None:
            return
        self._player.set_volume(volume)
