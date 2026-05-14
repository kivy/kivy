# distutils: language = c++
'''
AVFoundation Video
==================

Video implementation using the AVFoundation framework, the default video
provider on macOS (and, in a follow-up PR, iOS).

.. versionadded:: 3.0.0
'''

__all__ = ('VideoAVFoundation',)


cdef extern from "video_avfoundation_implem.mm":
    cppclass VideoFrame:
        char *data
        unsigned int datasize
        unsigned int rowsize
        int width
        int height
        double pts
        unsigned int gl_texture_id
        unsigned int gl_target

    cppclass VideoPlayer:
        VideoPlayer(const char *url)

        void load()
        void play()
        void pause()
        void stop()
        void unload()
        void seek(double seconds, bint precise)

        double position()
        double duration()
        void setVolume(double v)

        bint hasNewFrame()
        VideoFrame *retrieveFrame()

        bint isEOS()
        bint isBuffering()

        void setAutomaticallyWaitsToMinimizeStalling(bint wait)
        void setForceCPUCopy(bint forced)

        @staticmethod
        VideoFrame *generateThumbnail(
            const char *url, double t, int w, int h)


from cython cimport view as cyview
from kivy.clock import Clock
from kivy.core.video import VideoBase
from kivy.graphics.texture import Texture
from kivy.logger import Logger


# Whitelist of options keys this provider honors. Keys outside this set
# are logged as a warning at construction time and otherwise ignored;
# the warning catches typos cheaply without surprising apps that
# legitimately stash extra metadata in the dict.
_KNOWN_OPTIONS = frozenset({
    'automatically_waits_to_minimize_stalling',
    'force_cpu_copy',
})


cdef _frame_to_texture(VideoFrame *frame, existing_texture):
    '''Wrap or update a Kivy Texture from a VideoFrame.

    Returns the Texture (possibly the same instance as
    ``existing_texture``).
    '''
    cdef int width = frame.width
    cdef int height = frame.height
    cdef unsigned int datasize = frame.datasize
    cdef cyview.array cyarr
    cdef unsigned char *buf
    cdef unsigned int i
    cdef unsigned char b

    if frame.gl_texture_id != 0:
        # Zero-copy path: wrap the externally-owned GL texture that the
        # .mm layer bound to an IOSurface via
        # EGL_ANGLE_iosurface_client_buffer. The GL id is owned by
        # ``VideoPlayer`` (created in ``_probeZeroCopy`` via
        # ``glGenTextures``, deleted in ``_teardownZeroCopy``); the
        # underlying GL contents are replaced in-place each frame via
        # ``eglBindTexImage``, which the GPU picks up automatically
        # on next draw.
        #
        # We pass ``nofree=True`` so Kivy's deferred
        # ``glDeleteTextures`` never fires for these wrappers.
        # Without that, when a player is rebuilt (e.g. via
        # ``apply_and_reload``) the old player's GL id can be
        # recycled by the driver for the new player's texture; any
        # straggler wrapper from the old player would then queue a
        # duplicate delete that lands on the *new* player's still-
        # bound texture, producing the classic "audio plays, video
        # goes black" failure mode.
        if existing_texture is None or \
                getattr(existing_texture, 'id', 0) != frame.gl_texture_id or \
                existing_texture.size != (width, height):
            existing_texture = Texture(
                width=width,
                height=height,
                target=frame.gl_target,
                texid=frame.gl_texture_id,
                colorfmt='bgra',
                bufferfmt='ubyte',
                mipmap=False,
                nofree=True)
            existing_texture.flip_vertical()
        return existing_texture

    if frame.data == NULL or datasize == 0 or width == 0 or height == 0:
        return existing_texture

    # CPU-copy path. The .mm layer hands us BGRA pixel data (from
    # ``kCVPixelFormatType_32BGRA`` for playback, or a BGRA
    # ``CGBitmapContext`` for thumbnails). We swizzle BGRA -> RGBA
    # in-place and upload as native RGBA rather than relying on
    # Kivy's ``colorfmt='bgra'`` upload, which fails silently on
    # Kivy's ANGLE/Metal GL backend (``EXT_bgra`` is not exposed,
    # so ``glTexImage2D`` rejects ``GL_BGRA`` with
    # ``GL_INVALID_ENUM`` and the resulting texture renders black).
    # Doing the swap here also makes downstream operations like
    # ``Texture.pixels`` (FBO readback) work, which they don't on a
    # BGRA-flagged texture in this backend.
    buf = <unsigned char *>frame.data
    with nogil:
        for i in range(0, datasize, 4):
            b = buf[i]
            buf[i] = buf[i + 2]
            buf[i + 2] = b

    if existing_texture is None or existing_texture.size != (width, height):
        existing_texture = Texture.create(
            size=(width, height), colorfmt='rgba')
        existing_texture.flip_vertical()

    cyarr = cyview.array(
        shape=(datasize,),
        itemsize=sizeof(char),
        format='B',
        mode='c',
        allocate_buffer=False,
    )
    cyarr.data = frame.data
    existing_texture.blit_buffer(cyarr, colorfmt='rgba')
    return existing_texture


cdef class _AVVideoStorage:
    cdef VideoPlayer *player

    def __cinit__(self):
        self.player = NULL

    def __dealloc__(self):
        if self.player != NULL:
            del self.player
            self.player = NULL


class VideoAVFoundation(VideoBase):
    '''Implementation of :class:`VideoBase` using the AVFoundation
    framework on macOS / iOS.

    Pixel transfer uses zero-copy when running on Kivy's ANGLE/Metal GL
    backend: the ``CVPixelBufferRef``'s underlying ``IOSurface`` is
    wrapped as an EGL pbuffer (via
    ``EGL_ANGLE_iosurface_client_buffer``) and bound to a persistent
    ``GL_TEXTURE_2D``, whose id is surfaced through
    :attr:`VideoFrame.gl_texture_id`. On any other backend (or when the
    runtime probe fails) the implementation falls back automatically to
    a CPU-copy path that ``memcpy``'s the BGRA pixel buffer into a
    :class:`~kivy.graphics.texture.Texture` via ``blit_buffer``. The
    selection is per-frame: a single frame failing to bind doesn't
    disable zero-copy for the rest of the stream.

    Provider-specific options (read from :attr:`VideoBase.options`):

    - ``automatically_waits_to_minimize_stalling`` (bool, default
      ``True``): forwarded to ``AVPlayer.automaticallyWaitsToMinimizeStalling``.
      The default (``True``) matches AVPlayer's own default and favors
      uninterrupted playback at the cost of start-up latency. Set to
      ``False`` for snappier start (AVPlayer begins playback as soon as
      the first decodable frame is available rather than buffering
      ahead).
    - ``force_cpu_copy`` (bool, default ``False``): bypass the zero-copy
      path (when available) and always use the CPU-copy path. Useful for
      A/B testing and debugging.

    Unknown keys in ``options`` are logged as a warning at construction
    time and otherwise ignored.

    .. seealso::
        :attr:`kivy.uix.video.Video.options` -- the widget-level
        property most apps use to pass these keys, with a cross-provider
        summary of supported options.

    .. versionadded:: 3.0.0
    '''

    def __init__(self, **kwargs):
        self._storage = _AVVideoStorage()
        self._update_ev = None
        self._duration = 0.0
        self._position = 0.0
        super(VideoAVFoundation, self).__init__(**kwargs)
        # Warn (once, eagerly) about any options keys this provider
        # doesn't recognize. Construction-time so the user sees it
        # immediately, not on first play.
        unknown = sorted(set(self._options) - _KNOWN_OPTIONS)
        if unknown:
            Logger.warning(
                f'VideoAVFoundation: ignoring unknown options keys '
                f'{unknown!r}; known keys: '
                f'{sorted(_KNOWN_OPTIONS)!r}')

    def __del__(self):
        self._release_player()

    @classmethod
    def generate_thumbnail(cls, filename, time, size=None):
        '''Generate a thumbnail Texture via AVAssetImageGenerator.

        See :meth:`kivy.core.video.VideoBase.generate_thumbnail`.

        .. versionadded:: 3.0.0
        '''
        cdef int w = 0
        cdef int h = 0
        cdef VideoFrame *frame = NULL
        cdef bytes url_b
        if not filename:
            return None
        if size is not None:
            try:
                w = int(size[0])
                h = int(size[1])
            except Exception:
                w = 0
                h = 0
        url_b = filename.encode('utf-8') if isinstance(filename, str) \
            else bytes(filename)
        frame = VideoPlayer.generateThumbnail(
            <const char *>url_b, <double>time, w, h)
        if frame == NULL:
            return None
        try:
            # Thumbnails always come back via the CPU-copy path
            # (AVAssetImageGenerator -> memcpy -> blit_buffer).
            texture = _frame_to_texture(frame, None)
        finally:
            del frame
        return texture

    # ---------- VideoBase API ----------

    def load(self):
        cdef _AVVideoStorage storage
        cdef bytes url_b
        Logger.debug(
            'VideoAVFoundation: Load <{}>'.format(self._filename))
        self._release_player()
        if not self._filename:
            return
        storage = <_AVVideoStorage>self._storage
        url_b = self._filename.encode('utf-8') \
            if isinstance(self._filename, str) else bytes(self._filename)
        storage.player = new VideoPlayer(<const char *>url_b)
        # Apply options that need to be in place before load(). Defaults
        # match AVPlayer's own (automaticallyWaitsToMinimizeStalling=YES,
        # zero-copy when available).
        storage.player.setAutomaticallyWaitsToMinimizeStalling(
            <bint>bool(self._options.get(
                'automatically_waits_to_minimize_stalling', True)))
        storage.player.setForceCPUCopy(
            <bint>bool(self._options.get('force_cpu_copy', False)))
        storage.player.load()
        storage.player.setVolume(<double>self._volume)

        # Drive frame polling from the Kivy Clock.
        if self._update_ev is None:
            self._update_ev = Clock.schedule_interval(
                self._update, 1.0 / max(1, self._fps))

    def unload(self):
        # ``_release_player()`` runs ``VideoPlayer.unload()`` which in
        # turn calls ``_teardownZeroCopy -> glDeleteTextures`` for the
        # zero-copy GL texture. Any straggler Texture wrappers around
        # that id were tagged ``_nofree=1`` in ``_frame_to_texture``
        # so their eventual ``__dealloc__`` is a no-op on the GL side.
        self._release_player()
        if self._update_ev is not None:
            self._update_ev.cancel()
            self._update_ev = None
        self._state = ''
        if self._buffering:
            self._buffering = False
            self.dispatch('on_buffering', False)

    def _release_player(self):
        cdef _AVVideoStorage storage = <_AVVideoStorage>self._storage
        if storage.player != NULL:
            storage.player.unload()
            del storage.player
            storage.player = NULL

    def play(self):
        cdef _AVVideoStorage storage = <_AVVideoStorage>self._storage
        super(VideoAVFoundation, self).play()
        if storage.player != NULL:
            storage.player.setVolume(<double>self._volume)
            storage.player.play()

    def pause(self):
        cdef _AVVideoStorage storage = <_AVVideoStorage>self._storage
        super(VideoAVFoundation, self).pause()
        if storage.player != NULL:
            storage.player.pause()

    def stop(self):
        cdef _AVVideoStorage storage = <_AVVideoStorage>self._storage
        super(VideoAVFoundation, self).stop()
        if storage.player != NULL:
            storage.player.stop()

    def seek(self, percent, precise=True):
        cdef _AVVideoStorage storage = <_AVVideoStorage>self._storage
        cdef double dur
        cdef double target
        if storage.player == NULL:
            return
        dur = storage.player.duration()
        if dur <= 0.0:
            return
        # Match the documented semantics of VideoBase.seek: percent is a
        # proportion in [0, 1] of the total duration.
        target = float(percent) * dur
        storage.player.seek(target, <bint>bool(precise))

    def _get_position(self):
        cdef _AVVideoStorage storage = <_AVVideoStorage>self._storage
        if storage.player == NULL:
            return 0.0
        return storage.player.position()

    def _get_duration(self):
        cdef _AVVideoStorage storage = <_AVVideoStorage>self._storage
        if storage.player == NULL:
            return 0.0
        return storage.player.duration()

    def _set_volume(self, value):
        cdef _AVVideoStorage storage = <_AVVideoStorage>self._storage
        self._volume = value
        if storage.player != NULL:
            storage.player.setVolume(<double>value)

    # ---------- Frame pump ----------

    def _update(self, dt):
        cdef _AVVideoStorage storage = <_AVVideoStorage>self._storage
        cdef VideoFrame *frame = NULL
        cdef bint new_buffering

        if storage.player == NULL:
            return

        # Sync the buffering signal on every tick and dispatch
        # on_buffering on transitions only. AVFoundation drives
        # mBuffering from a KVO observer on AVPlayer.timeControlStatus,
        # so this is just a cheap read of an atomic<bool>; gating the
        # dispatch on a change keeps event volume to one per
        # transition rather than per frame.
        new_buffering = storage.player.isBuffering()
        if bool(new_buffering) != self._buffering:
            self._buffering = bool(new_buffering)
            self.dispatch('on_buffering', self._buffering)

        # EOS handling: if AVFoundation reported playback ended, route
        # through VideoBase's standard _do_eos which dispatches on_eos.
        if storage.player.isEOS():
            # Latch: we only want to dispatch once.
            if self._state != '':
                self._do_eos()
            return

        if not storage.player.hasNewFrame():
            return

        frame = storage.player.retrieveFrame()
        if frame == NULL:
            return

        had_texture = self._texture is not None
        self._texture = _frame_to_texture(frame, self._texture)
        if not had_texture and self._texture is not None:
            self.dispatch('on_load')
        if self._texture is not None:
            self.dispatch('on_frame')
