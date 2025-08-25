# Author : Sk Sahil (Sahil-pixel)
# Video core provider for Android using Android MediaPlayer & OpenGL Texture
# https://github.com/Sahil-pixel/AndroidVideo4Kivy/blob/main/android_video.py


__all__ = ('VideoAndroid', )
from jnius import autoclass
from kivy.clock import mainthread
from kivy.logger import Logger
from kivy.core.video import VideoBase
from kivy.graphics import Rectangle, Callback
from kivy.graphics.texture import Texture
from kivy.graphics.fbo import Fbo

MediaPlayer = autoclass("android.media.MediaPlayer")
Surface = autoclass("android.view.Surface")
SurfaceTexture = autoclass("android.graphics.SurfaceTexture")
GLES11Ext = autoclass("android.opengl.GLES11Ext")



Logger.info('VideoAndroid: Using Android MediaPlayer')


class VideoAndroid(VideoBase):
    _mediaplayer=None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mediaplayer = None
        self._surface_texture = None
        self._surface = None
        self._video_texture = None
        self._fbo = None
        self._texture_cb = None
        self._resolution = (0, 0)

    def load(self):
        self.unload()
        if not self._filename:
            Logger.error("VideoAndroid: No filename set")
            return

        self._mediaplayer = MediaPlayer()
        self._mediaplayer.setDataSource(self._filename)
        self._mediaplayer.prepare()

        w = self._mediaplayer.getVideoWidth()
        h = self._mediaplayer.getVideoHeight()
        self._resolution = (w, h)

        # Create OES texture
        GL_TEXTURE_EXTERNAL_OES = GLES11Ext.GL_TEXTURE_EXTERNAL_OES
        self._video_texture = Texture(
            width=w, height=h, target=GL_TEXTURE_EXTERNAL_OES, colorfmt="rgba")
        self._video_texture.wrap = "clamp_to_edge"

        # SurfaceTexture + Surface
        self._surface_texture = SurfaceTexture(int(self._video_texture.id))
        self._surface_texture.setDefaultBufferSize(w, h)
        self._surface = Surface(self._surface_texture)
        self._mediaplayer.setSurface(self._surface)

        # FBO for Kivy texture
        self._fbo = Fbo(size=(w, h))
        self._fbo.shader.fs = """
            #extension GL_OES_EGL_image_external : require
            #ifdef GL_ES
                precision highp float;
            #endif
            varying vec4 frag_color;
            varying vec2 tex_coord0;
            uniform samplerExternalOES texture1;
            void main() {
                gl_FragColor = texture2D(texture1, tex_coord0);
            }
        """
        with self._fbo:
            self._texture_cb = Callback(
                lambda instr: self._video_texture.bind)
            Rectangle(size=(w, h))

        self._texture = self._fbo.texture
        self.dispatch("on_load")

    def unload(self):
        if self._mediaplayer:
            try:
                self._mediaplayer.release()
            except Exception:
                pass
        del self._mediaplayer
        del self._video_texture
        del self._fbo
        del self._texture_cb
        del self._surface_texture
        del self._surface
        self._texture = None
        self._state = ""
        self._resolution = (0, 0)

    # Property overrides
    def _get_position(self):
        return self._mediaplayer.getCurrentPosition() / 1000.0 if self._mediaplayer else 0

    def _set_position(self, pos):
        if self._mediaplayer:
            self._mediaplayer.seekTo(int(pos * 1000))

    def _get_duration(self):
        return self._mediaplayer.getDuration() / 1000.0 if self._mediaplayer else 0

    def _set_volume(self, volume):
        if self._mediaplayer:
            self._mediaplayer.setVolume(volume, volume)

    # Controls
    def play(self):
        if not self._mediaplayer:
            self.load()
        if self._mediaplayer and self._state != "playing":
            self._mediaplayer.start()
            self._state = "playing"

    def pause(self):
        if self._mediaplayer and self._state == "playing":
            self._mediaplayer.pause()
            self._state = "paused"

    def stop(self):
        if self._mediaplayer:
            self._mediaplayer.stop()
        self._state = "stopped"

    # Called automatically by VideoBase
    def _update(self, dt):
        if not self._surface_texture:
            return
        self._surface_texture.updateTexImage()
        self._texture_cb.ask_update()
        self._fbo.draw()
        self._texture = self._fbo.texture
        if self._texture:
            self.dispatch("on_frame")

        if self._mediaplayer and not self._mediaplayer.isPlaying():
            self._do_eos()

    @mainthread
    def _do_eos(self):
        if self.eos == "pause":
            self.pause()
        elif self.eos == "stop":
            self.stop()
        elif self.eos == "loop":
            self.position = 0
            self.play()
        self.dispatch("on_eos")

