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
from kivy.core.gl import GL_BGR_EXT

try:
    import opencv as cv
    import opencv.highgui as hg
except:
    raise

class CameraOpenCV(CameraBase):
    '''Implementation of CameraBase using OpenCV

    :Parameters:
        `video_src` : int, default is 0
            Index of OpenCV camera to use (0 mean default camera)
    '''

    def __init__(self, **kwargs):
        # override the default source of video
        kwargs.setdefault('video_src', 0)

        self._device = None

        super(CameraOpenCV, self).__init__(**kwargs)

    def init_camera(self):
        # create the device
        self._device = hg.cvCreateCameraCapture(self.video_src)

        try:
            # try first to set resolution
            cv.hg(self._device, cv.CV_CAP_PROP_FRAME_WIDTH,
                              self.resolution[0])
            cv.hg(self._device, cv.CV_CAP_PROP_FRAME_HEIGHT,
                              self.resolution[1])

            # and get frame to check if it's ok
            frame  = hg.cvQueryFrame(self._device)
            if not int(frame.width) == self.resolution[0]:
                raise Exception('OpenCV: Resolution not supported')

        except:
            # error while setting resolution
            # fallback on default one
            w = int(hg.cvGetCaptureProperty(self._device,
                    hg.CV_CAP_PROP_FRAME_WIDTH))
            h = int(hg.cvGetCaptureProperty(self._device,
                    hg.CV_CAP_PROP_FRAME_HEIGHT))
            frame  = hg.cvQueryFrame(self._device)
            Logger.warning(
                'OpenCV: Camera resolution %s not possible! Defaulting to %s.' %
                (self.resolution, (w, h)))

            # set resolution to default one
            self._resolution = (w, h)

        # create texture !
        self._texture = Texture.create(*self._resolution)
        self._texture.flip_vertical()

        if not self.stopped:
            self.start()

    def update(self):
        if self.stopped:
            return
        try:
            frame = hg.cvQueryFrame(self._device)
            self._format = GL_BGR_EXT
            self._buffer = frame.imageData
            self._copy_to_gpu()
        except:
            Logger.exception('OpenCV: Couldn\'t get image from Camera')

