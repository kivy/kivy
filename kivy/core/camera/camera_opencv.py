'''
OpenCV Camera: Implement CameraBase with OpenCV
'''

#
# TODO: make usage of thread or multiprocess
#

__all__ = ('CameraOpenCV', )

from kivy.logger import Logger
from kivy.graphics.texture import Texture
from . import CameraBase

try:
    import opencv as cv
    import opencv.highgui as hg
except:
    raise

class CameraOpenCV(CameraBase):
    '''Implementation of CameraBase using OpenCV
    '''

    def __init__(self, **kwargs):
        self._device = None
        super(CameraOpenCV, self).__init__(**kwargs)

    def init_camera(self):
        # create the device
        self._device = hg.cvCreateCameraCapture(self._index)

        try:
            # try first to set resolution
            cv.hg(self._device, cv.CV_CAP_PROP_FRAME_WIDTH,
                              self.resolution[0])
            cv.hg(self._device, cv.CV_CAP_PROP_FRAME_HEIGHT,
                              self.resolution[1])

            # and get frame to check if it's ok
            frame = hg.cvQueryFrame(self._device)
            if not int(frame.width) == self.resolution[0]:
                raise Exception('OpenCV: Resolution not supported')

        except:
            # error while setting resolution
            # fallback on default one
            w = int(hg.cvGetCaptureProperty(self._device,
                    hg.CV_CAP_PROP_FRAME_WIDTH))
            h = int(hg.cvGetCaptureProperty(self._device,
                    hg.CV_CAP_PROP_FRAME_HEIGHT))
            frame = hg.cvQueryFrame(self._device)
            Logger.warning(
                'OpenCV: Camera resolution %s not possible! Defaulting to %s.' %
                (self.resolution, (w, h)))

            # set resolution to default one
            self._resolution = (w, h)

        # create texture !
        self._texture = Texture.create(*self._resolution)
        self._texture.flip_vertical()
        self.dispatch('on_load')

        if not self.stopped:
            self.start()

    def _update(self, dt):
        if self.stopped:
            return
        try:
            frame = hg.cvQueryFrame(self._device)
            self._format = 'bgr'
            self._buffer = frame.imageData
            self._copy_to_gpu()
        except:
            Logger.exception('OpenCV: Couldn\'t get image from Camera')

