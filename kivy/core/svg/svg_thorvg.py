'''
SVG provider - ThorVG backend
=============================

Implements :class:`~kivy.core.svg.SvgProviderBase` using ``thorvg-python``.

Requires ``thorvg-python``.  Install with::

    pip install thorvg-python

.. versionadded:: 3.0.0
'''

import math
import xml.etree.ElementTree as ET

from kivy.logger import Logger
from kivy.core.svg import SvgProviderBase, SvgLoader

# Module-level ThorVG engine and Accessor singletons.  Initialised on first
# use so that importing this module does not hard-fail when thorvg-python
# is absent.
_engine = None
_accessor = None

# Cached ctypes function wrappers - set once on first use so that
# argtypes/restype are not reassigned on every render call.
_tvg_generate_id_fn = None
_tvg_get_paint_fn = None


def _get_engine():
    '''Return the shared ThorVG Engine, initialising it if needed.'''
    global _engine
    if _engine is None:
        import thorvg_python as tvg
        _engine = tvg.Engine(threads=0)
    return _engine


def _generate_id(name):
    '''Hash *name* to the uint32 paint ID that ThorVG uses internally.

    This is a workaround for a bug in ``thorvg_python``'s
    ``Accessor.accessor_generate_id()`` method.

    Wraps ``tvg_accessor_generate_id`` from the ThorVG C library directly.
    The ``thorvg_python`` binding's ``Accessor.accessor_generate_id()`` calls
    ``.value`` on the ctypes return, which fails on platforms where ctypes
    already unwraps ``c_uint32`` to a plain Python ``int``.  Using ``int()``
    here handles both cases safely.

    argtypes/restype are set once and cached in ``_tvg_generate_id_fn`` so
    that repeated calls do not pay the ctypes attribute-set overhead.
    '''
    global _accessor, _tvg_generate_id_fn
    import ctypes
    from thorvg_python.accessor import Accessor
    engine = _get_engine()
    if _accessor is None:
        _accessor = Accessor(engine, None)
    if _tvg_generate_id_fn is None:
        fn = _accessor.thorvg_lib.tvg_accessor_generate_id
        fn.argtypes = [ctypes.c_char_p]
        fn.restype = ctypes.c_uint32
        _tvg_generate_id_fn = fn
    # c_char_p passes a null-terminated byte string; encode() provides UTF-8.
    return int(_tvg_generate_id_fn(name.encode()))


def _picture_get_paint(pic, hash_id):
    '''Retrieve a Paint node from a Picture by its uint32 hash ID.

    Works around a bug in ``thorvg_python``'s ``Picture.get_paint``
    where all three ctypes calls incorrectly name ``tvg_picture_get_size``
    instead of ``tvg_picture_get_paint``, causing an access violation when
    the function writes floats into what should be a pointer-return path.

    argtypes/restype are set once and cached in ``_tvg_get_paint_fn``.
    '''
    global _tvg_get_paint_fn
    import ctypes
    from thorvg_python.base import PaintPointer
    from thorvg_python.paint import Paint
    if _tvg_get_paint_fn is None:
        fn = pic.thorvg_lib.tvg_picture_get_paint
        fn.argtypes = [PaintPointer, ctypes.c_uint32]
        fn.restype = PaintPointer
        _tvg_get_paint_fn = fn
    paint_ptr = _tvg_get_paint_fn(pic._paint, ctypes.c_uint32(hash_id))
    if not paint_ptr:
        return None
    return Paint(pic.engine, paint_ptr)


def _parse_element_ids(svg_bytes):
    '''Return a list of all ``id`` attribute values in the SVG XML.'''
    ids = []
    try:
        root = ET.fromstring(svg_bytes)
        # Strip namespace prefixes so we can match elements regardless of
        # whether the SVG uses a default namespace.
        for elem in root.iter():
            eid = elem.get('id')
            if eid:
                ids.append(eid)
    except ET.ParseError as exc:
        Logger.warning(
            f'SvgThorvg: XML parse error scanning element IDs: {exc}'
        )
    return ids


def _apply_current_color(svg_bytes, color_tuple):
    '''Replace every ``currentColor`` token in *svg_bytes* with a hex colour.

    ``currentColor`` is an SVG reserved keyword and will not appear inside
    element names or IDs, so a plain byte-string replacement is safe.

    Per the SVG 1.1 spec, ``currentColor`` carries only RGB - opacity is
    expressed separately via ``fill-opacity`` / ``stroke-opacity``.  Only
    the first three components of *color_tuple* are used.

    :param bytes svg_bytes: Raw SVG source.
    :param tuple color_tuple: ``(r, g, b[, a])`` floats 0.0-1.0.  The alpha
        component, if present, is ignored.
    :returns: Modified SVG bytes.
    '''
    r, g, b = color_tuple[:3]
    hex_color = (f'#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}'
                 ).encode('ascii')
    return svg_bytes.replace(b'currentColor', hex_color)


def _rgba_bytes_from_canvas(canvas):
    '''Extract RGBA bytes from a rendered ThorVG SwCanvas.

    ThorVG's default ABGR8888 colorspace names the *integer* bit layout
    (A in the high byte, R in the low byte).  On a little-endian machine
    those bytes land in memory as [R, G, B, A] - exactly Kivy's ``rgba``
    format.  All of Kivy's supported platforms (x86-64, ARM64/iOS,
    ARM64/Android, Apple Silicon) run in little-endian mode, so no
    byte-swapping is needed.

    .. note:: Optimisation opportunity - this call copies the full pixel
        buffer into a new Python ``bytes`` object (~47 MB at 4K).

        If a Cython wrapper for ThorVG is introduced (e.g. to bundle ThorVG
        directly into the Kivy build the way other backends are), this
        becomes trivial: ``SwCanvas.__getbuffer__`` can expose the render
        target directly, allowing ``Texture.blit_buffer(canvas)`` with zero
        copies and clean lifetime management via a context manager.  The
        choice between ``thorvg_python`` (optional pip dependency) and a
        Cython wrapper (compiled backend) is an architecture decision for
        the Kivy maintainers.

    :returns: bytes, or ``None`` on failure.
    '''
    try:
        return bytes(canvas.buffer_arr)
    except Exception as exc:
        Logger.error(f'SvgThorvg: failed to extract pixel buffer: {exc}')
        return None


def _svg_parse_dim(s):
    '''Parse *s* as a positive finite float; return ``None`` on failure.

    Strips trailing ``px`` units before conversion.
    '''
    try:
        v = float((s or '').strip().rstrip('px').strip())
        return v if math.isfinite(v) and v > 0 else None
    except (ValueError, TypeError):
        return None


class SvgProviderThorvg(SvgProviderBase):
    '''ThorVG-backed SVG provider.

    Each instance represents one loaded SVG document.  The document is parsed
    once at :meth:`load` / :meth:`load_data` time; subsequent :meth:`render`
    calls create a fresh ThorVG ``Picture`` from the cached document data,
    apply any runtime overrides, and return RGBA bytes.
    '''

    _provider_name = 'thorvg'

    def __init__(self):
        self._source_path = None   # file path (load() path)
        self._source_data = None   # raw SVG bytes (always stored)
        self._element_ids = []
        self._doc_size = (0.0, 0.0)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self, source):
        '''Load an SVG from *source* (file path).

        Reads the file bytes, caches them for :meth:`render`, and scans the
        XML to populate :meth:`get_element_ids`.  Uses a temporary ThorVG
        ``Picture`` to retrieve the intrinsic document size.

        :returns: ``True`` on success.
        '''
        try:
            with open(source, 'rb') as fh:
                data = fh.read()
        except OSError as exc:
            Logger.error(f'SvgThorvg: cannot read {source!r}: {exc}')
            return False

        self._source_path = source
        self._source_data = data
        self._element_ids = _parse_element_ids(data)
        self._doc_size = self._probe_size_from_data(data)
        Logger.debug(f'SvgThorvg: loaded {source!r}  size={self._doc_size}')
        return True

    def load_data(self, data, mimetype='svg'):
        '''Load an SVG from raw *data* bytes.

        :returns: ``True`` on success.
        '''
        if not data:
            Logger.error('SvgThorvg: load_data() called with empty data')
            return False

        self._source_path = None
        self._source_data = data
        self._element_ids = _parse_element_ids(data)
        self._doc_size = self._probe_size_from_data(data)
        Logger.debug(
            f'SvgThorvg: loaded in-memory SVG ({len(data)} bytes)'
            f'  size={self._doc_size}'
        )
        return True

    def _probe_size_from_data(self, data):
        '''Create a temporary Picture just to read the intrinsic SVG size.

        Falls back to XML parsing when ThorVG returns non-finite dimensions
        (e.g. an SVG with only a ``height`` attribute and no ``width``).
        '''
        try:
            import thorvg_python as tvg
            engine = _get_engine()
            pic = tvg.Picture(engine)
            result = pic.load_data(data, 'svg', None, False)
            if result != tvg.Result.SUCCESS:
                Logger.warning(
                    f'SvgThorvg: could not probe SVG size (result={result})'
                )
                return (0.0, 0.0)
            res, w, h = pic.get_size()
            if math.isfinite(w) and math.isfinite(h) and w > 0 and h > 0:
                return (w, h)
            # ThorVG returned inf/nan - fall back to XML for viewBox / w / h.
            return self._probe_size_from_xml(data)
        except Exception as exc:
            Logger.warning(f'SvgThorvg: size probe failed: {exc}')
            return (0.0, 0.0)

    def _probe_size_from_xml(self, data):
        '''Parse width/height/viewBox directly from the SVG XML.'''
        try:
            root = ET.fromstring(data)

            w = _svg_parse_dim(root.get('width'))
            h = _svg_parse_dim(root.get('height'))

            # Try viewBox as a fallback for missing/non-numeric w or h.
            vb = root.get('viewBox') or ''
            vb_parts = vb.replace(',', ' ').split()
            if len(vb_parts) == 4:
                w = w or _svg_parse_dim(vb_parts[2])
                h = h or _svg_parse_dim(vb_parts[3])

            if w and h:
                return (w, h)
            # If only one dimension is known, assume square.
            if w:
                return (w, w)
            if h:
                return (h, h)
            Logger.warning(
                'SvgThorvg: could not determine SVG dimensions from XML'
            )
            return (0.0, 0.0)
        except ET.ParseError as exc:
            Logger.warning(f'SvgThorvg: XML size fallback failed: {exc}')
            return (0.0, 0.0)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_document_size(self):
        return self._doc_size

    def get_element_ids(self):
        return list(self._element_ids)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, width, height, current_color=None, element_overrides=None):
        '''Rasterize the SVG and return raw RGBA bytes.

        A fresh ThorVG ``Picture`` and ``SwCanvas`` are created on each call
        so that element override mutations do not persist across renders.

        :param int width: Output width in pixels (must be > 0).
        :param int height: Output height in pixels (must be > 0).
        :param current_color: If set, every ``currentColor`` token in the SVG
            source is replaced with this colour before loading into ThorVG.
        :param element_overrides: Per-element visibility/opacity dict.
        :returns: RGBA bytes or ``None`` on failure.
        '''
        if not self._source_data:
            Logger.error('SvgThorvg: render() called before load()')
            return None
        if width <= 0 or height <= 0:
            Logger.warning(
                f'SvgThorvg: render() called with invalid size'
                f' ({width} x {height})'
            )
            return None

        try:
            import thorvg_python as tvg
        except ImportError:
            Logger.error(
                'SvgThorvg: thorvg-python is not installed. '
                'Run: pip install thorvg-python'
            )
            return None

        engine = _get_engine()

        # ---- set up canvas ----
        canvas = tvg.SwCanvas(engine)
        result = canvas.set_target(width, height)
        if result != tvg.Result.SUCCESS:
            Logger.error(
                f'SvgThorvg: set_target({width}, {height}) failed: {result}'
            )
            canvas.destroy()
            return None

        # ---- prepare SVG data (apply currentColor if needed) ----
        svg_data = self._source_data
        if current_color is not None:
            svg_data = _apply_current_color(svg_data, current_color)

        # ---- load picture ----
        pic = tvg.Picture(engine)
        result = pic.load_data(svg_data, 'svg', None, True)
        if result != tvg.Result.SUCCESS:
            Logger.error(
                f'SvgThorvg: Picture.load_data() failed: {result}'
            )
            canvas.destroy()
            return None

        pic.set_size(float(width), float(height))

        # ---- apply element overrides ----
        if element_overrides:
            for elem_id, overrides in element_overrides.items():
                hash_id = _generate_id(elem_id)
                paint = _picture_get_paint(pic, hash_id)
                if paint is None:
                    # Warning logged by widget layer; skip silently here.
                    continue
                visible = overrides.get('visible', True)
                if not visible:
                    paint.set_opacity(0)
                else:
                    opacity_f = overrides.get('opacity', 1.0)
                    paint.set_opacity(max(0, min(255, int(opacity_f * 255))))

        # ---- render ----
        canvas.add(pic)
        canvas.update()
        canvas.draw(True)
        canvas.sync()

        rgba = _rgba_bytes_from_canvas(canvas)
        canvas.destroy()

        if rgba is None:
            Logger.error('SvgThorvg: failed to extract RGBA bytes from canvas')

        return rgba


# Self-register when this module is imported.
SvgLoader.register(SvgProviderThorvg)
