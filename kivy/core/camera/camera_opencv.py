'''
OpenCV Camera: Implement CameraBase with OpenCV
'''

#
# TODO: make usage of thread or multiprocess
#

from __future__ import division

__all__ = ('CameraOpenCV')


from kivy.logger import Logger
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.camera import CameraBase
from kivy.utils import platform

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

    def __init__(self, **kwargs):
        kwargs.setdefault('api_name', "CAP_ANY")
        self.api_name = kwargs.get('api_name')
        
        #Handle generic default value in the camera class
        if self.api_name == "default":
            self.api_name == "CAP_ANY"
        
        # Provide a default api for opencv that doesn't lag on windows
        if platform == 'win' and self.api_name == "CAP_ANY":
            self.api_name = "CAP_DSHOW"
        
        # we will need it, because constants have
        # different access paths between ver. 2 and 3
        try:
            self.opencvMajorVersion = int(cv.__version__[0])

        except NameError:
            self.opencvMajorVersion = int(cv2.__version__[0])

        #ID names used from here:
        #https://docs.opencv.org/3.4/d4/d15/group__videoio__flags__base.html#ga023786be1ee68a9105bf2e48c700294d
        if self.opencvMajorVersion in (3, 4):
            api_ids = { "CAP_ANY": cv2.CAP_ANY,
                        "CAP_VFW": cv2.CAP_VFW,
                        "CAP_V4L": cv2.CAP_V4L,
                        "CAP_V4L2": cv2.CAP_V4L2,
                        "CAP_FIREWIRE": cv2.CAP_FIREWIRE,
                        "CAP_FIREWARE": cv2.CAP_FIREWARE,
                        "CAP_IEEE1394": cv2.CAP_IEEE1394,
                        "CAP_DC1394": cv2.CAP_DC1394,
                        "CAP_CMU1394": cv2.CAP_CMU1394,
                        "CAP_QT": cv2.CAP_QT,
                        "CAP_UNICAP": cv2.CAP_UNICAP,
                        "CAP_DSHOW": cv2.CAP_DSHOW,
                        "CAP_PVAPI": cv2.CAP_PVAPI,
                        "CAP_OPENNI": cv2.CAP_OPENNI,
                        "CAP_OPENNI_ASUS": cv2.CAP_OPENNI_ASUS,
                        "CAP_ANDROID": cv2.CAP_ANDROID,
                        "CAP_XIAPI": cv2.CAP_XIAPI,
                        "CAP_AVFOUNDATION": cv2.CAP_AVFOUNDATION,
                        "CAP_GIGANETIX": cv2.CAP_GIGANETIX,
                        "CAP_MSMF": cv2.CAP_MSMF,
                        "CAP_WINRT": cv2.CAP_WINRT,
                        "CAP_INTELPERC": cv2.CAP_INTELPERC,
                        "CAP_OPENNI2": cv2.CAP_OPENNI2,
                        "CAP_OPENNI2_ASUS": cv2.CAP_OPENNI2_ASUS,
                        "CAP_GPHOTO2": cv2.CAP_GPHOTO2,
                        "CAP_GSTREAMER": cv2.CAP_GSTREAMER,
                        "CAP_FFMPEG": cv2.CAP_FFMPEG,
                        "CAP_IMAGES": cv2.CAP_IMAGES,
                        "CAP_ARAVIS": cv2.CAP_ARAVIS,
                        "CAP_OPENCV_MJPEG": cv2.CAP_OPENCV_MJPEG,
                        "CAP_INTEL_MFX": cv2.CAP_INTEL_MFX,
                        "CAP_XINE": cv2.CAP_XINE}

        elif self.opencvMajorVersion == 2:
            api_ids = { "CAP_ANY": cv2.cv.CAP_ANY,
                        "CAP_VFW": cv2.cv.CAP_VFW,
                        "CAP_V4L": cv2.cv.CAP_V4L,
                        "CAP_V4L2": cv2.cv.CAP_V4L2,
                        "CAP_FIREWIRE": cv2.cv.CAP_FIREWIRE,
                        "CAP_FIREWARE": cv2.cv.CAP_FIREWARE,
                        "CAP_IEEE1394": cv2.cv.CAP_IEEE1394,
                        "CAP_DC1394": cv2.cv.CAP_DC1394,
                        "CAP_CMU1394": cv2.cv.CAP_CMU1394,
                        "CAP_QT": cv2.cv.CAP_QT,
                        "CAP_UNICAP": cv2.cv.CAP_UNICAP,
                        "CAP_DSHOW": cv2.cv.CAP_DSHOW,
                        "CAP_PVAPI": cv2.cv.CAP_PVAPI,
                        "CAP_OPENNI": cv2.cv.CAP_OPENNI,
                        "CAP_OPENNI_ASUS": cv2.cv.CAP_OPENNI_ASUS,
                        "CAP_ANDROID": cv2.cv.CAP_ANDROID,
                        "CAP_XIAPI": cv2.cv.CAP_XIAPI,
                        "CAP_AVFOUNDATION": cv2.cv.CAP_AVFOUNDATION,
                        "CAP_GIGANETIX": cv2.cv.CAP_GIGANETIX,
                        "CAP_MSMF": cv2.cv.CAP_MSMF,
                        "CAP_WINRT": cv2.cv.CAP_WINRT,
                        "CAP_INTELPERC": cv2.cv.CAP_INTELPERC,
                        "CAP_OPENNI2": cv2.cv.CAP_OPENNI2,
                        "CAP_OPENNI2_ASUS": cv2.cv.CAP_OPENNI2_ASUS,
                        "CAP_GPHOTO2": cv2.cv.CAP_GPHOTO2,
                        "CAP_GSTREAMER": cv2.cv.CAP_GSTREAMER,
                        "CAP_FFMPEG": cv2.cv.CAP_FFMPEG,
                        "CAP_IMAGES": cv2.cv.CAP_IMAGES,
                        "CAP_ARAVIS": cv2.cv.CAP_ARAVIS,
                        "CAP_OPENCV_MJPEG": cv2.cv.CAP_OPENCV_MJPEG,
                        "CAP_INTEL_MFX": cv2.cv.CAP_INTEL_MFX,
                        "CAP_XINE": cv2.cv.CAP_XINE}

        elif self.opencvMajorVersion == 1:
            api_ids = { "CAP_ANY": cv.CAP_ANY,
                        "CAP_VFW": cv.CAP_VFW,
                        "CAP_V4L": cv.CAP_V4L,
                        "CAP_V4L2": cv.CAP_V4L2,
                        "CAP_FIREWIRE": cv.CAP_FIREWIRE,
                        "CAP_FIREWARE": cv.CAP_FIREWARE,
                        "CAP_IEEE1394": cv.CAP_IEEE1394,
                        "CAP_DC1394": cv.CAP_DC1394,
                        "CAP_CMU1394": cv.CAP_CMU1394,
                        "CAP_QT": cv.CAP_QT,
                        "CAP_UNICAP": cv.CAP_UNICAP,
                        "CAP_DSHOW": cv.CAP_DSHOW,
                        "CAP_PVAPI": cv.CAP_PVAPI,
                        "CAP_OPENNI": cv.CAP_OPENNI,
                        "CAP_OPENNI_ASUS": cv.CAP_OPENNI_ASUS,
                        "CAP_ANDROID": cv.CAP_ANDROID,
                        "CAP_XIAPI": cv.CAP_XIAPI,
                        "CAP_AVFOUNDATION": cv.CAP_AVFOUNDATION,
                        "CAP_GIGANETIX": cv.CAP_GIGANETIX,
                        "CAP_MSMF": cv.CAP_MSMF,
                        "CAP_WINRT": cv.CAP_WINRT,
                        "CAP_INTELPERC": cv.CAP_INTELPERC,
                        "CAP_OPENNI2": cv.CAP_OPENNI2,
                        "CAP_OPENNI2_ASUS": cv.CAP_OPENNI2_ASUS,
                        "CAP_GPHOTO2": cv.CAP_GPHOTO2,
                        "CAP_GSTREAMER": cv.CAP_GSTREAMER,
                        "CAP_FFMPEG": cv.CAP_FFMPEG,
                        "CAP_IMAGES": cv.CAP_IMAGES,
                        "CAP_ARAVIS": cv.CAP_ARAVIS,
                        "CAP_OPENCV_MJPEG": cv.CAP_OPENCV_MJPEG,
                        "CAP_INTEL_MFX": cv.CAP_INTEL_MFX,
                        "CAP_XINE": cv.CAP_XINE}

        
        self.api_id = api_ids.get(self.api_name, 0) #0 is the API ID of CAP_ANY for both cv and cv2
        if self.api_name not in api_ids:
            Logger.exception('OpenCV: The API name provided is not valid.  Using the default instead.')
            
        self._device = None
        super(CameraOpenCV, self).__init__(**kwargs)

    def init_camera(self):
        # consts have changed locations between versions 2 and 3
        if self.opencvMajorVersion in (3, 4):
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
            self._device = hg.cvCreateCameraCapture(self._index, self.api_id)
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
            # get fps
            self.fps = cv.GetCaptureProperty(self._device, cv.CV_CAP_PROP_FPS)

        elif self.opencvMajorVersion in (2, 3, 4):
            # create the device
            self._device = cv2.VideoCapture(self._index, self.api_id)
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
            # get fps
            self.fps = self._device.get(PROPERTY_FPS)

        if self.fps == 0 or self.fps == 1:
            self.fps = 1.0 / 30
        elif self.fps > 1:
            self.fps = 1.0 / self.fps

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
                # frame is already of type ndarray
                # which can be reshaped to 1-d.
                self._buffer = frame.reshape(-1)
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
