'''
A video provider that uses the `av` python wrapper of ffmpeg

requires Pillow to get images from frames.

TODO: sound management!
'''

# check we have the required dependencies
import av
import PIL  # noqa

from kivy.core.video import VideoBase
from kivy.graphics.texture import Texture


class VideoAV(VideoBase):
    def __init__(self, **kwargs):
        super(VideoAV, self).__init__(**kwargs)
        self._cont = None
        self._texture = None
        self._frames = None
        self._next_frame = None

    def seek(self, percent, precise=True):
        if self._cont is None:
            return
        self._cont.seek(
            int(percent * self._cont.duration),
            whence='frame',
            any_frame=precise
        )
        self._position = percent * self.duration
        self._frames = self._cont.decode(video=0)
        self._update(0, forced=True)

    def play(self):
        if self._cont:
            # XXX should we close the previous container?
            pass

        if self._cont is None:
            self._cont = cont = av.open(self._filename)
            self._frames = cont.decode(video=0)
            self._texture = None
            self._position = 0

        super(VideoAV, self).play()

    def pause(self):
        super(VideoAV, self).pause()

    def stop(self):
        self._cont = self._frames = self._texture = None
        super(VideoAV, self).stop()

    def _update(self, dt, forced=False):
        if self.state != 'playing' and not forced:
            return
        self._position += dt
        if not self._frames:
            return

        if self._next_frame:
            frame = self._next_frame
            if self._position < (frame.index * frame.time_base / 1000.):
                return

            img = frame.to_image()
            if not self._texture:
                size = img.size
                self._texture = tex = Texture.create(size)
                tex.flip_vertical()
                self.dispatch('on_load')

            tex = self._texture
            tex.blit_buffer(img.tobytes())
            self.dispatch('on_frame')

        try:
            frame = self._next_frame = next(self._frames)
            while self._position >= frame.index * frame.time_base:
                frame = self._next_frame = next(self._frames)
        except StopIteration:
            self.stop()
            self.dispatch('on_eos')
            return

    def _get_position(self):
        return self._position

    def _get_duration(self):
        if self._cont:
            return float(
                self._cont.duration *
                self._next_frame.time_base / 1000
            )
        return 0
