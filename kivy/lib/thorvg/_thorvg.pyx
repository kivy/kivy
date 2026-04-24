# cython: language_level=3
# distutils: language = c++
"""
Cython wrapper around the minimal ThorVG v1.0.4 C API used by Kivy's SVG,
SVG-image and Lottie providers.

Public surface (imported through [kivy/lib/thorvg/__init__.py](__init__.py)):

- :class:`SwCanvas` - software raster canvas exposing its pixel buffer via
  the Python buffer protocol for zero-copy texture uploads.
- :class:`Picture` - SVG/Lottie/image paint node.
- :class:`LottieAnimation` - Lottie animation wrapper that owns an internal
  :class:`Picture`.
- :class:`Accessor` - scene-tree walker + ID generator.
- :class:`Paint` - base paint handle returned by :meth:`Picture.get_paint`
  and inside :class:`Accessor` callbacks.
- :class:`Result` - enum mirroring ``Tvg_Result`` values.

Engine lifecycle:

The ThorVG rendering engine is initialised exactly once when this module is
first imported (``tvg_engine_init(threads=0)``). ThorVG's C API maintains an
internal reference count for repeated ``init``/``term`` calls, so no Python
shadow-refcounting is needed. The engine is not explicitly terminated - OS
process teardown handles that cleanly.
"""

from cpython.buffer cimport PyBuffer_FillInfo
from cpython.mem cimport PyMem_Malloc, PyMem_Free
from libc.stdint cimport uint8_t, uint32_t
from libc.string cimport memset
from libcpp cimport bool as cbool

from enum import IntEnum

from kivy.lib.thorvg cimport thorvg as tvg


# ---------------------------------------------------------------------------
# Result enum (mirrors Tvg_Result values)
# ---------------------------------------------------------------------------


class Result(IntEnum):
    SUCCESS = <int>tvg.TVG_RESULT_SUCCESS
    INVALID_ARGUMENT = <int>tvg.TVG_RESULT_INVALID_ARGUMENT
    INSUFFICIENT_CONDITION = <int>tvg.TVG_RESULT_INSUFFICIENT_CONDITION
    FAILED_ALLOCATION = <int>tvg.TVG_RESULT_FAILED_ALLOCATION
    MEMORY_CORRUPTION = <int>tvg.TVG_RESULT_MEMORY_CORRUPTION
    NOT_SUPPORTED = <int>tvg.TVG_RESULT_NOT_SUPPORTED
    UNKNOWN = <int>tvg.TVG_RESULT_UNKNOWN


cdef inline object _wrap_result(tvg.Tvg_Result r):
    # Unknown future values pass through as-is rather than raising.
    try:
        return Result(<int>r)
    except ValueError:
        return <int>r


# ---------------------------------------------------------------------------
# Engine bootstrap (runs once at module import)
# ---------------------------------------------------------------------------


cdef tvg.Tvg_Result _engine_init_result = tvg.tvg_engine_init(0)
if _engine_init_result != tvg.TVG_RESULT_SUCCESS:
    # Engine init failure is non-recoverable for the wrapper - surface it
    # immediately at import time.
    raise RuntimeError(
        'kivy.lib.thorvg: tvg_engine_init failed with result {}'.format(
            <int>_engine_init_result))


def engine_version():
    """Return the ThorVG engine version as a ``(result, major, minor, micro,
    version_string)`` tuple.
    """
    cdef uint32_t major = 0
    cdef uint32_t minor = 0
    cdef uint32_t micro = 0
    cdef const char *version = NULL
    cdef tvg.Tvg_Result r = tvg.tvg_engine_version(
        &major, &minor, &micro, &version)
    py_version = version.decode('utf-8') if version is not NULL else None
    return (_wrap_result(r), <int>major, <int>minor, <int>micro, py_version)


# ---------------------------------------------------------------------------
# Paint (base class - also used to wrap non-owned handles from Picture /
# Accessor callbacks).
# ---------------------------------------------------------------------------


cdef class Paint:
    """A thin wrapper around a ``Tvg_Paint`` handle.

    ``_owned`` tracks whether Python is responsible for unref'ing the paint
    on ``__dealloc__``:

    - ``True`` when the paint was created by user code (e.g. ``Picture()``)
      and has not yet been handed off to a :class:`SwCanvas`.
    - ``False`` for paints fetched via :meth:`Picture.get_paint`, paints
      exposed through :meth:`Accessor` callbacks, or any paint whose
      ownership has been transferred to a canvas via :meth:`SwCanvas.add`.
    """

    cdef tvg.Tvg_Paint _paint
    cdef bint _owned

    def __cinit__(self):
        self._paint = NULL
        self._owned = False

    def __dealloc__(self):
        if self._paint != NULL and self._owned:
            tvg.tvg_paint_unref(self._paint, True)
            self._paint = NULL

    @staticmethod
    cdef Paint _wrap(tvg.Tvg_Paint handle, bint owned):
        cdef Paint p = Paint.__new__(Paint)
        p._paint = handle
        p._owned = owned
        return p

    def set_opacity(self, int opacity):
        """Set the paint opacity (0-255). Returns a :class:`Result`."""
        if self._paint == NULL:
            return Result.INVALID_ARGUMENT
        cdef uint8_t op
        if opacity < 0:
            op = 0
        elif opacity > 255:
            op = 255
        else:
            op = <uint8_t>opacity
        return _wrap_result(tvg.tvg_paint_set_opacity(self._paint, op))

    def get_id(self):
        """Return the paint's internal ID hash, or 0 if unset."""
        if self._paint == NULL:
            return 0
        return <unsigned long>tvg.tvg_paint_get_id(self._paint)


# ---------------------------------------------------------------------------
# Picture (SVG / Lottie / raster picture loader)
# ---------------------------------------------------------------------------


cdef class Picture(Paint):
    """A ``Picture`` paint node.

    Can be constructed directly and loaded via :meth:`load` / :meth:`load_data`,
    or obtained from :meth:`LottieAnimation.get_picture` in which case the
    picture is owned by the animation and must not be unref'd here.
    """

    def __cinit__(self, *args, **kwargs):
        self._paint = tvg.tvg_picture_new()
        self._owned = True

    def load(self, path):
        """Load a picture from *path* (file). Returns a :class:`Result`."""
        if self._paint == NULL:
            return Result.INVALID_ARGUMENT
        if isinstance(path, str):
            path_bytes = path.encode('utf-8')
        else:
            path_bytes = bytes(path)
        cdef bytes _b = path_bytes
        cdef const char *p = _b
        return _wrap_result(tvg.tvg_picture_load(self._paint, p))

    def load_data(self, data, mimetype='', rpath=None, copy=True):
        """Load a picture from in-memory *data* bytes.

        :param bytes data: Raw file contents.
        :param str mimetype: e.g. ``'svg'``, ``'lottie'``.
        :param rpath: Optional resource path string for external references.
        :param bool copy: If ``True``, ThorVG copies *data* into its own
            buffer. If ``False``, the caller must keep *data* alive for the
            lifetime of the picture.
        """
        if self._paint == NULL:
            return Result.INVALID_ARGUMENT
        if not isinstance(data, (bytes, bytearray)):
            if isinstance(data, str):
                data = data.encode('utf-8')
            else:
                data = bytes(data)
        cdef bytes _data = bytes(data)
        cdef const char *data_ptr = _data
        cdef uint32_t data_len = <uint32_t>len(_data)

        if isinstance(mimetype, str):
            mt_bytes = mimetype.encode('utf-8')
        else:
            mt_bytes = bytes(mimetype)
        cdef bytes _mt = mt_bytes
        cdef const char *mt_ptr = _mt

        cdef bytes _rp
        cdef const char *rp_ptr = NULL
        if rpath is not None:
            if isinstance(rpath, str):
                _rp = rpath.encode('utf-8')
            else:
                _rp = bytes(rpath)
            rp_ptr = _rp

        cdef bint c_copy = <bint>bool(copy)
        return _wrap_result(tvg.tvg_picture_load_data(
            self._paint, data_ptr, data_len, mt_ptr, rp_ptr, c_copy))

    def set_size(self, float w, float h):
        """Resize the picture content. Returns a :class:`Result`."""
        if self._paint == NULL:
            return Result.INVALID_ARGUMENT
        return _wrap_result(tvg.tvg_picture_set_size(self._paint, w, h))

    def get_size(self):
        """Return ``(result, w, h)`` - the picture's intrinsic size."""
        if self._paint == NULL:
            return (Result.INVALID_ARGUMENT, 0.0, 0.0)
        cdef float w = 0.0
        cdef float h = 0.0
        cdef tvg.Tvg_Result r = tvg.tvg_picture_get_size(
            self._paint, &w, &h)
        return (_wrap_result(r), float(w), float(h))

    def get_paint(self, id):
        """Look up a child paint by ID hash; return ``None`` if not found.

        *id* is a ``uint32_t`` handle - typically obtained from
        :meth:`Accessor.accessor_generate_id` or :meth:`Paint.get_id`.
        The parameter is declared untyped so that Python ints in the full
        ``uint32_t`` range (0..2^32 - 1) are accepted without Cython
        raising ``OverflowError`` on values above ``INT_MAX``.

        The returned :class:`Paint` is not owned by Python - it is a
        non-owning view into the picture's scene tree.
        """
        if self._paint == NULL:
            return None
        cdef uint32_t c_id = <uint32_t><unsigned long>id
        cdef tvg.Tvg_Paint child = <tvg.Tvg_Paint>tvg.tvg_picture_get_paint(
            self._paint, c_id)
        if child == NULL:
            return None
        return Paint._wrap(child, False)

    def set_accessible(self, accessible):
        """Enable or disable the accessible-mode ID→name map for SVGs.

        Must be called before :meth:`load` / :meth:`load_data`. Required for
        :meth:`Accessor.get_name` to resolve to the original SVG ``id``.
        """
        if self._paint == NULL:
            return Result.INVALID_ARGUMENT
        cdef bint c_acc = <bint>bool(accessible)
        return _wrap_result(tvg.tvg_picture_set_accessible(
            self._paint, c_acc))


cdef Picture _wrap_borrowed_picture(tvg.Tvg_Paint handle):
    """Wrap an externally-owned picture handle (e.g. from an animation).

    ``Picture.__cinit__`` always allocates a fresh ``Tvg_Paint``; we
    immediately free it and replace with *handle*, marking the wrapper as
    non-owning so ``__dealloc__`` is a no-op.
    """
    cdef Picture p = Picture()
    if p._paint != NULL:
        tvg.tvg_paint_unref(p._paint, True)
    p._paint = handle
    p._owned = False
    return p


# ---------------------------------------------------------------------------
# SwCanvas
# ---------------------------------------------------------------------------


cdef class SwCanvas:
    """Software canvas backed by an RGBA pixel buffer.

    The buffer is exposed via the Python buffer protocol as a 1-D ``bytes``
    (``format='B'``) of length ``stride * h * 4``. ``bytes(canvas)`` copies
    the buffer, while ``memoryview(canvas)`` / Kivy's
    ``Texture.blit_buffer(canvas)`` access it without copying.

    The buffer is valid for access only outside the ``draw()`` / ``sync()``
    window - always call :meth:`sync` before reading pixels.
    """

    cdef tvg.Tvg_Canvas _canvas
    cdef uint32_t *_buffer
    cdef Py_ssize_t _buffer_len_bytes
    cdef readonly int w
    cdef readonly int h
    cdef readonly int stride
    # Keep strong refs to paints added through `add()` so that GC'ing the
    # Python wrapper does not leave the canvas holding a freed handle (the
    # canvas treats Paint ownership as transferred and will free them on
    # destroy).
    cdef list _paints

    def __cinit__(self):
        self._canvas = NULL
        self._buffer = NULL
        self._buffer_len_bytes = 0
        self.w = 0
        self.h = 0
        self.stride = 0
        self._paints = []

    def __init__(self):
        self._canvas = tvg.tvg_swcanvas_create(tvg.TVG_ENGINE_OPTION_DEFAULT)
        if self._canvas == NULL:
            raise RuntimeError(
                'kivy.lib.thorvg: tvg_swcanvas_create returned NULL')

    def __dealloc__(self):
        # Canvas destruction frees the paints it owns; drop our Python-side
        # list first so their __dealloc__ doesn't attempt to unref them.
        for p in self._paints or []:
            (<Paint>p)._owned = False
        self._paints = None
        if self._canvas != NULL:
            tvg.tvg_canvas_destroy(self._canvas)
            self._canvas = NULL
        if self._buffer != NULL:
            PyMem_Free(self._buffer)
            self._buffer = NULL

    def set_target(self, int w, int h, stride=None):
        """Allocate/resize the RGBA pixel buffer and bind it to the canvas.

        :param int w: width in pixels.
        :param int h: height in pixels.
        :param int stride: row stride in pixels. Defaults to *w*.
        """
        if self._canvas == NULL:
            return Result.INVALID_ARGUMENT
        if w <= 0 or h <= 0:
            return Result.INVALID_ARGUMENT
        cdef int c_stride = w if stride is None else int(stride)
        if c_stride <= 0:
            return Result.INVALID_ARGUMENT
        cdef Py_ssize_t needed = <Py_ssize_t>c_stride * <Py_ssize_t>h \
            * <Py_ssize_t>sizeof(uint32_t)
        cdef uint32_t *buf
        if self._buffer == NULL or self._buffer_len_bytes != needed:
            if self._buffer != NULL:
                PyMem_Free(self._buffer)
                self._buffer = NULL
                self._buffer_len_bytes = 0
            buf = <uint32_t *>PyMem_Malloc(<size_t>needed)
            if buf == NULL:
                return Result.FAILED_ALLOCATION
            self._buffer = buf
            self._buffer_len_bytes = needed
        memset(self._buffer, 0, <size_t>self._buffer_len_bytes)
        cdef tvg.Tvg_Result r = tvg.tvg_swcanvas_set_target(
            self._canvas, self._buffer,
            <uint32_t>c_stride, <uint32_t>w, <uint32_t>h,
            tvg.TVG_COLORSPACE_ABGR8888)
        if r == tvg.TVG_RESULT_SUCCESS:
            self.w = w
            self.h = h
            self.stride = c_stride
        return _wrap_result(r)

    def add(self, Paint paint not None):
        """Add *paint* to the canvas. Ownership is transferred to the canvas.

        After a successful ``add`` the Python :class:`Paint` wrapper becomes
        non-owning; the paint will be freed when the canvas is destroyed (or
        re-rendered with a different scene).
        """
        if self._canvas == NULL or paint._paint == NULL:
            return Result.INVALID_ARGUMENT
        cdef tvg.Tvg_Result r = tvg.tvg_canvas_add(
            self._canvas, paint._paint)
        if r == tvg.TVG_RESULT_SUCCESS:
            paint._owned = False
            self._paints.append(paint)
        return _wrap_result(r)

    def remove(self, Paint paint=None):
        """Remove *paint* from the canvas, or clear all paints if ``None``."""
        if self._canvas == NULL:
            return Result.INVALID_ARGUMENT
        cdef tvg.Tvg_Paint p = NULL
        if paint is not None:
            p = paint._paint
        cdef tvg.Tvg_Result r = tvg.tvg_canvas_remove(self._canvas, p)
        if r == tvg.TVG_RESULT_SUCCESS:
            if paint is None:
                self._paints = []
            else:
                try:
                    self._paints.remove(paint)
                except ValueError:
                    pass
        return _wrap_result(r)

    def update(self):
        if self._canvas == NULL:
            return Result.INVALID_ARGUMENT
        return _wrap_result(tvg.tvg_canvas_update(self._canvas))

    def draw(self, clear=True):
        if self._canvas == NULL:
            return Result.INVALID_ARGUMENT
        cdef bint c_clear = <bint>bool(clear)
        return _wrap_result(tvg.tvg_canvas_draw(self._canvas, c_clear))

    def sync(self):
        if self._canvas == NULL:
            return Result.INVALID_ARGUMENT
        return _wrap_result(tvg.tvg_canvas_sync(self._canvas))

    def destroy(self):
        """Destroy the canvas and free its pixel buffer.

        Subsequent operations return :class:`Result.INVALID_ARGUMENT`.
        """
        for p in self._paints or []:
            (<Paint>p)._owned = False
        self._paints = []
        cdef tvg.Tvg_Result r = tvg.TVG_RESULT_SUCCESS
        if self._canvas != NULL:
            r = tvg.tvg_canvas_destroy(self._canvas)
            self._canvas = NULL
        if self._buffer != NULL:
            PyMem_Free(self._buffer)
            self._buffer = NULL
            self._buffer_len_bytes = 0
        self.w = 0
        self.h = 0
        self.stride = 0
        return _wrap_result(r)

    # -- Buffer protocol ---------------------------------------------------

    def __getbuffer__(self, Py_buffer *view, int flags):
        if self._buffer == NULL:
            raise BufferError(
                'SwCanvas buffer not allocated (call set_target first)')
        PyBuffer_FillInfo(
            view, self, <void *>self._buffer,
            self._buffer_len_bytes, 0, flags)

    def __releasebuffer__(self, Py_buffer *view):
        pass

    # -- Back-compat attribute expected by existing providers -------------

    @property
    def buffer_arr(self):
        """Return ``self`` - a buffer-protocol object of raw RGBA bytes.

        Keeps :func:`bytes(canvas.buffer_arr)` working for the existing
        provider code that was written against ``thorvg-python``'s
        ``SwCanvas.buffer_arr`` ctypes array attribute.
        """
        return self


# ---------------------------------------------------------------------------
# Accessor
# ---------------------------------------------------------------------------


cdef cbool _accessor_trampoline(
        tvg.Tvg_Paint paint, void *data) noexcept with gil:
    """C callback passed to ``tvg_accessor_set``.

    *data* is a pointer to a Python tuple ``(callback, user_data)`` held on
    the Python ``Accessor`` instance for the duration of the call. We never
    propagate Python exceptions back into ThorVG's traversal - errors are
    caught here and reported via :mod:`kivy.logger`.
    """
    cdef object payload = <object>data
    cdef Paint p = Paint._wrap(paint, False)
    cdef object cb = payload[0]
    cdef object user_data = payload[1]
    try:
        return bool(cb(p, user_data))
    except Exception:
        from kivy.logger import Logger
        import traceback
        Logger.error(
            'ThorVG: accessor callback raised: {}'.format(
                traceback.format_exc()))
        return False


cdef class Accessor:
    """Scene-tree walker + ID generator.

    Most usage involves :meth:`accessor_generate_id` (a pure hash function)
    and :meth:`set` (walks a :class:`Picture` scene tree, invoking a Python
    callback for each descendant paint).
    """

    cdef tvg.Tvg_Accessor _accessor
    # Holds `(callback, user_data)` during a `set()` call so the C callback
    # can dereference it safely.
    cdef object _cb_payload

    def __cinit__(self):
        self._accessor = NULL
        self._cb_payload = None

    def __init__(self):
        self._accessor = tvg.tvg_accessor_new()
        if self._accessor == NULL:
            raise RuntimeError(
                'kivy.lib.thorvg: tvg_accessor_new returned NULL')

    def __dealloc__(self):
        if self._accessor != NULL:
            tvg.tvg_accessor_del(self._accessor)
            self._accessor = NULL

    def accessor_generate_id(self, name):
        """Hash *name* to the same 32-bit ID ThorVG uses for paint lookup."""
        if isinstance(name, str):
            name_bytes = name.encode('utf-8')
        else:
            name_bytes = bytes(name)
        cdef bytes _n = name_bytes
        cdef const char *np = _n
        return <unsigned long>tvg.tvg_accessor_generate_id(np)

    def get_name(self, id):
        """Look up the original SVG ``id`` string for a given ID hash.

        *id* accepts the full ``uint32_t`` range returned by
        :meth:`accessor_generate_id` / :meth:`Paint.get_id`.  Only valid
        inside an :meth:`set` callback for a :class:`Picture` loaded
        with :meth:`Picture.set_accessible` ``True``.
        """
        if self._accessor == NULL:
            return None
        cdef uint32_t c_id = <uint32_t><unsigned long>id
        cdef const char *s = tvg.tvg_accessor_get_name(
            self._accessor, c_id)
        if s is NULL:
            return None
        return s.decode('utf-8')

    def set(self, Picture picture not None, func, data=b''):
        """Walk *picture*'s scene tree, calling *func(paint, data)* for each.

        *func* must return a truthy value to continue traversal, a falsy
        value to stop. Exceptions raised inside the callback are logged and
        terminate traversal.
        """
        if self._accessor == NULL or picture._paint == NULL:
            return Result.INVALID_ARGUMENT
        self._cb_payload = (func, data)
        cdef tvg.Tvg_Result r
        try:
            r = tvg.tvg_accessor_set(
                self._accessor, picture._paint,
                _accessor_trampoline, <void *>self._cb_payload)
        finally:
            self._cb_payload = None
        return _wrap_result(r)


# ---------------------------------------------------------------------------
# LottieAnimation
# ---------------------------------------------------------------------------


cdef class LottieAnimation:
    """Lottie animation controller.

    Constructing this class allocates an internal :class:`Picture` used to
    load the Lottie JSON. Call :meth:`get_picture` to retrieve it, load the
    file / bytes via the picture's :meth:`Picture.load` / :meth:`Picture.load_data`,
    size it, add it to a :class:`SwCanvas`, then drive frames through this
    animation object.
    """

    cdef tvg.Tvg_Animation _animation
    cdef Picture _picture  # non-owning borrow; lifetime tied to animation.

    def __cinit__(self):
        self._animation = NULL
        self._picture = None

    def __init__(self):
        self._animation = tvg.tvg_lottie_animation_new()
        if self._animation == NULL:
            raise RuntimeError(
                'kivy.lib.thorvg: tvg_lottie_animation_new returned NULL')
        cdef tvg.Tvg_Paint handle = tvg.tvg_animation_get_picture(
            self._animation)
        if handle == NULL:
            tvg.tvg_animation_del(self._animation)
            self._animation = NULL
            raise RuntimeError(
                'kivy.lib.thorvg: tvg_animation_get_picture returned NULL')
        # The picture is owned by the animation; don't let Python free it.
        self._picture = _wrap_borrowed_picture(handle)

    def __dealloc__(self):
        # Drop the picture wrapper first (non-owning, so this is a no-op on
        # the C side), then delete the animation which frees both.
        self._picture = None
        if self._animation != NULL:
            tvg.tvg_animation_del(self._animation)
            self._animation = NULL

    def get_picture(self):
        """Return the :class:`Picture` owned by this animation."""
        return self._picture

    def set_frame(self, float frame):
        if self._animation == NULL:
            return Result.INVALID_ARGUMENT
        return _wrap_result(tvg.tvg_animation_set_frame(
            self._animation, frame))

    def get_total_frame(self):
        """Return ``(result, total_frames_float)``."""
        if self._animation == NULL:
            return (Result.INVALID_ARGUMENT, 0.0)
        cdef float cnt = 0.0
        cdef tvg.Tvg_Result r = tvg.tvg_animation_get_total_frame(
            self._animation, &cnt)
        return (_wrap_result(r), float(cnt))

    def get_duration(self):
        """Return ``(result, duration_seconds)``."""
        if self._animation == NULL:
            return (Result.INVALID_ARGUMENT, 0.0)
        cdef float d = 0.0
        cdef tvg.Tvg_Result r = tvg.tvg_animation_get_duration(
            self._animation, &d)
        return (_wrap_result(r), float(d))

    def set_segment(self, float begin, float end):
        if self._animation == NULL:
            return Result.INVALID_ARGUMENT
        return _wrap_result(tvg.tvg_animation_set_segment(
            self._animation, begin, end))

    def set_marker(self, name):
        if self._animation == NULL:
            return Result.INVALID_ARGUMENT
        if isinstance(name, str):
            b = name.encode('utf-8')
        else:
            b = bytes(name)
        cdef bytes _b = b
        cdef const char *p = _b
        return _wrap_result(tvg.tvg_lottie_animation_set_marker(
            self._animation, p))

    def get_markers_cnt(self):
        """Return ``(result, count)``."""
        if self._animation == NULL:
            return (Result.INVALID_ARGUMENT, 0)
        cdef uint32_t cnt = 0
        cdef tvg.Tvg_Result r = tvg.tvg_lottie_animation_get_markers_cnt(
            self._animation, &cnt)
        return (_wrap_result(r), <int>cnt)

    def get_marker(self, int idx):
        """Return ``(result, marker_name_or_None)`` for marker *idx*."""
        if self._animation == NULL:
            return (Result.INVALID_ARGUMENT, None)
        cdef const char *name = NULL
        cdef tvg.Tvg_Result r = tvg.tvg_lottie_animation_get_marker(
            self._animation, <uint32_t>idx, &name)
        py_name = name.decode('utf-8') if name is not NULL else None
        return (_wrap_result(r), py_name)

    def gen_slot(self, slot):
        """Generate a slot ID from JSON *slot* data. Returns 0 on failure."""
        if self._animation == NULL:
            return 0
        if isinstance(slot, str):
            b = slot.encode('utf-8')
        else:
            b = bytes(slot)
        cdef bytes _b = b
        cdef const char *p = _b
        cdef uint32_t handle = tvg.tvg_lottie_animation_gen_slot(
            self._animation, p)
        return <unsigned long>handle

    def apply_slot(self, id):
        """Apply the slot override identified by *id*.

        *id* is the unsigned 32-bit handle returned by :meth:`gen_slot`
        (or ``0`` to clear all active overrides). The parameter is
        declared untyped so that Python ints in the full ``uint32_t``
        range (0..2^32 - 1) can be accepted without Cython raising
        ``OverflowError`` on values above ``INT_MAX``.
        """
        if self._animation == NULL:
            return Result.INVALID_ARGUMENT
        cdef uint32_t c_id = <uint32_t><unsigned long>id
        return _wrap_result(tvg.tvg_lottie_animation_apply_slot(
            self._animation, c_id))

    def del_slot(self, id):
        """Delete the slot override identified by *id*.

        Accepts the full ``uint32_t`` range returned by :meth:`gen_slot`
        (see :meth:`apply_slot` for rationale).
        """
        if self._animation == NULL:
            return Result.INVALID_ARGUMENT
        cdef uint32_t c_id = <uint32_t><unsigned long>id
        return _wrap_result(tvg.tvg_lottie_animation_del_slot(
            self._animation, c_id))

    def set_quality(self, int value):
        if self._animation == NULL:
            return Result.INVALID_ARGUMENT
        cdef uint8_t v
        if value < 0:
            v = 0
        elif value > 100:
            v = 100
        else:
            v = <uint8_t>value
        return _wrap_result(tvg.tvg_lottie_animation_set_quality(
            self._animation, v))
