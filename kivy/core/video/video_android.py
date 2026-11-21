'''
Android video provider
======================

Plays video through androidx.media3 ExoPlayer. See :class:`VideoAndroid`.
'''

__all__ = ('VideoAndroid', )

import struct
import threading
import weakref

from jnius import JavaException, PythonJavaClass, autoclass, java_method

from kivy.core.video import VideoBase
from kivy.graphics import Callback, Rectangle
from kivy.graphics.fbo import Fbo
from kivy.graphics.opengl import (
    GL_TEXTURE0,
    glActiveTexture,
    glBindTexture,
    glDeleteTextures,
    glGenTextures,
)
from kivy.graphics.texture import Texture
from kivy.graphics.transformation import Matrix
from kivy.logger import Logger
from kivy.mobile._platform.android import get_app_context, run_on_ui_thread
from kivy.utils import path_to_str

File = autoclass('java.io.File')
Uri = autoclass('android.net.Uri')
Looper = autoclass('android.os.Looper')
Handler = autoclass('android.os.Handler')
Surface = autoclass('android.view.Surface')
SurfaceTexture = autoclass('android.graphics.SurfaceTexture')

GL_TEXTURE_EXTERNAL_OES = 0x8D65

# The transform decoders usually supply (a vertical flip), used when the
# SurfaceTexture's can't be read: with the shader's own flip, it samples the
# frame untransformed.
_DEFAULT_TRANSFORM = (
    1.0, 0.0, 0.0, 0.0,
    0.0, -1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 1.0, 0.0, 1.0,
)

# No Android-specific options exist yet; kept as an explicit, empty set so
# unknown keys are reported the same way as for the other providers.
_KNOWN_OPTIONS = frozenset()
# VideoBase's own keyword arguments. The Video widget also passes them in
# options, for apps that set ``eos`` there, so they aren't unknown.
_BASE_KWARGS = frozenset({'filename', 'eos', 'async', 'autoplay', 'fps'})

_MISSING_MEDIA3 = (
    'androidx.media3 ExoPlayer is not in this app. Add the Maven dependency '
    'androidx.media3:media3-exoplayer to the Android build. If it is '
    'already there and this is a release build, R8 removed it: add the '
    'keep rule "-keep class androidx.media3.** { *; }". See "Playing '
    'video" in the Android packaging guide.')

_FS_EXTERNAL = '''
#extension GL_OES_EGL_image_external : require
#ifdef GL_ES
    precision highp float;
#endif

varying vec4 frag_color;
varying vec2 tex_coord0;

uniform sampler2D texture0;
uniform samplerExternalOES texture1;
uniform mat4 tex_matrix;

void main(void) {
    // The SurfaceTexture transform expects coordinates that start at the
    // bottom-left of the output; in Kivy's FBO, tex_coord0 runs the other way.
    vec2 st = vec2(tex_coord0.x, 1.0 - tex_coord0.y);
    vec2 uv = (tex_matrix * vec4(st, 0.0, 1.0)).xy;
    gl_FragColor = texture2D(texture1, uv);
}
'''


class _Media3:
    '''The androidx.media3 classes the provider uses. They are only in the
    APK when the app declares the Maven dependency, so they are resolved on
    first use rather than at import.
    '''

    def __init__(self):
        self.Builder = autoclass('androidx.media3.exoplayer.ExoPlayer$Builder')
        self.MediaItem = autoclass('androidx.media3.common.MediaItem')
        self.AudioAttributesBuilder = autoclass(
            'androidx.media3.common.AudioAttributes$Builder')
        self.SeekParameters = autoclass(
            'androidx.media3.exoplayer.SeekParameters')
        C = autoclass('androidx.media3.common.C')
        self.USAGE_MEDIA = C.USAGE_MEDIA
        self.AUDIO_CONTENT_TYPE_MOVIE = C.AUDIO_CONTENT_TYPE_MOVIE
        Player = autoclass('androidx.media3.common.Player')
        self.STATE_IDLE = Player.STATE_IDLE
        self.STATE_BUFFERING = Player.STATE_BUFFERING
        self.STATE_ENDED = Player.STATE_ENDED


_media3 = None
_handler = None


def _get_media3():
    global _media3
    if _media3 is None:
        _media3 = _Media3()
    return _media3


def _main_handler():
    global _handler
    if _handler is None:
        _handler = Handler(Looper.getMainLooper())
    return _handler


def _to_uri(filename):
    if '://' in filename:
        return Uri.parse(filename)
    return Uri.fromFile(File(filename))


def _describe_error(error):
    '''One line for a ``PlaybackException``: its code name, its message, and
    the message of its cause, which is usually the specific one (a path, an
    HTTP status).
    '''
    message = error.getErrorCodeName()
    if error.getMessage():
        message += ': {}'.format(error.getMessage())
    cause = error.getCause()
    if cause is not None and cause.getMessage():
        message += ' ({})'.format(cause.getMessage())
    return message


def _read_player(player):
    '''Snapshot of everything ``_update()`` needs. Must run on the player's
    application thread, the Android UI thread.
    '''
    width = height = 0
    size = player.getVideoSize()
    if size.width > 0 and size.height > 0:
        ratio = size.pixelWidthHeightRatio
        width = int(round(size.width * ratio)) if ratio > 0 else size.width
        height = size.height
    else:
        video_format = player.getVideoFormat()
        if (video_format is not None
                and video_format.width > 0 and video_format.height > 0):
            width, height = video_format.width, video_format.height
            if video_format.rotationDegrees in (90, 270):
                width, height = height, width
    error = player.getPlayerError()
    return {
        'state': player.getPlaybackState(),
        'position': player.getCurrentPosition(),
        'duration': player.getDuration(),
        'size': (width, height),
        'error': None if error is None else _describe_error(error),
    }


def _java_bytes(array):
    try:
        return bytes(array)
    except (TypeError, ValueError):
        # A plain list of signed Java bytes.
        return bytes(value & 0xFF for value in array)


class _PollRunnable(PythonJavaClass):
    __javainterfaces__ = ['java/lang/Runnable']
    __javacontext__ = 'app'

    def __init__(self, video):
        super().__init__()
        self._video = weakref.ref(video)

    @java_method('()V')
    def run(self):
        video = self._video()
        if video is not None:
            video._poll()


class VideoAndroid(VideoBase):
    '''Implementation of :class:`~kivy.core.video.VideoBase` using
    androidx.media3 ExoPlayer on Android.

    **Required dependency.** ExoPlayer is not part of Android: the app has
    to add the Maven dependency ``androidx.media3:media3-exoplayer`` to its
    build (tested with 1.11.1, which needs compile SDK 36). Without it,
    every video fires ``on_error`` with a message that says so. Add
    ``androidx.media3:media3-exoplayer-hls`` or ``-dash`` as well to play
    HLS (``.m3u8``) or DASH (``.mpd``) streams. Network sources need the
    ``INTERNET`` permission, and a release build with R8 enabled needs a
    keep rule for ``androidx.media3``. See "Playing video" in the Android
    packaging guide for each toolchain's settings.

    **Sources.** A file path, or a URI with a scheme: ``file://``,
    ``http://``, ``https://`` and ``content://`` (MediaStore, the Storage
    Access Framework, a share intent).

    **Supported formats.** Decoding uses the device's own decoders
    (MediaCodec); Kivy ships none. H.264 video with AAC audio plays on every
    device. HEVC, VP9 and AV1 play on most recent devices.

    **Rendering.** Frames are decoded into a ``SurfaceTexture`` and drawn
    into a :class:`~kivy.graphics.fbo.Fbo` on the GPU, without a copy
    through the CPU. The texture transform the decoder supplies is applied,
    so cropping and rotation recorded in the file are honored.

    **Threading.** ExoPlayer may only be called from the thread it belongs
    to, which here is the Android UI thread, not Kivy's. The provider posts
    every call to that thread and reads the player's state from it once per
    frame, so none of this is visible to the app and Kivy's thread never
    waits for the UI thread.

    **Audio and app lifecycle.** The player requests audio focus, so
    playback pauses for a phone call and turns down for notifications. When the
    app is paused it pauses playback, and resumes it with the app.

    A video that can't be played (a missing file, an unsupported format, a
    corrupt file, a network error, or the missing dependency above) is
    logged, playback stops, and ``on_error`` fires with the reason (see
    :meth:`~kivy.core.video.VideoBase.on_error`).

    The provider has no ``options`` keys. Unknown keys are logged as a
    warning at construction time and otherwise ignored.

    .. seealso::
        :attr:`kivy.uix.video.Video.options` -- the widget-level property
        most apps use to pass provider options.

    .. versionchanged:: 3.0.0
        Rewritten on androidx.media3 ExoPlayer, replacing
        ``android.media.MediaPlayer``, and registered as the ``android``
        provider.
    '''

    def __init__(self, **kwargs):
        # VideoBase.__init__ calls load(), so everything load() touches has
        # to exist first.
        self._lock = threading.Lock()
        self._player = None
        self._generation = 0
        self._snapshot = None
        self._async_error = None
        self._pending_error = None
        self._error_reported = False
        self._cmd_seq = 0
        self._applied_seq = 0
        self._seek_override = None
        self._eos_handled = False
        self._poll_pending = False
        self._poll_runnable = _PollRunnable(self)
        self._oes_id = None
        self._surface_texture = None
        self._surface = None
        self._fbo = None
        self._fbo_size = (0, 0)
        self._texture_cb = None
        self._transform = [0.0] * 16
        self._logged_identity = False
        self._last_timestamp = 0
        self._loaded = False
        self._resume_play = False
        self._app = None
        self._app_callbacks = None
        super().__init__(**kwargs)
        unknown = sorted(set(self._options) - _KNOWN_OPTIONS - _BASE_KWARGS)
        if unknown:
            Logger.warning(
                'VideoAndroid: ignoring unknown options keys {!r}; known '
                'keys: {!r}'.format(unknown, sorted(_KNOWN_OPTIONS)))

    # ---------- Loading ----------

    def load(self):
        Logger.debug('VideoAndroid: Load <{}>'.format(self._filename))
        self._release_player()
        # Failures found here are reported by _update() on the first tick:
        # load() runs while the Video widget is still constructing this
        # object, before it has bound on_error.
        self._error_reported = False
        if not self._filename:
            return
        try:
            media3 = _get_media3()
        except JavaException:
            self._pending_error = _MISSING_MEDIA3
            return
        try:
            context = get_app_context()
        except Exception:
            context = None
        if context is None:
            self._pending_error = 'no Android Activity to play video in'
            return
        try:
            self._create_video_surface()
            builder = media3.Builder(context)
            # The player belongs to this Looper's thread: every later call
            # into it has to be made there, which is what _post() does.
            builder.setLooper(Looper.getMainLooper())
            attributes = (
                media3.AudioAttributesBuilder()
                .setUsage(media3.USAGE_MEDIA)
                .setContentType(media3.AUDIO_CONTENT_TYPE_MOVIE)
                .build())
            builder.setAudioAttributes(attributes, True)
            self._player = builder.build()
            media_item = media3.MediaItem.fromUri(_to_uri(self._filename))
        except JavaException as e:
            self._release_player()
            self._pending_error = 'could not create the player: {}'.format(e)
            return

        surface = self._surface
        volume = float(self._volume)

        def prepare(player):
            player.setVideoSurface(surface)
            player.setVolume(volume)
            player.setMediaItem(media_item)
            player.prepare()

        self._post(prepare)
        self._bind_app()

    def unload(self):
        self._release_player()
        self._unbind_app()
        super().unload()

    def _release_player(self):
        player = self._player
        surface = self._surface
        surface_texture = self._surface_texture
        oes_id = self._oes_id
        self._player = None
        self._surface = self._surface_texture = self._oes_id = None
        with self._lock:
            self._generation += 1
            self._snapshot = None
            self._async_error = None
        self._pending_error = None
        self._seek_override = None
        self._eos_handled = False
        self._fbo = None
        self._fbo_size = (0, 0)
        self._texture_cb = None
        self._texture = None
        self._loaded = False

        if player is not None or surface is not None:
            # In one call on the UI thread, so the player is released
            # before the surface it draws into. Calls posted earlier run
            # first, so none of them reaches a released player.
            def release():
                if player is not None:
                    player.release()
                if surface is not None:
                    surface.release()
                if surface_texture is not None:
                    surface_texture.release()

            try:
                run_on_ui_thread(release)
            except Exception as e:
                Logger.debug(
                    'VideoAndroid: could not release the player: {}'.format(e))
        if oes_id is not None:
            self._delete_gl_texture(oes_id)

    # ---------- Talking to the player ----------

    def _post(self, fn):
        '''Run ``fn(player)`` on the player's thread, the Android UI thread.

        Calls run in the order they are posted. Nothing waits for them; a
        failure is reported by the next ``_update()``.
        '''
        player = self._player
        if player is None:
            return
        self._cmd_seq += 1
        seq = self._cmd_seq
        generation = self._generation

        def run():
            try:
                fn(player)
            except Exception as e:
                self._set_async_error(str(e), generation)
            finally:
                self._applied_seq = seq

        try:
            run_on_ui_thread(run)
        except Exception as e:
            self._pending_error = (
                'could not reach the Android UI thread: {}'.format(e))

    def _set_async_error(self, error, generation):
        with self._lock:
            if generation == self._generation and self._async_error is None:
                self._async_error = error

    def _request_poll(self):
        if not self._poll_pending:
            self._poll_pending = True
            _main_handler().post(self._poll_runnable)

    def _poll(self):
        # On the Android UI thread, posted by _request_poll().
        with self._lock:
            generation = self._generation
        try:
            player = self._player
            if player is None:
                return
            snapshot = _read_player(player)
            snapshot['seq'] = self._applied_seq
            with self._lock:
                if generation == self._generation:
                    self._snapshot = snapshot
        except Exception as e:
            self._set_async_error(str(e), generation)
        finally:
            self._poll_pending = False

    # ---------- Frame pump ----------

    def _update(self, dt):
        if self._error_reported:
            return
        error = self._pending_error
        with self._lock:
            error = error or self._async_error
            snapshot = self._snapshot
        if error is None and snapshot is not None:
            error = snapshot['error']
        if error is not None:
            self._error_reported = True
            Logger.error('VideoAndroid: <{}>: {}'.format(self._filename, error))
            self._do_error(error)
            return
        if self._player is None:
            return

        self._request_poll()
        if snapshot is None:
            self._set_buffering(self._state == 'playing')
            return
        media3 = _media3
        state = snapshot['state']
        self._set_buffering(
            self._state == 'playing'
            and state in (media3.STATE_IDLE, media3.STATE_BUFFERING))

        width, height = snapshot['size']
        if width and height and (width, height) != self._fbo_size:
            if not self._build_fbo(width, height):
                return
        if self._fbo is not None:
            try:
                drew = self._draw_frame()
            except JavaException as e:
                self._pending_error = 'could not draw the video: {}'.format(e)
                return
            if drew:
                self._texture = self._fbo.texture
                if not self._loaded:
                    self._loaded = True
                    self.dispatch('on_load')
                self.dispatch('on_frame')

        # The snapshot lags the player by a tick, so after a loop's seek it
        # can still say ENDED once; _eos_handled stays set until it doesn't.
        if state == media3.STATE_ENDED:
            if not self._eos_handled:
                self._eos_handled = True
                if self._state != '':
                    self._do_eos()
        else:
            self._eos_handled = False

    def _set_buffering(self, buffering):
        if buffering != self._buffering:
            self._buffering = buffering
            self.dispatch('on_buffering', buffering)

    # ---------- GL ----------

    def _create_video_surface(self):
        # A bare texture name: SurfaceTexture binds it to
        # GL_TEXTURE_EXTERNAL_OES, and a name that was ever bound to
        # GL_TEXTURE_2D (as a kivy Texture's is) can't change target.
        self._oes_id = glGenTextures(1)[0]
        self._surface_texture = SurfaceTexture(self._oes_id)
        self._surface = Surface(self._surface_texture)
        self._last_timestamp = 0

    def _delete_gl_texture(self, texture_id):
        glDeleteTextures(1, struct.pack('I', texture_id))

    def _build_fbo(self, width, height):
        try:
            fbo = Fbo(size=(width, height))
            fbo.shader.fs = _FS_EXTERNAL
            compiled = fbo.shader.success
        except Exception:
            compiled = False
        if not compiled:
            self._pending_error = (
                'the GPU driver could not compile the video shader '
                '(GL_OES_EGL_image_external)')
            return False
        fbo['texture1'] = 1
        fbo['tex_matrix'] = Matrix()
        with fbo:
            self._texture_cb = Callback(self._bind_video_texture)
            Rectangle(size=(width, height))
        self._fbo = fbo
        self._fbo_size = (width, height)
        return True

    def _bind_video_texture(self, instr):
        glActiveTexture(GL_TEXTURE0 + 1)
        glBindTexture(GL_TEXTURE_EXTERNAL_OES, self._oes_id)
        glActiveTexture(GL_TEXTURE0)

    def _draw_frame(self):
        '''Latch the newest decoded frame and draw it into the FBO. Returns
        whether there was a new frame.
        '''
        surface_texture = self._surface_texture
        surface_texture.updateTexImage()
        timestamp = surface_texture.getTimestamp()
        if timestamp == self._last_timestamp:
            return False
        self._last_timestamp = timestamp
        surface_texture.getTransformMatrix(self._transform)
        matrix = Matrix()
        if any(self._transform):
            matrix.set(flat=self._transform)
        else:
            matrix.set(flat=_DEFAULT_TRANSFORM)
            if not self._logged_identity:
                self._logged_identity = True
                Logger.info(
                    'VideoAndroid: no texture transform from the decoder; '
                    'drawing frames untransformed')
        self._fbo['tex_matrix'] = matrix
        self._texture_cb.ask_update()
        self._fbo.draw()
        return True

    # ---------- Controls ----------

    def play(self):
        super().play()

        def start(player):
            if player.getPlaybackState() == _media3.STATE_ENDED:
                player.seekTo(0)
            player.play()

        self._post(start)

    def pause(self):
        super().pause()
        self._post(lambda player: player.pause())

    def stop(self):
        super().stop()

        def rewind(player):
            player.pause()
            player.seekTo(0)

        self._post(rewind)
        if self._player is not None:
            self._seek_override = (self._cmd_seq, 0.0)

    def seek(self, percent, precise=True):
        duration = self._get_duration()
        if self._player is None or duration <= 0:
            return
        position_ms = int(min(1.0, max(0.0, float(percent))) * duration * 1000)
        seek_parameters = _media3.SeekParameters
        parameters = (
            seek_parameters.EXACT if precise else seek_parameters.CLOSEST_SYNC)

        def seek_to(player):
            player.setSeekParameters(parameters)
            player.seekTo(position_ms)

        self._post(seek_to)
        # Report the target until a snapshot taken after the seek arrives,
        # so a slider bound to position doesn't jump back for a tick.
        self._seek_override = (self._cmd_seq, position_ms / 1000.0)

    def _get_position(self):
        with self._lock:
            snapshot = self._snapshot
        override = self._seek_override
        if override is not None:
            seq, seconds = override
            if snapshot is None or snapshot['seq'] < seq:
                return seconds
            self._seek_override = None
        if snapshot is None:
            return 0.0
        return max(0, snapshot['position']) / 1000.0

    def _get_duration(self):
        with self._lock:
            snapshot = self._snapshot
        if snapshot is None:
            return 0.0
        # C.TIME_UNSET, a large negative number, until the duration is known.
        return max(0, snapshot['duration']) / 1000.0

    def _set_volume(self, volume):
        self._volume = volume
        value = float(volume)
        self._post(lambda player: player.setVolume(value))

    # ---------- App lifecycle ----------

    def _bind_app(self):
        from kivy.app import App
        app = App.get_running_app()
        if app is None or app is self._app:
            return
        self._unbind_app()
        ref = weakref.ref(self)

        def on_pause(*args):
            video = ref()
            if video is not None:
                video._on_app_pause()

        def on_resume(*args):
            video = ref()
            if video is not None:
                video._on_app_resume()

        app.fbind('on_pause', on_pause)
        app.fbind('on_resume', on_resume)
        self._app = app
        self._app_callbacks = (on_pause, on_resume)

    def _unbind_app(self):
        app, self._app = self._app, None
        if app is not None:
            on_pause, on_resume = self._app_callbacks
            app.funbind('on_pause', on_pause)
            app.funbind('on_resume', on_resume)
        self._app_callbacks = None

    def _on_app_pause(self):
        if self._player is None:
            return
        self._resume_play = self._state == 'playing'
        self._post(lambda player: player.pause())

    def _on_app_resume(self):
        if self._player is None:
            return
        # The GL context may have been lost while paused, taking the
        # texture name with it, so draw into a fresh surface. The old name
        # isn't deleted: after a context loss it may already belong to
        # another texture.
        old_surface = self._surface
        old_surface_texture = self._surface_texture
        self._create_video_surface()
        surface = self._surface

        def swap(player):
            player.setVideoSurface(surface)
            old_surface.release()
            old_surface_texture.release()

        self._post(swap)
        if self._resume_play:
            self._resume_play = False
            self._post(lambda player: player.play())

    # ---------- Thumbnails ----------

    @classmethod
    def generate_thumbnail(cls, filename, time, size=None):
        '''Decode the frame at `time` seconds with Android's
        ``MediaMetadataRetriever``, without creating a player. Returns
        ``None`` if the file can't be opened or has no frame there.

        .. versionadded:: 3.0.0
        '''
        filename = path_to_str(filename)
        MediaMetadataRetriever = autoclass(
            'android.media.MediaMetadataRetriever')
        retriever = None
        try:
            retriever = MediaMetadataRetriever()
            scheme = filename.split('://', 1)[0].lower() \
                if '://' in filename else ''
            if scheme in ('http', 'https'):
                retriever.setDataSource(
                    filename, autoclass('java.util.HashMap')())
            elif scheme in ('', 'file'):
                retriever.setDataSource(
                    filename if not scheme else Uri.parse(filename).getPath())
            else:
                retriever.setDataSource(get_app_context(), Uri.parse(filename))
            bitmap = retriever.getFrameAtTime(
                int(max(0.0, float(time)) * 1000000),
                MediaMetadataRetriever.OPTION_CLOSEST)
            if bitmap is None:
                Logger.warning(
                    'VideoAndroid: no frame at {}s in <{}>'.format(
                        time, filename))
                return None
            return _bitmap_to_texture(bitmap, size)
        except Exception as e:
            Logger.warning(
                'VideoAndroid: could not make a thumbnail of <{}>: {}'.format(
                    filename, e))
            return None
        finally:
            if retriever is not None:
                try:
                    retriever.release()
                except JavaException:
                    pass


def _bitmap_to_texture(bitmap, size):
    Bitmap = autoclass('android.graphics.Bitmap')
    BitmapConfig = autoclass('android.graphics.Bitmap$Config')
    ByteBuffer = autoclass('java.nio.ByteBuffer')
    if size is not None:
        bitmap = Bitmap.createScaledBitmap(
            bitmap, int(size[0]), int(size[1]), True)
    config = bitmap.getConfig()
    if config is None or config.name() != 'ARGB_8888':
        bitmap = bitmap.copy(BitmapConfig.ARGB_8888, False)
    width, height = bitmap.getWidth(), bitmap.getHeight()
    buffer = ByteBuffer.allocate(width * height * 4)
    bitmap.copyPixelsToBuffer(buffer)
    texture = Texture.create(size=(width, height), colorfmt='rgba')
    texture.blit_buffer(
        _java_bytes(buffer.array()), colorfmt='rgba', bufferfmt='ubyte')
    texture.flip_vertical()
    return texture
