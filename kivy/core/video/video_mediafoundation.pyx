# distutils: language = c++
'''
Media Foundation Video
=======================

Video implementation using Microsoft Media Foundation, the default video
provider on Windows.

Pixel transfer is zero-copy whenever the GL context's interop bridge
registers successfully: the decoded ``ID3D11Texture2D`` is shared
directly into GL (via ``WGL_NV_DX_interop2`` for a WGL context, or
``EGL_ANGLE_d3d_texture_client_buffer`` for an ANGLE context) and wrapped into a :class:`~kivy.graphics.texture.Texture` with
``nofree=True`` -- no per-frame ``memcpy``. If that one-time registration
fails (e.g. a GPU/driver gap), the provider falls back to a CPU copy for
every frame instead of failing outright. A format whose only decoder has
no Direct3D 11 support (MPEG-1, for example) is decoded in software,
also with a CPU copy for every frame.

.. versionadded:: 3.0.0
'''

__all__ = ('VideoMediaFoundation',)

from libc.stdlib cimport free


cdef extern from "video_mediafoundation_implem.h":
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
        bint hasError()

        const char *lastError()
        const char *interopNote()
        bint usingCpuFallback()

        @staticmethod
        VideoFrame *generateThumbnail(
            const char *url, double t, int w, int h)


from cython cimport view as cyview
from kivy.clock import Clock
from kivy.core.video import VideoBase
from kivy.graphics.texture import Texture
from kivy.logger import Logger


# No Media Foundation-specific options exist yet; kept as an explicit,
# empty whitelist (rather than skipping the check) so the warning below
# starts working for free the moment a real option is added.
_KNOWN_OPTIONS = frozenset()
# VideoBase's own keyword arguments. The Video widget also passes them in
# options, for apps that set ``eos`` there, so they aren't unknown.
_BASE_KWARGS = frozenset({'filename', 'eos', 'async', 'autoplay', 'fps'})


cdef _frame_to_texture(VideoFrame *frame, existing_texture):
    '''Wrap or update a Kivy Texture from a VideoFrame.

    Returns the Texture (possibly the same instance as
    ``existing_texture``).
    '''
    cdef int width = frame.width
    cdef int height = frame.height
    cdef unsigned int datasize = frame.datasize
    cdef cyview.array cyarr

    if frame.gl_texture_id != 0:
        # Zero-copy path: wrap the externally-owned GL texture that the
        # native layer shared from Media Foundation's decode target via
        # the active GL backend's interop bridge. The underlying GL
        # contents are replaced in-place every frame by the native
        # layer (re-locked for WGL, re-bound via eglBindTexImage for
        # ANGLE); we only need to (re-)wrap the id here if it or
        # the size actually changed.
        #
        # nofree=True so Kivy's deferred glDeleteTextures never fires
        # for these wrappers -- the native VideoPlayer owns this id's
        # lifecycle (see video_mediafoundation_implem.cpp's unload()).
        if existing_texture is None or \
                getattr(existing_texture, 'id', 0) != frame.gl_texture_id or \
                existing_texture.size != (width, height):
            # The shared D3D11 texture is top-down (row 0 = top), while
            # GL/Kivy treat texture row 0 as the bottom -- same situation
            # as video_avfoundation's IOSurface path, so same flip.
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

    # CPU-copy path: either the interop bridge failed to register (live
    # playback fallback) or this is a generate_thumbnail() frame. The
    # native layer already swizzles BGRA->RGBA (see
    # video_mediafoundation_implem.cpp), matching video_avfoundation's
    # own CPU-copy convention rather than uploading as colorfmt='bgra',
    # since GL_BGRA upload support isn't guaranteed across every GL
    # backend this can run under. Rows are top-down, so flip like the
    # zero-copy branch above.
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


cdef class _MFVideoStorage:
    cdef VideoPlayer *player

    def __cinit__(self):
        self.player = NULL

    def __dealloc__(self):
        if self.player != NULL:
            del self.player
            self.player = NULL


class VideoMediaFoundation(VideoBase):
    '''Implementation of :class:`VideoBase` using Media Foundation on
    Windows.

    Pixel transfer is zero-copy when the GL context's interop bridge is
    available: Media Foundation decodes into a shared
    ``ID3D11Texture2D``, which is registered once with
    ``WGL_NV_DX_interop2`` or shared via
    ``EGL_ANGLE_d3d_texture_client_buffer``, then wrapped into a
    :class:`~kivy.graphics.texture.Texture` with ``nofree=True``.

    The bridge follows the kind of GL context that is actually current,
    not the ``KIVY_GL_BACKEND`` name. ``glew`` and ``sdl3`` always run
    on WGL. ``angle_sdl3`` asks SDL for an OpenGL ES context, which SDL
    serves from the driver's own ES profile over WGL when it has one
    (NVIDIA does), and from ANGLE otherwise or when the
    ``SDL_OPENGL_ES_DRIVER=1`` environment variable forces ANGLE. Both
    kinds of context get zero-copy. If that one-time registration fails -- a GPU/driver
    gap, most commonly a laptop where the active GL context and Media
    Foundation's decode device land on different GPUs -- the provider
    falls back to a CPU copy for every frame instead of failing
    outright, logged once as a single diagnostic.

    **Supported formats.** Decoding uses the Media Foundation decoders
    installed on the system; Kivy ships none. Standard MP4 files (H.264
    video with AAC audio) play out of the box. Other formats need
    Microsoft's optional video extensions, installed from the Microsoft
    Store, and are then picked up automatically with no change to the
    app:

    - HEVC (H.265): *HEVC Video Extensions*. Not free on every system;
      some PCs come with a free manufacturer version preinstalled.
    - AV1: *AV1 Video Extension* (free).
    - VP9: *VP9 Video Extensions* (free).
    - MPEG-2: *MPEG-2 Video Extension* (free).

    Windows "N" and "KN" editions ship without Media Foundation. There
    this provider fails to import and Kivy selects the next available
    video provider, unless the user installs the Media Feature Pack
    (Settings > Apps > Optional features).

    Unknown keys in ``options`` are logged as a warning at construction
    time and otherwise ignored.

    .. seealso::
        :attr:`kivy.uix.video.Video.options` -- the widget-level
        property most apps use to pass these keys, with a cross-provider
        summary of supported options.

    .. versionadded:: 3.0.0
    '''

    def __init__(self, **kwargs):
        self._storage = _MFVideoStorage()
        self._update_ev = None
        self._logged_fallback = False
        self._logged_error = False
        super(VideoMediaFoundation, self).__init__(**kwargs)
        unknown = sorted(set(self._options) - _KNOWN_OPTIONS - _BASE_KWARGS)
        if unknown:
            Logger.warning(
                f'VideoMediaFoundation: ignoring unknown options keys '
                f'{unknown!r}; known keys: '
                f'{sorted(_KNOWN_OPTIONS)!r}')

    def __del__(self):
        self._release_player()

    @classmethod
    def generate_thumbnail(cls, filename, time, size=None):
        '''Generate a thumbnail Texture via Media Foundation.

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
            texture = _frame_to_texture(frame, None)
        finally:
            free(frame.data)
            del frame
        return texture

    # ---------- VideoBase API ----------

    def load(self):
        cdef _MFVideoStorage storage
        cdef bytes url_b
        cdef bytes err
        Logger.debug(
            'VideoMediaFoundation: Load <{}>'.format(self._filename))
        self._release_player()
        if not self._filename:
            return
        storage = <_MFVideoStorage>self._storage
        url_b = self._filename.encode('utf-8') \
            if isinstance(self._filename, str) else bytes(self._filename)
        storage.player = new VideoPlayer(<const char *>url_b)
        storage.player.load()
        err = storage.player.lastError()
        self._logged_error = bool(err)
        if err:
            Logger.error(
                'VideoMediaFoundation: setup failed: {}'.format(
                    err.decode('utf-8', 'replace')))
        storage.player.setVolume(<double>self._volume)

        # Drive frame polling from the Kivy Clock. load() itself is
        # non-blocking (SetSource is async); readiness and frames are
        # discovered here, one cheap poll per tick.
        if self._update_ev is None:
            self._update_ev = Clock.schedule_interval(
                self._update, 1.0 / max(1, self._fps))

    def unload(self):
        self._release_player()
        if self._update_ev is not None:
            self._update_ev.cancel()
            self._update_ev = None
        self._state = ''
        if self._buffering:
            self._buffering = False
            self.dispatch('on_buffering', False)

    def _release_player(self):
        cdef _MFVideoStorage storage = <_MFVideoStorage>self._storage
        if storage.player != NULL:
            storage.player.unload()
            del storage.player
            storage.player = NULL

    def play(self):
        cdef _MFVideoStorage storage = <_MFVideoStorage>self._storage
        super(VideoMediaFoundation, self).play()
        if storage.player != NULL:
            storage.player.setVolume(<double>self._volume)
            storage.player.play()

    def pause(self):
        cdef _MFVideoStorage storage = <_MFVideoStorage>self._storage
        super(VideoMediaFoundation, self).pause()
        if storage.player != NULL:
            storage.player.pause()

    def stop(self):
        cdef _MFVideoStorage storage = <_MFVideoStorage>self._storage
        super(VideoMediaFoundation, self).stop()
        if storage.player != NULL:
            storage.player.stop()

    def seek(self, percent, precise=True):
        cdef _MFVideoStorage storage = <_MFVideoStorage>self._storage
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
        cdef _MFVideoStorage storage = <_MFVideoStorage>self._storage
        if storage.player == NULL:
            return 0.0
        return storage.player.position()

    def _get_duration(self):
        cdef _MFVideoStorage storage = <_MFVideoStorage>self._storage
        if storage.player == NULL:
            return 0.0
        return storage.player.duration()

    def _set_volume(self, value):
        cdef _MFVideoStorage storage = <_MFVideoStorage>self._storage
        self._volume = value
        if storage.player != NULL:
            storage.player.setVolume(<double>value)

    # ---------- Frame pump ----------

    def _update(self, dt):
        cdef _MFVideoStorage storage = <_MFVideoStorage>self._storage
        cdef VideoFrame *frame = NULL
        cdef bint new_buffering

        if storage.player == NULL:
            return

        # Media Foundation reports a file it can't play (for example one
        # whose codec has no installed decoder) asynchronously, as an
        # error event; without this the video would just never load.
        if storage.player.hasError():
            if not self._logged_error:
                self._logged_error = True
                Logger.error('VideoMediaFoundation: <{}>: {}'.format(
                    self._filename,
                    storage.player.lastError().decode('utf-8', 'replace')))
            return

        new_buffering = storage.player.isBuffering()
        if bool(new_buffering) != self._buffering:
            self._buffering = bool(new_buffering)
            self.dispatch('on_buffering', self._buffering)

        if storage.player.isEOS():
            if self._state != '':
                self._do_eos()
            return

        if not storage.player.hasNewFrame():
            return

        frame = storage.player.retrieveFrame()
        if frame == NULL:
            return

        if not self._logged_fallback and storage.player.usingCpuFallback():
            self._logged_fallback = True
            Logger.info(
                'VideoMediaFoundation: using a CPU copy for every frame '
                '(zero-copy unavailable: {})'.format(
                    storage.player.interopNote().decode('utf-8', 'replace')))

        had_texture = self._texture is not None
        self._texture = _frame_to_texture(frame, self._texture)
        if not had_texture and self._texture is not None:
            self.dispatch('on_load')
        if self._texture is not None:
            self.dispatch('on_frame')
