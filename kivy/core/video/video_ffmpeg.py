'''
FFmpeg video abstraction
========================

.. versionadded:: 1.0.8

This abstraction requires ffmpeg python extensions. We have made a special
extension that is used for the android platform but can also be used on x86
platforms. The project is available at::

    http://github.com/tito/ffmpeg-android

The extension is designed for implementing a video player.
Refer to the documentation of the ffmpeg-android project for more information
about the requirements.
'''

try:
    import ffmpeg
except:
    raise

from kivy.core.video import VideoBase
from kivy.graphics.texture import Texture


class VideoFFMpeg(VideoBase):

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
        self._player.set_volume(self._volume)
        self._do_load = True

    def stop(self):
        self.unload()

    def seek(self, percent, precise=True):
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
        if not player.is_open:
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

        if self._texture:
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

    def _set_volume(self, value):
        self._volume = value
        if self._player:
            self._player.set_volume(self._volume)
