'''
PiCamera Camera: Implement CameraBase with PiCamera
'''

#
# TODO: make usage of thread or multiprocess
#

__all__ = ('CameraPiCamera', )

from math import ceil

from kivy.logger import Logger
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.camera import CameraBase

from picamera import PiCamera
import numpy


class CameraPiCamera(CameraBase):
    '''Implementation of CameraBase using PiCamera
    '''
    _update_ev = None

    def __init__(self, **kwargs):
        self._camera = None
        self._format = 'bgr'
        self._framerate = kwargs.get('framerate', 30)
        super(CameraPiCamera, self).__init__(**kwargs)

    def init_camera(self):
        if self._camera is not None:
            self._camera.close()

        self._camera = PiCamera()
        self._camera.resolution = self.resolution
        self._camera.framerate = self._framerate
        self._camera.iso = 800

        self.fps = 1. / self._framerate

        if not self.stopped:
            self.start()

    def raw_buffer_size(self):
        '''Round buffer size up to 32x16 blocks.

        See https://picamera.readthedocs.io/en/release-1.13/recipes2.html#capturing-to-a-numpy-array
        '''  # noqa
        return (
            ceil(self.resolution[0] / 32.) * 32,
            ceil(self.resolution[1] / 16.) * 16
        )

    def _update(self, dt):
        if self.stopped:
            return

        if self._texture is None:
            # Create the texture
            self._texture = Texture.create(self._resolution)
            self._texture.flip_vertical()
            self.dispatch('on_load')

        try:
            bufsize = self.raw_buffer_size()
            output = numpy.empty(
                (bufsize[0] * bufsize[1] * 3,), dtype=numpy.uint8)
            self._camera.capture(output, self._format, use_video_port=True)

            # Trim the buffer to fit the actual requested resolution.
            # TODO: Is there a simpler way to do all this reshuffling?
            output = output.reshape((bufsize[0], bufsize[1], 3))
            output = output[:self.resolution[0], :self.resolution[1], :]
            self._buffer = output.reshape(
                (self.resolution[0] * self.resolution[1] * 3,))

            self._copy_to_gpu()
        except KeyboardInterrupt:
            raise
        except Exception:
            Logger.exception('PiCamera: Couldn\'t get image from Camera')

    def start(self):
        super(CameraPiCamera, self).start()
        if self._update_ev is not None:
            self._update_ev.cancel()
        self._update_ev = Clock.schedule_interval(self._update, self.fps)

    def stop(self):
        super(CameraPiCamera, self).stop()
        if self._update_ev is not None:
            self._update_ev.cancel()
            self._update_ev = None
