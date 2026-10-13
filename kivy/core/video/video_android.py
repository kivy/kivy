import math

from jnius import PythonJavaClass, autoclass, java_method
from kivy.clock import mainthread
from kivy.core.video import VideoBase
from kivy.graphics import Callback, Rectangle
from kivy.graphics.fbo import Fbo
from kivy.graphics.texture import Texture
from kivy.logger import Logger

__all__ = ('VideoAndroid', )

MediaPlayer = autoclass("android.media.MediaPlayer")
MediaMetadataRetriever = autoclass("android.media.MediaMetadataRetriever")
Surface = autoclass("android.view.Surface")
SurfaceTexture = autoclass("android.graphics.SurfaceTexture")

class OnCompletionListener(PythonJavaClass):
    __javainterfaces__ = ["android/media/MediaPlayer$OnCompletionListener"]
    __javacontext__ = "app"

    def __init__(self, callback, **kwargs):
        super(OnCompletionListener, self).__init__(**kwargs)
        self.callback = callback

    @java_method("(Landroid/media/MediaPlayer;)V")
    def onCompletion(self, mp):
        if self.callback:
            self.callback()


class OnErrorListener(PythonJavaClass):
    __javainterfaces__ = ["android/media/MediaPlayer$OnErrorListener"]
    __javacontext__ = "app"

    def __init__(self, callback, **kwargs):
        super(OnErrorListener, self).__init__(**kwargs)
        self.callback = callback

    @java_method("(Landroid/media/MediaPlayer;II)Z")
    def onError(self, mp, what, extra):
        if self.callback:
            return self.callback(what, extra)
        return False


class VideoAndroid(VideoBase):
    _mediaplayer = None

    def __init__(self, **kwargs):
        super(VideoAndroid, self).__init__(**kwargs)
        self._completion_listener = None
        self._rotation = 0

    def load(self):
        self.unload('Loading')

        if not self._filename:
            Logger.error("VideoAndroid: No filename set")
            return

        try:
            self._retriever = MediaMetadataRetriever()
            self._retriever.setDataSource(self._filename)
            _rotation = self._retriever.extractMetadata(
                MediaMetadataRetriever.METADATA_KEY_VIDEO_ROTATION)
            self._rotation = int(_rotation or self._rotation)
            Logger.info(f"VideoAndroid: Rotation: {self._rotation}")
        except Exception as e:
            Logger.warning(f"VideoAndroid: Failed to get rotation: {e}")
            self._rotation = 0

        self._mediaplayer = MediaPlayer()
        self._mediaplayer.setDataSource(self._filename)
        self._completion_listener = OnCompletionListener(self._completion_callback)
        self._mediaplayer.setOnCompletionListener(self._completion_listener)
        self._error_listener = OnErrorListener(self._error_callback)
        self._mediaplayer.setOnErrorListener(self._error_listener)
        self._mediaplayer.prepare()

        width = self._mediaplayer.getVideoWidth()
        height = self._mediaplayer.getVideoHeight()
        self._resolution = _resolution = (width, height)

        self._video_texture = Texture.create(size=_resolution, colorfmt="rgba")

        # SurfaceTexture + Surface
        self._surface_texture = SurfaceTexture(int(self._video_texture.id))
        self._surface_texture.setDefaultBufferSize(width, height)
        self._surface = Surface(self._surface_texture)
        self._mediaplayer.setSurface(self._surface)

        # FBO for Kivy texture
        self._fbo = Fbo(size=_resolution)
        self._fbo['resolution'] = (float(width), float(height))
        self._fbo['angle'] = float(math.radians(self._rotation))
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
            uniform vec2 resolution;
            uniform float angle;  // rotation angle in radians

            // General rotation function
            vec2 rotate(vec2 uv, float angle) {
                float s = sin(angle);
                float c = cos(angle);
                mat2 m = mat2(c, -s, s, c);
                return m * (uv - 0.5) + 0.5;  // rotate around center (0.5, 0.5)
            }

            void main()
            {
                vec2 uv = tex_coord0;

                // Apply rotation
                uv =  clamp(rotate(uv, angle), 0.0, 1.0);

                // Sample from external camera texture
                gl_FragColor = texture2D(texture1, uv);
            }
        '''
        with self._fbo:
            self._texture_cb = Callback(lambda instr: self._video_texture.bind)
            Rectangle(size=_resolution)

        self._texture = self._fbo.texture
        self.dispatch("on_load")

    def unload(self, message='Unloading'):
        Logger.info("VideoAndroid: %s", message)

        # Safely release MediaPlayer
        if self._mediaplayer:
            try:
                self._mediaplayer.release()
            except Exception:
                pass

        self._mediaplayer = None
        self._video_texture = None
        self._fbo = None
        self._texture_cb = None
        self._surface_texture = None
        self._surface = None
        self._retriever = None
        self._state = ""
        self._resolution = (0, 0)
        self._error_listener = None

    # Property overrides
    def _get_position(self):
        pos = 0

        if self._mediaplayer:
            pos = self._mediaplayer.getCurrentPosition() / 1000.0

        return pos

    def _set_position(self, pos):
        if self._mediaplayer:
            dur = self._mediaplayer.getDuration()
            ms = int(max(0.0, min(1.0, pos)) * dur)
            was_playing = self._mediaplayer.isPlaying()
            self._mediaplayer.seekTo(ms)
            if was_playing:
                self._mediaplayer.start()

    def _get_duration(self):
        return self._mediaplayer.getDuration() / 1000.0 if self._mediaplayer else 0

    def _get_state(self):
        return self._state

    def _set_volume(self, volume):
        if self._mediaplayer:
            self._mediaplayer.setVolume(volume, volume)

    def _set_loop(self, loop):
        if self._mediaplayer:
            self._mediaplayer.setLooping(bool(loop))

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
            self._mediaplayer.pause()
            self._set_position(0)
            self._state = ""
            # self.unload()

    def seek(self, percent, precise=True):
        self._set_position(percent)

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

    def _completion_callback(self,):
        self._do_eos()

    @mainthread
    def _do_eos(self):
        if self.eos == "pause":
            self.pause()
        elif self.eos == "stop":
            self.stop()
        elif self.eos == "loop":
            self.stop()
            self.play()

        self.dispatch("on_eos")

    def _error_callback(self, what, extra):
        Logger.error(f"VideoAndroid: MediaPlayer error! What: {what}, Extra: {extra}")
        self.unload()
        return True
