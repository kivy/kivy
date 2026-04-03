'''
SvgWidget
=========

A Kivy widget for displaying SVG content using adaptive rasterization via
the :mod:`kivy.core.svg` provider system.

.. rubric:: Features

- SVG loading from :attr:`~SvgWidget.source` (local file path or in-memory
  SVG ``bytes``; :class:`AsyncSvgWidget` additionally accepts HTTP/HTTPS URLs)
- Efficient downscaling using mipmaps (enabled by default)
- Re-rasterization at higher resolution when the display scale crosses an
  internal threshold
- Limited runtime document customisation:

  - :attr:`~SvgWidget.current_color` - sets the CSS ``currentColor`` value
  - :attr:`~SvgWidget.element_overrides` - per-element visibility and opacity
    by SVG element ``id``

- :class:`AsyncSvgWidget` adds asynchronous HTTP/HTTPS loading

.. rubric:: Difference from the SVG image provider

The SVG image provider (``kivy.core.image``) lets you use
``Image(source="file.svg")`` and renders once at a fixed size.
``SvgWidget`` differs in:

- **Adaptive re-rasterization** - re-renders when scaling up beyond threshold
- **Mipmap-first** - mipmaps enabled by default
- **``current_color``** - CSS ``currentColor`` injection not available via
  the image pipeline
- **Element overrides** - per-element visibility/opacity not available via
  the image pipeline

.. rubric:: Basic usage

::

    from kivy.uix.svg import SvgWidget

    svg = SvgWidget(source='diagram.svg', size_hint=(None, None), size=(64, 64))

KV::

    SvgWidget:
        source: 'diagram.svg'
        current_color: 1, 0, 0   # red currentColor
        on_load: print('SVG ready')

    AsyncSvgWidget:
        source: 'https://example.com/diagram.svg'

.. rubric:: SVG icon button

Combine :class:`~kivy.uix.behaviors.ToggleButtonBehavior` with
:class:`SvgWidget` to create a tappable icon that changes colour on toggle.
This pattern works with any SVG that uses ``stroke="currentColor"`` or
``fill="currentColor"``.  Most popular svg icon libraries use ``currentColor`` by
default, including `Lucide <https://lucide.dev>`_, `Heroicons
<https://heroicons.com>`_, and `Tabler Icons <https://tabler.io/icons>`_.

::

    # Python
    from kivy.uix.behaviors import ToggleButtonBehavior
    from kivy.uix.svg import SvgWidget

    class StarIconToggleButton(ToggleButtonBehavior, SvgWidget):
        pass

    # KV
    <StarIconToggleButton>:
        source: 'star.svg'
        size_hint: None, None
        size: '64dp', '64dp'
        fit_mode: 'contain'
        mipmap: False
        current_color: 'gold' if self.activated else 'grey'

.. versionadded:: 3.0.0
'''

from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.logger import Logger
from kivy.network.urlrequest import UrlRequest
from kivy.properties import (
    AliasProperty,
    BooleanProperty,
    ColorProperty,
    DictProperty,
    ListProperty,
    ObjectProperty,
    OptionProperty,
)
from kivy.resources import resource_find
from kivy.uix.image import Image
from kivy.uix.widget import Widget

__all__ = ('SvgWidget', 'AsyncSvgWidget')

_SvgLoader = None


def _next_power_of_2(n):
    '''Return the smallest power of 2 that is >= n (minimum 1).'''
    n = int(n)
    if n <= 1:
        return 1
    return 1 << (n - 1).bit_length()


def _get_svg_loader():
    global _SvgLoader
    if _SvgLoader is None:
        from kivy.core.svg import SvgLoader
        _SvgLoader = SvgLoader
    return _SvgLoader


class SvgWidget(Widget):
    '''Widget that displays an SVG document using adaptive rasterization.

    The SVG is rasterized to a :class:`~kivy.graphics.texture.Texture` via
    the :mod:`kivy.core.svg` provider.  The texture is re-created when the
    display size grows beyond :attr:`_RERENDER_THRESHOLD` times the current
    raster size, keeping the image sharp at larger scales without wasting GPU
    memory at smaller ones.

    Downscaling is handled efficiently by OpenGL mipmaps
    (:attr:`mipmap` defaults to ``True``).
    '''

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    source = ObjectProperty(None, allownone=True)
    '''SVG source - a file path, raw bytes, or (for :class:`AsyncSvgWidget`)
    an HTTP/HTTPS URL.

    The type determines how the SVG is loaded:

    - ``str`` or :class:`pathlib.Path` - resolved via ``resource_find`` and
      loaded from the local filesystem.
    - ``bytes`` or ``bytearray`` - loaded directly as in-memory SVG data;
      no file I/O is performed.  Useful for embedding SVG content in code.

    When passing ``bytes``, Kivy forwards them to the SVG renderer unchanged.
    No encoding conversion is performed, so the byte sequence must already
    match the encoding declared in the SVG (e.g. ``encoding="utf-8"`` or
    ``encoding="gb2312"``).  Use ``open(path, 'rb')`` or an explicit
    ``str.encode(encoding)`` call to produce correctly encoded bytes; the
    proper encoding is the caller's responsibility.

    Setting this property automatically triggers a load and rasterize.

    :attr:`source` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to ``None``.
    '''

    texture = ObjectProperty(None, allownone=True)
    '''Current rasterized :class:`~kivy.graphics.texture.Texture`.

    Updated after every successful rasterization (including re-renders on
    scale-up).

    :attr:`texture` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to ``None``.
    '''

    texture_size = ListProperty([0, 0])
    '''Pixel dimensions of the current :attr:`texture`.

    Updated whenever :attr:`texture` changes.  Reflects the size at which the
    SVG was last rasterized, which equals the widget size at render time.

    Use this to read back the rendered resolution (for example, to pass to a
    shader or to report in a UI label).

    .. note::

        Do **not** use ``texture_size`` to drive the widget size (e.g.
        ``size: self.texture_size`` in KV).  The widget must have a non-zero
        size before rasterization can produce a texture, so this creates a
        circular dependency that leaves the widget invisible.  Use
        :attr:`viewbox_size` instead.

    :attr:`texture_size` is a :class:`~kivy.properties.ListProperty` and
    defaults to ``[0, 0]``.
    '''

    fit_mode = OptionProperty(
        'scale-down',
        options=('scale-down', 'fill', 'contain', 'cover'),
    )
    '''Scaling mode for display within the widget bounds.

    Identical in meaning to :attr:`~kivy.uix.image.Image.fit_mode`.

    Available options:

    - ``"scale-down"`` - never upscales; preserves aspect ratio.
    - ``"fill"`` - stretches to fill the widget; ignores aspect ratio.
    - ``"contain"`` - fits inside widget; may upscale; preserves ratio.
    - ``"cover"`` - fills widget; may crop; preserves ratio.

    :attr:`fit_mode` is an :class:`~kivy.properties.OptionProperty` and
    defaults to ``'scale-down'``.
    '''

    color = ColorProperty([1, 1, 1, 1])
    '''Tint colour applied via the canvas ``Color`` instruction.

    :attr:`color` is a :class:`~kivy.properties.ColorProperty` and
    defaults to ``[1, 1, 1, 1]`` (opaque white - no tint).
    '''

    mipmap = BooleanProperty(True)
    '''Enable mipmap generation on the rasterized texture.

    Mipmaps allow efficient GPU downscaling without aliasing artefacts.
    Defaults to ``True`` (unlike :class:`~kivy.uix.image.Image`).

    Changing this property after load triggers a re-rasterization.

    :attr:`mipmap` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to ``True``.
    '''

    current_color = ColorProperty([0, 0, 0, 1])
    '''RGB colour injected for the CSS ``currentColor`` keyword at render time.

    Every ``currentColor`` token in the SVG source is replaced with this
    colour before rasterization.  Changing this property triggers a
    re-render at the current raster size.

    Per the SVG spec, ``currentColor`` is a pure RGB value - opacity is a
    separate concern expressed via ``fill-opacity`` / ``stroke-opacity``
    attributes in the SVG source.  Only the red, green and blue components
    of this property are used; the alpha component is ignored.

    :attr:`current_color` is a :class:`~kivy.properties.ColorProperty` and
    defaults to ``[0, 0, 0, 1]`` (black).
    '''

    element_overrides = DictProperty({})
    '''Per-element render overrides keyed by SVG element ``id``.

    Each value is a dict with optional keys:

    - ``'visible'`` (bool) - ``False`` forces opacity to 0.
    - ``'opacity'`` (float 0.0-1.0) - overrides the SVG native opacity when
      the element is visible.

    Absent keys fall back to SVG defaults.  Changing this property triggers
    a re-render at the current raster size.

    Example::

        svg.element_overrides = {
            'badge':     {'visible': False},
            'highlight': {'opacity': 0.5},
        }

    :attr:`element_overrides` is a :class:`~kivy.properties.DictProperty`
    and defaults to ``{}``.
    '''

    viewbox_size = ListProperty([0, 0])
    '''Intrinsic SVG dimensions from the ``viewBox`` or ``width``/``height``
    attributes.  Set at load time, before rasterization; ``[0, 0]`` before
    any source is loaded.

    This is the correct property to use when you want the widget to display
    at the SVG's natural pixel size.  Because ``viewbox_size`` is populated
    before the deferred rasterize fires, a KV binding like::

        SvgWidget:
            size_hint: None, None
            size: self.viewbox_size

    works without a circular dependency: the size is known by the time the
    first rasterization is scheduled, so the texture is produced at exactly
    the right dimensions.

    Contrast with :attr:`texture_size` (set *after* rasterization, so it
    cannot safely drive the widget size) and :attr:`norm_image_size` (depends
    on ``self.size`` internally, same circular problem).

    :attr:`viewbox_size` is a :class:`~kivy.properties.ListProperty` and
    defaults to ``[0, 0]``.
    '''

    loaded = BooleanProperty(False)
    '''``True`` once the SVG has been successfully loaded and the first
    texture is ready.  Resets to ``False`` when :attr:`source` changes or
    :meth:`reload` is called.

    Use this as a guard before calling element manipulation methods::

        if svg.loaded:
            svg.hide_element('badge')

    :attr:`loaded` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to ``False``.
    '''

    status = OptionProperty(
        'empty',
        options=('empty', 'loading', 'ready', 'error'),
    )
    '''Current load state.

    +------------+-------------------------------------+
    | Value      | Meaning                             |
    +============+=====================================+
    | ``empty``  | No source set                       |
    +------------+-------------------------------------+
    | ``loading``| Source set; loading in progress     |
    +------------+-------------------------------------+
    | ``ready``  | SVG loaded and texture available    |
    +------------+-------------------------------------+
    | ``error``  | Load or render failed               |
    +------------+-------------------------------------+

    ``loaded`` is always equivalent to ``status == 'ready'``.  Use whichever
    reads more clearly: ``status`` when you need to distinguish between states
    (e.g. show a spinner while ``'loading'``, an error icon on ``'error'``),
    or ``loaded`` for a simple boolean guard (``if self.loaded:``).

    :attr:`status` is an :class:`~kivy.properties.OptionProperty` and
    defaults to ``'empty'``.
    '''

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    __events__ = ('on_load', 'on_error')

    # ------------------------------------------------------------------
    # Private state
    # ------------------------------------------------------------------

    def _get_image_ratio(self):
        if self.texture:
            w, h = self.texture.size
            return w / max(1.0, h)
        vw, vh = self.viewbox_size
        if vh:
            return vw / vh
        return 1.0

    image_ratio = AliasProperty(
        _get_image_ratio,
        bind=('texture', 'viewbox_size'),
        cache=True,
    )

    def get_norm_image_size(self):
        '''Return the display size of the SVG after applying :attr:`fit_mode`.

        Mirrors :meth:`~kivy.uix.image.Image.get_norm_image_size` exactly.
        '''
        if not self.texture:
            return list(self.size)

        ratio = self.image_ratio
        w, h = self.size
        tw, th = self.texture.size

        if self.fit_mode == 'cover':
            widget_ratio = w / max(1, h)
            if widget_ratio > ratio:
                return [w, (w * th) / tw]
            else:
                return [(h * tw) / th, h]
        elif self.fit_mode == 'fill':
            return [w, h]
        elif self.fit_mode == 'contain':
            iw = w
        else:  # scale-down
            iw = min(w, tw)

        ih = iw / ratio
        if ih > h:
            if self.fit_mode == 'contain':
                ih = h
            else:
                ih = min(h, th)
            iw = ih * ratio
        return [iw, ih]

    norm_image_size = AliasProperty(
        get_norm_image_size,
        bind=('texture', 'size', 'image_ratio', 'fit_mode'),
        cache=True,
    )
    '''The portion of the widget area actually occupied by the rendered image
    after :attr:`fit_mode` geometry is applied.

    For example, with ``fit_mode='contain'`` on a 400x400 widget displaying a
    400x250 SVG, ``norm_image_size`` returns ``[400, 250]`` — the image fills
    the full width but only part of the height.

    Use this to center an overlay on the rendered content, to do hit-testing
    against the visible image region, or to place a sibling widget alongside
    the actual (not padded) image area.

    .. note::

        Do **not** use ``norm_image_size`` to drive the widget size.
        :meth:`get_norm_image_size` reads ``self.size`` internally, so binding
        ``size: self.norm_image_size`` creates the same circular dependency as
        :attr:`texture_size`.  Use :attr:`viewbox_size` for that purpose.

    :attr:`norm_image_size` is an :class:`~kivy.properties.AliasProperty`
    and is read-only.
    '''

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self, **kwargs):
        self._svg_provider = None
        self._raster_size = [0, 0]
        self._deferred_rasterize = None
        fbind = self.fbind
        fbind('source', self.texture_update)
        fbind('mipmap', self._on_mipmap)
        fbind('current_color', self._on_render_param)
        fbind('element_overrides', self._on_render_param)
        fbind('size', self._check_rerender)
        super().__init__(**kwargs)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def texture_update(self, *largs):
        '''Load (or reload) the SVG from :attr:`source` and rasterize.

        Called automatically when :attr:`source` changes.  Can also be
        called manually to force a reload.
        '''
        source = self.source
        if not source:
            self._clear_svg()
            return

        self.loaded = False
        self.status = 'loading'

        loader = _get_svg_loader()

        if isinstance(source, (bytes, bytearray)):
            provider = loader.load_data(source)
            if not provider:
                msg = 'SvgWidget: failed to load SVG from in-memory bytes'
                Logger.error(msg)
                self._set_error(msg)
                return
        else:
            path = resource_find(str(source))
            if not path:
                msg = f'SvgWidget: source not found: {source!r}'
                Logger.error(msg)
                self._set_error(msg)
                return
            provider = loader.load(path)
            if not provider:
                msg = f'SvgWidget: no SVG provider could load {path!r}'
                Logger.error(msg)
                self._set_error(msg)
                return

        self._svg_provider = provider
        self.viewbox_size = list(provider.get_document_size())

        # Always defer the first rasterize by one clock tick.  This lets KV
        # finish applying all rules (including size bindings) before we render,
        # so the first texture is produced at the correct widget size rather
        # than the Widget default of (100, 100).
        if self._deferred_rasterize:
            self._deferred_rasterize.cancel()
        self._deferred_rasterize = Clock.schedule_once(
            self._deferred_rasterize_cb, 0
        )

    def reload(self):
        '''Discard the current SVG document and reload from :attr:`source`.

        Resets :attr:`loaded` and :attr:`status` immediately; the new texture
        is available after the next successful rasterization.
        '''
        self._svg_provider = None
        self._raster_size = [0, 0]
        self.loaded = False
        self.status = 'loading'
        old_source = self.source
        self.source = None
        self.source = old_source

    def get_element_ids(self):
        '''Return a list of all SVG element ``id`` values in the document.

        The list is built once at load time.  Returns an empty list if the
        SVG has not been loaded yet, and logs a warning.

        :rtype: list[str]
        '''
        if not self.loaded:
            Logger.warning(
                'SvgWidget: get_element_ids() called before SVG is loaded'
            )
            return []
        return self._svg_provider.get_element_ids()

    def hide_element(self, element_id):
        '''Hide the SVG element with the given ``id``.

        Convenience wrapper for ``set_element_visible(element_id, False)``.

        :param str element_id: The SVG element ``id`` attribute value.
        '''
        self.set_element_visible(element_id, False)

    def show_element(self, element_id):
        '''Show the SVG element with the given ``id``.

        Convenience wrapper for ``set_element_visible(element_id, True)``.

        :param str element_id: The SVG element ``id`` attribute value.
        '''
        self.set_element_visible(element_id, True)

    def set_element_visible(self, element_id, visible):
        '''Set the visibility of an SVG element by its ``id``.

        Stores the override in :attr:`element_overrides` and triggers a
        re-render.  If the SVG is not yet loaded, the override is still
        stored and will be applied when the document loads.

        If *element_id* is not found in the document, a warning is logged
        but the override is still stored.

        :param str element_id: The SVG element ``id``.
        :param bool visible: ``True`` to show, ``False`` to hide.
        '''
        if not self.loaded:
            Logger.warning(
                'SvgWidget: set_element_visible() called before SVG is '
                'loaded; override will be applied on load.'
            )
        elif element_id not in self._svg_provider.get_element_ids():
            Logger.warning(
                f'SvgWidget: element id {element_id!r} not found in SVG'
                ' document'
            )
        self._set_element_override(element_id, 'visible', visible)

    def is_element_visible(self, element_id):
        '''Return whether the element with *element_id* is currently visible.

        Returns ``True`` for elements with no override (SVG default).

        :param str element_id: The SVG element ``id``.
        :rtype: bool
        '''
        return self.element_overrides.get(element_id, {}).get('visible', True)

    def set_element_opacity(self, element_id, opacity):
        '''Set the opacity override for an SVG element by its ``id``.

        Stores the override in :attr:`element_overrides` and triggers a
        re-render.  If the SVG is not yet loaded, the override is still
        stored.

        If *element_id* is not found in the document, a warning is logged.

        :param str element_id: The SVG element ``id``.
        :param float opacity: Opacity value 0.0 (transparent) - 1.0 (opaque).
        '''
        if not self.loaded:
            Logger.warning(
                'SvgWidget: set_element_opacity() called before SVG is '
                'loaded; override will be applied on load.'
            )
        elif element_id not in self._svg_provider.get_element_ids():
            Logger.warning(
                f'SvgWidget: element id {element_id!r} not found in SVG'
                ' document'
            )
        self._set_element_override(element_id, 'opacity', float(opacity))

    def get_element_opacity(self, element_id):
        '''Return the current opacity override for *element_id*.

        Returns ``1.0`` for elements with no opacity override.

        :param str element_id: The SVG element ``id``.
        :rtype: float
        '''
        return float(self.element_overrides.get(element_id, {}).get('opacity', 1.0))

    def reset_element_overrides(self):
        '''Clear all element visibility and opacity overrides.

        Triggers a re-render that restores all elements to their SVG defaults.
        '''
        self.element_overrides = {}

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_load(self, *args):
        pass

    def on_error(self, error):
        pass

    def on_texture(self, instance, texture):
        self.texture_size = texture.size if texture else [0, 0]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_element_override(self, element_id, key, value):
        '''Update a single key in :attr:`element_overrides` for *element_id*.

        Creates the entry if absent.  Triggers a re-render via the
        ``element_overrides`` property binding.
        '''
        overrides = dict(self.element_overrides)
        entry = dict(overrides.get(element_id, {}))
        entry[key] = value
        overrides[element_id] = entry
        self.element_overrides = overrides

    def _on_mipmap(self, *largs):
        '''Re-rasterize when the mipmap setting changes.'''
        if self._svg_provider and self._raster_size[0] > 0:
            self._rasterize(*self._raster_size)

    def _on_render_param(self, *largs):
        '''Re-render at the current widget size when current_color or
        element_overrides change.'''
        if self._svg_provider and self._raster_size[0] > 0:
            w, h = self.size
            if w > 0 and h > 0:
                self._rasterize(int(w), int(h))

    def _check_rerender(self, *largs):
        '''Called on every size change.  Re-rasterizes when the widget size
        crosses into a larger power-of-2 bucket than the current raster size,
        aligning re-renders with mipmap level boundaries.

        Widget size (not ``norm_image_size``) is used as the threshold so that
        ``fit_mode='scale-down'`` does not suppress re-renders: even when the
        texture is smaller than the widget, we still want to produce a texture
        at the widget's full resolution.
        '''
        if not self._svg_provider:
            return
        w, h = self.size
        if w <= 0 or h <= 0:
            return

        rw, rh = self._raster_size

        if rw <= 0 or rh <= 0:
            # Not yet rasterized yet.  Schedule a deferred rasterize rather
            # than calling _rasterize() synchronously.  Calling it here would
            # dispatch on_load before KV finishes applying all rules for this
            # widget (property bindings are applied in source order, so an
            # on_load: handler that appears after size: or source: in a KV
            # rule would miss the event entirely).  Deferring by one clock
            # tick lets all KV rules settle first.
            if not self._deferred_rasterize:
                self._deferred_rasterize = Clock.schedule_once(
                    self._deferred_rasterize_cb, 0
                )
            return

        # Re-rasterize when the dominant widget dimension crosses into the
        # next power-of-2 bucket.  The dominant raster dimension is always a
        # power of 2 (the snapped value), so max(rw, rh) gives the bucket.
        dom_widget = max(int(w), int(h))
        dom_raster = max(rw, rh)
        if _next_power_of_2(dom_widget) > dom_raster:
            self._rasterize(int(w), int(h))

    def _deferred_rasterize_cb(self, dt):
        self._deferred_rasterize = None
        w, h = self.size
        if w > 0 and h > 0 and self._svg_provider:
            self._rasterize(int(w), int(h))

    def _rasterize(self, widget_w, widget_h):
        '''Rasterize the SVG at a pixel size derived from (widget_w, widget_h).

        The render dimensions maintain the SVG's natural aspect ratio while
        fitting within widget_w and widget_h, producing a texture with the
        correct ratio.  Kivy's ``norm_image_size`` then handles display
        scaling within the widget bounds.
        '''
        if not self._svg_provider:
            return

        vw, vh = self.viewbox_size
        if vw > 0 and vh > 0:
            svg_ratio = vw / vh
            widget_ratio = widget_w / max(1, widget_h)
            if widget_ratio > svg_ratio:
                render_h = widget_h
                render_w = max(1, int(widget_h * svg_ratio))
            else:
                render_w = widget_w
                render_h = max(1, int(widget_w / svg_ratio))
        else:
            render_w, render_h = widget_w, widget_h

        # Snap the dominant (larger) dimension to the next power-of-2 bucket
        # and scale the other dimension proportionally.  Snapping both
        # independently would break the aspect ratio for non-square SVGs
        # (e.g. 512x358 → 512x512, stretching the image).
        if render_w >= render_h:
            bucket_w = _next_power_of_2(render_w)
            bucket_h = max(1, round(bucket_w * render_h / render_w))
        else:
            bucket_h = _next_power_of_2(render_h)
            bucket_w = max(1, round(bucket_h * render_w / render_h))

        rgba = self._svg_provider.render(
            bucket_w,
            bucket_h,
            current_color=self.current_color,
            element_overrides=self.element_overrides or None,
        )

        if rgba is None:
            msg = (
                f'SvgWidget: render failed for {self.source!r}'
                f' at {bucket_w}x{bucket_h}'
            )
            Logger.error(msg)
            self._set_error(msg)
            return

        tex = Texture.create(
            size=(bucket_w, bucket_h),
            colorfmt='rgba',
            mipmap=self.mipmap,
        )
        # --- Future optimisation: zero-copy texture upload -------------------
        #
        # Current path (this code):
        #   ThorVG canvas  ->  bytes() copy (~47 MB at 4K)  ->  blit_buffer
        #
        # The copy exists because blit_buffer is documented to accept a bytes-
        # like object, and _rgba_bytes_from_canvas() converts canvas.buffer_arr
        # (a ctypes array) to bytes.  canvas.buffer_arr already implements the
        # Python buffer protocol, so blit_buffer *could* read ThorVG's memory
        # directly - eliminating the copy entirely.
        #
        # What is needed to make this safe:
        #
        # 1. A Cython wrapper for the ThorVG SwCanvas that exposes buffer_arr
        #    as a proper memoryview (the ctypes array works today but is
        #    fragile; a Cython typed memoryview is the right vehicle).
        #
        # 2. The ThorVG SwCanvas object (not Kivy's canvas) must stay alive
        #    until blit_buffer returns.  On the main thread this is trivially
        #    true.  Once rasterization is moved to a background thread (see
        #    point 3), the SwCanvas must be kept alive explicitly - e.g. held
        #    in a local variable or a short-lived strong reference - until the
        #    main thread signals that the upload is complete.
        #
        # 3. Move the ThorVG render() call - the step that walks the SVG scene
        #    graph and writes pixels into the SwCanvas buffer - to a background
        #    thread (e.g. Python's ThreadPoolExecutor or a dedicated
        #    rasterization thread).  This prevents large or complex SVGs from
        #    freezing Kivy's event loop (animations, touch events) during
        #    rendering.  The SwCanvas lifetime management in point 2 is most
        #    cleanly solved here at the same time.
        #
        # Expected benefit: eliminates a ~47 MB allocation and memcpy per
        # frame at 4K.  At smaller sizes (e.g. 256x256 icon) the saving is
        # proportionally smaller (~256 KB) but the pattern is the same.
        # -------------------------------------------------------------------
        tex.blit_buffer(rgba, colorfmt='rgba', bufferfmt='ubyte')
        tex.flip_vertical()

        self._raster_size = [bucket_w, bucket_h]
        self.texture = tex

        if not self.loaded:
            self.loaded = True
            self.status = 'ready'
            self.dispatch('on_load')

    def _clear_svg(self):
        self._svg_provider = None
        self._raster_size = [0, 0]
        self.texture = None
        self.viewbox_size = [0, 0]
        self.loaded = False
        self.status = 'empty'

    def _set_error(self, msg):
        self.loaded = False
        self.status = 'error'
        self.dispatch('on_error', msg)


class AsyncSvgWidget(SvgWidget):
    '''Asynchronous variant of :class:`SvgWidget` that downloads SVG files
    from HTTP/HTTPS URLs in a background thread.

    Local file paths are loaded synchronously (same behaviour as
    :class:`SvgWidget`).  Remote URLs are downloaded in a daemon thread;
    the widget shows :attr:`loading_texture` while the download is in
    progress.

    .. note::

        The loading image and error image are taken from Kivy's global
        ``Loader.loading_image`` and ``Loader.error_image``, matching
        :class:`~kivy.uix.image.AsyncImage`.  To use a custom image, set
        these before creating any ``AsyncSvgWidget``::  The loading image
        supports GIF animation.

            from kivy.loader import Loader
            Loader.loading_image = 'my_spinner.gif'
            Loader.error_image   = 'my_error.png'

    Example KV usage::

        AsyncSvgWidget:
            source: 'https://example.com/icon.svg'
            on_load: print('downloaded and ready')
            on_error: print('failed:', args[1])
    '''

    loading_texture = ObjectProperty(None, allownone=True)
    '''Initial texture shown the moment a load starts, before the first GIF
    frame callback fires.

    Initialised to ``Loader.loading_image.texture`` in ``__init__``.  While
    loading is in progress the widget automatically tracks
    ``Loader.loading_image.texture`` so animated GIF placeholders play at
    full frame rate.  The binding is removed as soon as the SVG is ready or
    an error occurs.

    :attr:`loading_texture` is an :class:`~kivy.properties.ObjectProperty`
    and defaults to ``None``.
    '''

    error_texture = ObjectProperty(None, allownone=True)
    '''Texture shown when loading or rendering fails.

    Initialised to ``Loader.error_image.texture`` in ``__init__``.

    :attr:`error_texture` is an :class:`~kivy.properties.ObjectProperty`
    and defaults to ``None``.
    '''

    def __init__(self, **kwargs):
        self._pending_source = None
        self._pending_request = None
        self._loader_image = None

        # Initialise placeholder textures from Kivy's global Loader images,
        # matching how AsyncImage works.
        #
        # Loader.loading_image returns a raw ImageLoader (e.g. ImageLoaderSDL3)
        # which has no Kivy property system.  We create a kivy.uix.image.Image
        # widget from the same filename - it has texture as an ObjectProperty
        # so we can bind to frame changes and drive GIF animation.
        from kivy.loader import Loader
        super().__init__(**kwargs)
        try:
            self._loader_image = Image(
                source=Loader.loading_image.filename,
                fit_mode='scale-down',
                anim_delay=Loader.loading_image.anim_delay
                if hasattr(Loader.loading_image, 'anim_delay') else 0.25,
            )
            self.loading_texture = self._loader_image.texture
        except Exception:
            pass
        try:
            self.error_texture = Loader.error_image.texture
        except Exception:
            pass

        # Re-bind source to our async loader instead of the sync one.
        self.unbind(source=self.texture_update)
        self.fbind('source', self._load_source)
        # Trigger load if source was already set via kwargs.
        if self.source:
            self._load_source()

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------

    def texture_update(self, *largs):
        '''No-op - prevents the inherited synchronous load path.'''
        pass

    def get_norm_image_size(self):
        '''Return the display size after applying :attr:`fit_mode`.

        While loading or showing an error placeholder the texture is drawn
        at its natural size (``scale-down`` behaviour) regardless of
        :attr:`fit_mode`, so a small spinner GIF is never stretched to fill
        the widget.  Once the SVG is ready the base class logic applies.
        '''
        if self.status in ('loading', 'error') and self._loader_image:
            self._loader_image.size = self.size
            return list(self._loader_image.norm_image_size)
        return super().get_norm_image_size()

    norm_image_size = AliasProperty(
        get_norm_image_size,
        bind=('texture', 'size', 'image_ratio', 'fit_mode', 'status'),
        cache=True,
    )
    '''Extends the base :attr:`~SvgWidget.norm_image_size` to also
    recompute when :attr:`~SvgWidget.status` changes.'''

    # ------------------------------------------------------------------
    # Async load
    # ------------------------------------------------------------------

    def _load_source(self, *args):
        '''Triggered on :attr:`source` change.  Cancels any in-flight request,
        shows the loading placeholder, then dispatches to sync (local) or
        async (URI) loading.
        '''
        self._stop_loading_animation()

        if self._pending_request is not None:
            self._pending_request.cancel()
            self._pending_request = None

        source = self.source
        if not source:
            self._clear_svg()
            return

        self.loaded = False
        self.status = 'loading'
        self._start_loading_animation()
        self._pending_source = source

        if isinstance(source, (bytes, bytearray)):
            loader = _get_svg_loader()
            provider = loader.load_data(source)
            if not provider:
                msg = 'AsyncSvgWidget: failed to load SVG from in-memory bytes'
                Logger.error(msg)
                self._async_error(source, msg)
                return
            self._install_provider(provider)
        elif self.is_uri(source):
            self._pending_request = UrlRequest(
                source,
                on_success=self._on_download_success,
                on_failure=self._on_download_failure,
                on_error=self._on_download_error,
                req_headers={
                    'User-Agent': 'KivySvgWidget/3.0 (kivy svg widget; '
                                  'https://github.com/kivy/kivy)'
                },
                timeout=30,
            )
        else:
            path = resource_find(str(source))
            if not path:
                msg = f'AsyncSvgWidget: source not found: {source!r}'
                Logger.error(msg)
                self._async_error(source, msg)
                return
            self._do_sync_load(path)

    def _do_sync_load(self, path):
        '''Load a local file synchronously (same as SvgWidget but via the
        async-widget flow, preserving status transitions).'''
        loader = _get_svg_loader()
        provider = loader.load(path)
        if not provider:
            msg = f'AsyncSvgWidget: no provider could load {path!r}'
            Logger.error(msg)
            self._async_error(path, msg)
            return
        self._install_provider(provider)

    def _on_download_success(self, request, data):
        '''UrlRequest success callback - already on the main thread.'''
        self._pending_request = None
        if request.url != self._pending_source:
            return  # Source changed while download was in flight; discard.

        # UrlRequest may decode text/* responses to str even when decode=False.
        # svg_thorvg requires bytes throughout, so normalise here.
        if isinstance(data, str):
            data = data.encode('utf-8')

        loader = _get_svg_loader()
        provider = loader.load_data(data)
        if not provider:
            msg = f'AsyncSvgWidget: failed to load SVG data from {request.url!r}'
            Logger.error(msg)
            self._async_error(request.url, msg)
            return

        self._install_provider(provider)

    def _on_download_failure(self, request, result):
        '''UrlRequest failure callback - non-2xx HTTP status.'''
        self._pending_request = None
        if request.url != self._pending_source:
            return
        msg = f'AsyncSvgWidget: HTTP {request.resp_status} downloading {request.url!r}'
        Logger.error(msg)
        self._async_error(request.url, msg)

    def _on_download_error(self, request, error):
        '''UrlRequest error callback - network or timeout error.'''
        self._pending_request = None
        if request.url != self._pending_source:
            return
        msg = f'AsyncSvgWidget: error downloading {request.url!r}: {error}'
        Logger.error(msg)
        self._async_error(request.url, msg)

    def _async_error(self, source, msg):
        '''Main-thread error handler.'''
        if source != self._pending_source:
            return  # Stale; ignore.
        self._stop_loading_animation()
        self.texture = self.error_texture
        self._set_error(msg)

    # ------------------------------------------------------------------
    # Loading animation
    # ------------------------------------------------------------------

    def _start_loading_animation(self):
        '''Show the loading placeholder and bind to its texture so GIF
        animation frames update :attr:`~SvgWidget.texture` automatically.

        Safe to call when no loader image is available - does nothing in
        that case.
        '''
        img = self._loader_image
        if img is None:
            return
        self.texture = img.texture
        img.bind(texture=self._on_loading_texture)

    def _on_loading_texture(self, _instance, texture):
        '''Called each time the loading GIF advances a frame.

        Ignored once the SVG has finished loading so a late-arriving frame
        cannot overwrite the rasterized texture.
        '''
        if self.status == 'loading':
            self.texture = texture

    def _stop_loading_animation(self):
        '''Detach from the loading image so GIF frame callbacks stop.

        Safe to call multiple times or before :meth:`_start_loading_animation`.
        '''
        img = self._loader_image
        if img is not None:
            img.unbind(texture=self._on_loading_texture)

    def _install_provider(self, provider):
        '''Store *provider* and trigger the first rasterize.

        Rasterizes immediately if the widget already has a non-zero size,
        otherwise defers one clock tick (same pattern as
        :meth:`SvgWidget.texture_update`).
        '''
        self._stop_loading_animation()
        self._svg_provider = provider
        self.viewbox_size = list(provider.get_document_size())
        w, h = self.size
        if w > 0 and h > 0:
            self._rasterize(int(w), int(h))
        else:
            if self._deferred_rasterize:
                self._deferred_rasterize.cancel()
            self._deferred_rasterize = Clock.schedule_once(
                self._deferred_rasterize_cb, 0
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def is_uri(filename):
        '''Return ``True`` if *filename* is an HTTP or HTTPS URL.

        Non-string values (e.g. ``bytes``, :class:`pathlib.Path`) always
        return ``False``.

        :param filename: Source value to test.
        :rtype: bool
        '''
        if not isinstance(filename, str):
            return False
        proto = filename.split('://', 1)[0].lower()
        return proto in ('http', 'https')
