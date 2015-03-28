from jnius import autoclass
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.graphics import Fbo, BindTexture, Rectangle
from kivy.core.camera import CameraBase


Camera = autoclass('android.hardware.Camera')
SurfaceTexture = autoclass('android.graphics.SurfaceTexture')
GL_TEXTURE_EXTERNAL_OES = 36197


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
        self._camera_texture.bind()
        self._surface_texture = SurfaceTexture(int(self._camera_texture.id))
        self._android_camera.setPreviewTexture(self._surface_texture)

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

        fbo = Fbo(size=self._resolution)
        fbo.shader.fs = '''
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
        with fbo:
            BindTexture(texture=self._camera_texture, index=1)
            Rectangle(size=self._resolution)
        fbo.draw()
        self._texture = fbo.texture
        self.dispatch('on_load')
        self.dispatch('on_texture')
