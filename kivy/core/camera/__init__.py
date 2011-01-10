'''
Camera
======

Core class for acquiring the camera, and convert the input to a
:class:`~kivy.graphics.texture.Texture`.
'''

__all__ = ('CameraBase', 'Camera')

from kivy.logger import Logger
from kivy.core import core_select_lib

class CameraBase(object):
    '''Abstract Camera Widget class.

    Concrete camera classes must implement initialization and
    frame capturing to buffer that can be uploaded to gpu.

    :Parameters:
        `size` : tuple (int, int)
            Size at which the image is drawn. If no size is specified,
            it defaults to resolution of the camera image.
        `resolution` : tuple (int, int)
            Resolution to try to request from the camera.
            Used in the gstreamer pipeline by forcing the appsink caps
            to this resolution. If the camera doesnt support the resolution
            a negotiation error might be thrown.
    '''

    def __init__(self, **kwargs):
        # remove this part.
        from kivy.core.gl import GL_RGB

        kwargs.setdefault('stopped', False)
        kwargs.setdefault('resolution', (640, 480))
        kwargs.setdefault('video_src', 0)

        self.stopped        = kwargs.get('stopped')
        self._resolution    = kwargs.get('resolution')
        self._video_src     = kwargs.get('video_src')
        self._buffer        = None
        self._format        = GL_RGB
        self._texture       = None
        self.capture_device = None
        kwargs.setdefault('size', self._resolution)

        super(CameraBase, self).__init__(**kwargs)

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

    def _set_video_src(self, src):
        self._video_src = src
        self.init_camera()
    def _get_video_src(self):
        return self._video_src
    video_src = property(lambda self: self._get_video_src(),
                lambda self, x: self._set_video_src(x),
                doc='Source of the camera')

    def _get_texture(self):
        return self._texture
    texture = property(lambda self: self._get_texture(),
                doc='Return the camera texture with the latest capture')

    def init_camera(self):
        '''Initialise the camera (internal)'''
        pass

    def update(self):
        '''Update the camera (internal)'''
        pass

    def start(self):
        '''Start the camera acquire'''
        self.stopped = False

    def stop(self):
        '''Release the camera'''
        self.stopped = True

    def _copy_to_gpu(self):
        '''Copy the the buffer into the texture'''
        if self._texture is None:
            Logger.debug('Camera: copy_to_gpu() failed, _texture is None !')
            return
        self._texture.blit_buffer(self._buffer, format=self._format)
        self._buffer = None

# Load the appropriate provider
Camera = core_select_lib('camera', (
    ('gstreamer', 'camera_gstreamer', 'CameraGStreamer'),
    ('opencv', 'camera_opencv', 'CameraOpenCV'),
    ('videocapture', 'camera_videocapture', 'CameraVideoCapture'),
))
