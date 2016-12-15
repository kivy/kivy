'''
OpenCV Camera: Implement CameraBase with OpenCV
'''

#
# TODO: make usage of thread or multiprocess
#

__all__ = ('CameraOpenCV')

from kivy.logger import Logger
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.camera import CameraBase

try:
    import opencv as cv
    import opencv.highgui as hg
except ImportError:
    import cv

    class Hg(object):
        '''
        On OSX, not only are the import names different, but the API also
        differs. There is no module called 'highgui' but the names are directly
        available in the 'cv' module. Some of them even have a different
        names.

        Therefore we use this proxy object.
        '''

        def __getattr__(self, attr):
            if attr.startswith('cv'):
                attr = attr[2:]
            got = getattr(cv, attr)
            return got

    hg = Hg()


class CameraOpenCV(CameraBase):
    '''Implementation of CameraBase using OpenCV
    '''

    _update_ev = None

    def __init__(self, **kwargs):
        self._device = None
        super(CameraOpenCV, self).__init__(**kwargs)

    def init_camera(self):
        # create the device
        self._device = hg.cvCreateCameraCapture(self._index)

        # Set preferred resolution
        cv.SetCaptureProperty(self._device, cv.CV_CAP_PROP_FRAME_WIDTH,
                              self.resolution[0])
        cv.SetCaptureProperty(self._device, cv.CV_CAP_PROP_FRAME_HEIGHT,
                              self.resolution[1])

        # and get frame to check if it's ok
        frame = hg.cvQueryFrame(self._device)
        # Just set the resolution to the frame we just got, but don't use
        # self.resolution for that as that would cause an infinite recursion
        # with self.init_camera (but slowly as we'd have to always get a
        # frame).
        self._resolution = (int(frame.width), int(frame.height))

        # get fps
        self.fps = cv.GetCaptureProperty(self._device, cv.CV_CAP_PROP_FPS)
        if self.fps <= 0:
            self.fps = 1 / 30.

        if not self.stopped:
            self.start()

    def _update(self, dt):
        if self.stopped:
            return
        if self._texture is None:
            # Create the texture
            self._texture = Texture.create(self._resolution)
            self._texture.flip_vertical()
            self.dispatch('on_load')
        try:
            frame = hg.cvQueryFrame(self._device)
            self._format = 'bgr'
            try:
                self._buffer = frame.imageData
            except AttributeError:
                # On OSX there is no imageData attribute but a tostring()
                # method.
                self._buffer = frame.tostring()
            self._copy_to_gpu()
        except:
            Logger.exception('OpenCV: Couldn\'t get image from Camera')

    def start(self):
        super(CameraOpenCV, self).start()
        if self._update_ev is not None:
            self._update_ev.cancel()
        self._update_ev = Clock.schedule_interval(self._update, self.fps)

    def stop(self):
        super(CameraOpenCV, self).stop()
        if self._update_ev is not None:
            self._update_ev.cancel()
            self._update_ev = None
