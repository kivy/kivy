from jnius import autoclass
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.graphics import Fbo, BindTexture, Rectangle
from kivy.core.camera import CameraBase
from kivy.graphics.opengl import glReadPixels, GL_RGB, GL_UNSIGNED_BYTE


Camera = autoclass('android.hardware.Camera')
SurfaceTexture = autoclass('android.graphics.SurfaceTexture')
GL_TEXTURE_EXTERNAL_OES = autoclass('android.opengl.GLES11Ext').GL_TEXTURE_EXTERNAL_OES


class CameraAndroid(CameraBase):
    """
    Implementation of CameraBase using Android API
    """

    def __init__(self, **kwargs):
        self._android_camera = None
        super(CameraAndroid, self).__init__(**kwargs)

    def init_camera(self):
        self._android_camera = Camera.open(self._index)
        params = self._android_camera.getParameters()
        width, height = self._resolution
        params.setPreviewSize(width, height)
        self._android_camera.setParameters(params)
        #self._android_camera.setDisplayOrientation()
        self.fps = 30.

        self._camera_texture = Texture(width=width, height=height, target=GL_TEXTURE_EXTERNAL_OES, colorfmt='rgba')
        #self._camera_texture.bind()
        self._surface_texture = SurfaceTexture(int(self._camera_texture.id))
        self._android_camera.setPreviewTexture(self._surface_texture)

        self._fbo = Fbo(size=self._resolution)
        self._fbo.shader.fs = '''
            #extension GL_OES_EGL_image_external : require
            #ifdef GL_ES
                precision highp float;
            #endif

            /* Outputs from the vertex shader */
            varying vec4 frag_color;
            varying vec2 tex_coord0;

            /* uniform texture samplers */
            uniform sampler2D texture0;
            uniform samplerExternalOES texture1;

            void main()
            {
                gl_FragColor = texture2D(texture1, tex_coord0);
            }
        '''

    def _refresh_fbo(self):
        self._fbo.clear()
        with self._fbo:
            #BindTexture(texture=self._camera_texture, index=1)
            Rectangle(size=self._resolution)
        self._fbo.draw()

    def start(self):
        super(CameraAndroid, self).start()
        self._android_camera.startPreview()
        Clock.unschedule(self._update)
        Clock.schedule_interval(self._update, 1./self.fps)

    def stop(self):
        super(CameraAndroid, self).stop()
        Clock.unschedule(self._update)
        self._android_camera.stopPreview()

    def _update(self, dt):
        self._surface_texture.updateTexImage()
        self._refresh_fbo()
        if self._texture is None:
            self._texture = self._fbo.texture
            self.dispatch('on_load')
        self._copy_to_gpu()

    def _copy_to_gpu(self):
        """
        A dummy placeholder (the image is already in GPU) to be consistent with other providers.
        """
        self.dispatch('on_texture')

    @property
    def frame_data(self):
        """
        Image data of current frame, in RGB format
        """
        ##buf = self._texture.pixels  # very slow
        ##buf = self._fbo.pixels  # still slow
        self._fbo.bind()
        buf = glReadPixels(0, 0, self._resolution[0], self._resolution[1], GL_RGB, GL_UNSIGNED_BYTE)
        self._fbo.release()
        return buf
