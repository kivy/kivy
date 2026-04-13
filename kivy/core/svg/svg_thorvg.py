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


def _get_engine():
    '''Return the shared ThorVG Engine, initialising it if needed.'''
    global _engine
    if _engine is None:
        import thorvg_python as tvg
        _engine = tvg.Engine(threads=0)
    return _engine


def _generate_id(name):
    '''Hash *name* to the uint32 paint ID that ThorVG uses internally.

    Uses ``Accessor.accessor_generate_id()``, which is a pure hash function
    and does not require a loaded Picture.  The Accessor is a module-level
    singleton so the initialisation cost is paid only once.
    '''
    global _accessor
    from thorvg_python.accessor import Accessor
    engine = _get_engine()
    if _accessor is None:
        _accessor = Accessor(engine, None)
    return _accessor.accessor_generate_id(name)


def _extract_element_ids_xml(svg_bytes):
    '''Fallback: return ``id`` attribute values from the SVG XML.

    Used when the installed ``thorvg-python`` predates the accessible-mode API
    (``Picture.set_accessible`` / ``Accessor.get_name``).  Returns *all* XML
    ``id`` attributes, including the root ``<svg>`` element which is not
    addressable as a ThorVG Paint node.

    Prefer :func:`_extract_element_ids_accessible` when available.
    '''
    ids = []
    try:
        root = ET.fromstring(svg_bytes)
        for elem in root.iter():
            eid = elem.get('id')
            if eid:
                ids.append(eid)
    except ET.ParseError as exc:
        Logger.warning(
            f'SvgThorvg: XML parse error scanning element IDs: {exc}'
        )
    return ids


def _extract_element_ids_accessible(pic, engine):
    '''Return element IDs directly from ThorVG using the accessible-mode API.

    Requires ``thorvg-python`` built against ThorVG ≥ master/post-1.0.3 (PR
    #4294), which adds ``Picture.set_accessible`` and ``Accessor.get_name``.

    ``pic`` must have been created with ``set_accessible(True)`` **before**
    ``load_data()`` was called.  The paint tree is walked via
    ``Accessor.set()``; inside the callback ``Accessor.get_name(hash_id)``
    returns the original SVG ``id`` string for every named element.

    Only paint nodes that carry a non-zero ID *and* have a resolvable name are
    included, so the root ``<svg>`` element (which is not a Paint node) is
    automatically excluded.

    :param pic: A loaded ``thorvg_python.Picture`` with accessible mode enabled.
    :param engine: The shared ThorVG ``Engine``.
    :returns: List of original SVG ``id`` strings in paint-tree order.
    '''
    from thorvg_python.accessor import Accessor
    from thorvg_python.paint import Paint as TvgPaint

    ids = []
    accessor = Accessor(engine, None)

    def _visitor(paint_ptr, _data):
        p = TvgPaint(engine, paint_ptr)
        h = p.get_id()
        if h:
            name = accessor.get_name(h)
            if name is not None:
                ids.append(name)
        return True  # continue traversal

    accessor.set(pic, _visitor, b'')
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

        Reads the file bytes, caches them for :meth:`render`, and uses a
        single ThorVG ``Picture`` (with accessible mode enabled) to retrieve
        both the intrinsic document size and the addressable element IDs via
        :func:`_extract_element_ids_accessible`.

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
        self._doc_size, self._element_ids = self._probe_from_data(data)
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
        self._doc_size, self._element_ids = self._probe_from_data(data)
        Logger.debug(
            f'SvgThorvg: loaded in-memory SVG ({len(data)} bytes)'
            f'  size={self._doc_size}'
        )
        return True

    def _probe_from_data(self, data):
        '''Create a temporary Picture to read the SVG size and element IDs.

        Sets ``accessible=True`` before loading so that
        :func:`_extract_element_ids_accessible` can retrieve the original SVG
        ``id`` strings directly from ThorVG without XML parsing.

        Falls back to XML-based element ID discovery when the installed
        ``thorvg-python`` does not support the accessible-mode API (i.e. pre
        ThorVG master/PR-#4294).

        Falls back to XML dimension parsing when ThorVG returns non-finite
        dimensions (e.g. an SVG with only a ``height`` attribute).

        :returns: ``((w, h), element_ids)`` tuple.
        '''
        try:
            import thorvg_python as tvg
            engine = _get_engine()
            pic = tvg.Picture(engine)

            # Enable accessible mode so get_name() works inside the callback.
            # Graceful fallback: older thorvg-python builds lack this method.
            accessible_supported = hasattr(pic, 'set_accessible')
            if accessible_supported:
                pic.set_accessible(True)

            result = pic.load_data(data, 'svg', None, False)
            if result != tvg.Result.SUCCESS:
                Logger.warning(
                    f'SvgThorvg: could not probe SVG (result={result})'
                )
                return (0.0, 0.0), []

            # --- size ---
            res, w, h = pic.get_size()
            if math.isfinite(w) and math.isfinite(h) and w > 0 and h > 0:
                size = (w, h)
            else:
                size = self._probe_size_from_xml(data)

            # --- element IDs ---
            if accessible_supported:
                element_ids = _extract_element_ids_accessible(pic, engine)
            else:
                Logger.debug(
                    'SvgThorvg: accessible mode not available; '
                    'falling back to XML for element IDs'
                )
                element_ids = _extract_element_ids_xml(data)

            return size, element_ids

        except Exception as exc:
            Logger.warning(f'SvgThorvg: probe failed: {exc}')
            return (0.0, 0.0), []

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
                paint = pic.get_paint(hash_id)
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
