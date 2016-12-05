'''
Camera
======

Core class for acquiring the camera and converting its input into a
:class:`~kivy.graphics.texture.Texture`.

.. versionchanged:: 1.8.0
    There is now 2 distinct Gstreamer implementation: one using Gi/Gst
    working for both Python 2+3 with Gstreamer 1.0, and one using PyGST
    working only for Python 2 + Gstreamer 0.10.
'''

__all__ = ('CameraBase', 'Camera')


from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.logger import Logger
from kivy.core import core_select_lib


class CameraBase(EventDispatcher):
    '''Abstract Camera Widget class.

    Concrete camera classes must implement initialization and
    frame capturing to a buffer that can be uploaded to the gpu.

    :Parameters:
        `index`: int
            Source index of the camera.
        `size`: tuple (int, int)
            Size at which the image is drawn. If no size is specified,
            it defaults to the resolution of the camera image.
        `resolution`: tuple (int, int)
            Resolution to try to request from the camera.
            Used in the gstreamer pipeline by forcing the appsink caps
            to this resolution. If the camera doesnt support the resolution,
            a negotiation error might be thrown.

    :Events:
        `on_load`
            Fired when the camera is loaded and the texture has become
            available.
        `on_texture`
            Fired each time the camera texture is updated.
    '''

    __events__ = ('on_load', 'on_texture')

    def __init__(self, **kwargs):
        kwargs.setdefault('stopped', False)
        kwargs.setdefault('resolution', (640, 480))
        kwargs.setdefault('index', 0)

        self.stopped = kwargs.get('stopped')
        self._resolution = kwargs.get('resolution')
        self._index = kwargs.get('index')
        self._buffer = None
        self._format = 'rgb'
        self._texture = None
        self.capture_device = None
        kwargs.setdefault('size', self._resolution)

        super(CameraBase, self).__init__()

        self.init_camera()

        if not self.stopped:
            self.start()

    def _set_resolution(self, res):
        self._resolution = res
        self.init_camera()

    def _get_resolution(self):
        return self._resolution

    resolution = property(lambda self: self._get_resolution(),
                          lambda self, x: self._set_resolution(x),
                          doc='Resolution of camera capture (width, height)')

    def _set_index(self, x):
        if x == self._index:
            return
        self._index = x
        self.init_camera()

    def _get_index(self):
        return self._x

    index = property(lambda self: self._get_index(),
                     lambda self, x: self._set_index(x),
                     doc='Source index of the camera')

    def _get_texture(self):
        return self._texture
    texture = property(lambda self: self._get_texture(),
                       doc='Return the camera texture with the latest capture')

    def init_camera(self):
        '''Initialise the camera (internal)'''
        pass

    def start(self):
        '''Start the camera acquire'''
        self.stopped = False

    def stop(self):
        '''Release the camera'''
        self.stopped = True

    def _update(self, dt):
        '''Update the camera (internal)'''
        pass

    def _copy_to_gpu(self):
        '''Copy the the buffer into the texture'''
        if self._texture is None:
            Logger.debug('Camera: copy_to_gpu() failed, _texture is None !')
            return
        self._texture.blit_buffer(self._buffer, colorfmt=self._format)
        self._buffer = None
        self.dispatch('on_texture')

    def on_texture(self):
        pass

    def on_load(self):
        pass

# Load the appropriate providers
providers = ()

if platform == 'win':
    providers += (('videocapture', 'camera_videocapture',
                   'CameraVideoCapture'), )
elif platform == 'macosx':
    providers += (('avfoundation', 'camera_avfoundation',
                   'CameraAVFoundation'), )
elif platform == 'android':
    providers += (('android', 'camera_android', 'CameraAndroid'), )
else:
    #providers += (('gi', 'camera_gi', 'CameraGi'), )
    providers += (('pygst', 'camera_pygst', 'CameraPyGst'), )

providers += (('opencv', 'camera_opencv', 'CameraOpenCV'), )


Camera = core_select_lib('camera', (providers))
