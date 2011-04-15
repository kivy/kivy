'''
VideoCapture Camera: Implement CameraBase with VideoCapture
'''

#
# TODO: make usage of thread or multiprocess
#

__all__ = ('CameraVideoCapture', )

from . import CameraBase

try:
    from VideoCapture import Device
except:
    raise


class CameraVideoCapture(CameraBase):
    '''Implementation of CameraBase using VideoCapture
    '''

    def __init__(self, **kwargs):
        self._device = None
        super(CameraVideoCapture, self).__init__(**kwargs)
        self._format = 'bgr'

    def init_camera(self):
        # create the device
        self._device = Device(devnum=self._index, showVideoWindow=0)
        # set resolution
        try:
            self._device.setResolution(self.resolution[0], self.resolution[1])
        except:
            raise Exception('VideoCapture: Resolution not supported')

    def _update(self, dt):
        data, camera_width, camera_height = self._device.getBuffer()
        if self._texture is None:
            # first update, resize if necessary
            self.size = camera_width, camera_height
            # and create texture
            from kivy.graphics.texture import Texture
            self._texture = Texture.create(size=self.size, colorfmt='rgb')
            self.dispatch('on_load')

        # update buffer
        self._buffer = data
        self._copy_to_gpu()
