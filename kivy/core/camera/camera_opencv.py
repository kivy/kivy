'''
OpenCV Camera: Implement CameraBase with OpenCV
'''

#
# TODO: make usage of thread or multiprocess
#

__all__ = ('CameraOpenCV', )

from collections import Counter
from fractions import Fraction
import functools
import math
import operator
import time
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.camera import CameraBase

try:
    # opencv 1 case
    import opencv as cv

    try:
        import opencv.highgui as hg
    except ImportError:
        class Hg(object):
            '''
            On OSX, not only are the import names different,
            but the API also differs.
            There is no module called 'highgui' but the names are
            directly available in the 'cv' module.
            Some of them even have a different names.

            Therefore we use this proxy object.
            '''

            def __getattr__(self, attr):
                if attr.startswith('cv'):
                    attr = attr[2:]
                got = getattr(cv, attr)
                return got

    hg = Hg()

except ImportError:
    # opencv 2 case (and also opencv 3, because it still uses cv2 module name)
    try:
        import cv2
        # here missing this OSX specific highgui thing.
        # I'm not on OSX so don't know if it is still valid in opencv >= 2
    except ImportError:
        raise


class CameraOpenCV(CameraBase):
    '''
    Implementation of CameraBase using OpenCV
    '''
    _update_ev = None

    @staticmethod
    def measure_frame_rate(video_capture, frame_sample_size, threshold=2):
        '''
        Measure the frame rate of an OpenCV video capture.
        :param video_capture: A video capture.
        :param frame_sample_size: The number of frames to sample in order to
                                  measure the video capture's frame rate.
        :param threshold: The minimum frequency of a relevant frame rate
                          measurement.
        :return: The measured frame rate.
        :raises RuntimeError: The specified number of frames cannot be read
                              from the video capture.
        '''
        frame_count = 0
        rates = Counter()
        while frame_count != frame_sample_size:
            start = time.time()
            if not video_capture.grab():
                break
            duration = time.time() - start
            Logger.debug('OpenCV: Captured frame {}/{} in {}s.'.format(
                frame_count + 1, frame_sample_size, duration))
            frame_count += 1
            rates[round(1 / duration)] += 1
        if frame_count != frame_sample_size:
            raise RuntimeError(('OpenCV: Unable to measure the frame rate, '
                                'grabbed only {} out of {} frames.').format(
                frame_count, frame_sample_size))
        rate_frequencies = rates.most_common()
        Logger.debug('OpenCV: Capture (fps, frequency)s are {!r}.'.format(
            rate_frequencies))
        return Fraction(
            math.floor(
                operator.div(
                    *functools.reduce(
                        lambda x, y: (x[0] + operator.mul(*y), x[1] + y[1])
                        if y[1] >= threshold else x,
                        rate_frequencies,
                        (0, 0)))))

    def __init__(self, **kwargs):
        # we will need it, because constants have
        # different access paths between ver. 2 and 3
        try:
            self.opencvMajorVersion = int(cv.__version__[0])
        except NameError:
            self.opencvMajorVersion = int(cv2.__version__[0])

        self._device = None
        super(CameraOpenCV, self).__init__(**kwargs)

    def init_camera(self):
        # consts have changed locations between versions 2 and 3
        if self.opencvMajorVersion == 3:
            PROPERTY_WIDTH = cv2.CAP_PROP_FRAME_WIDTH
            PROPERTY_HEIGHT = cv2.CAP_PROP_FRAME_HEIGHT
            PROPERTY_FPS = cv2.CAP_PROP_FPS
        elif self.opencvMajorVersion == 2:
            PROPERTY_WIDTH = cv2.cv.CV_CAP_PROP_FRAME_WIDTH
            PROPERTY_HEIGHT = cv2.cv.CV_CAP_PROP_FRAME_HEIGHT
            PROPERTY_FPS = cv2.cv.CV_CAP_PROP_FPS
        elif self.opencvMajorVersion == 1:
            PROPERTY_WIDTH = cv.CV_CAP_PROP_FRAME_WIDTH
            PROPERTY_HEIGHT = cv.CV_CAP_PROP_FRAME_HEIGHT
            PROPERTY_FPS = cv.CV_CAP_PROP_FPS

        Logger.debug('Using opencv ver.' + str(self.opencvMajorVersion))

        if self.opencvMajorVersion == 1:
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
            # self.resolution for that as that would cause an infinite
            # recursion with self.init_camera (but slowly as we'd have to
            # always get a frame).
            self._resolution = (int(frame.width), int(frame.height))
            get_frame_rate = cv.GetCaptureProperty
        elif self.opencvMajorVersion == 2 or self.opencvMajorVersion == 3:
            # create the device
            self._device = cv2.VideoCapture(self._index)
            # Set preferred resolution
            self._device.set(PROPERTY_WIDTH,
                             self.resolution[0])
            self._device.set(PROPERTY_HEIGHT,
                             self.resolution[1])
            # and get frame to check if it's ok
            ret, frame = self._device.read()
            # source:
            # http://stackoverflow.com/questions/32468371/video-capture-propid-parameters-in-opencv # noqa
            self._resolution = (int(frame.shape[1]), int(frame.shape[0]))
            get_frame_rate = lambda device, property: device.get(property)
        # get fps
        if self._frame_sample_size:
            frame_rate = self.measure_frame_rate(self._device,
                                                 self._frame_sample_size)
            Logger.info("Camera {}'s frame rate is {}fps based on {} "
                        "sample frames.".format(
                self._index, frame_rate, self._frame_sample_size))
        else:
            frame_rate = Fraction(get_frame_rate(self._device, PROPERTY_FPS))
            Logger.info("Camera {}'s frame rate is {}fps according to its "
                        "driver.".format(self._index, frame_rate))
        # The event interval is the inverse of the camera's frame rate.
        self.fps = float(1 / frame_rate)

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
            ret, frame = self._device.read()
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
