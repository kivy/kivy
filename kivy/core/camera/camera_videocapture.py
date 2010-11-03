'''
VideoCapture Camera: Implement CameraBase with VideoCapture
'''

#
# TODO: make usage of thread or multiprocess
#

__all__ = ('CameraVideoCapture', )

import kivy
from . import CameraBase
from kivy.core.gl import GL_BGR

try:
    from VideoCapture import Device
except:
    raise

class CameraVideoCapture(CameraBase):
    '''Implementation of CameraBase using VideoCapture

    :Parameters:
        `video_src` : int, default is 0
            Index of VideoCapture camera to use (0 mean default camera)
    '''

    def __init__(self, **kwargs):
        # override the default source of video
        kwargs.setdefault('video_src', 0)
        self._device = None
        super(CameraVideoCapture, self).__init__(**kwargs)
        self._format = GL_BGR

    def init_camera(self):
        # create the device
        self._device = Device(devnum=self.video_src, showVideoWindow=0)
        # set resolution
        try:
            self._device.setResolution(self.resolution[0], self.resolution[1])
        except:
            raise Exception('VideoCapture: Resolution not supported')

    def update(self):
        data, camera_width, camera_height = self._device.getBuffer()
        if self._texture is None:
            # first update, resize if necessary
            self.size = camera_width, camera_height
            # and create texture
            self._texture = kivy.Texture.create(camera_width, camera_height,
                                                format=GL_BGR)

        # update buffer
        self._buffer = data
        self._copy_to_gpu()
