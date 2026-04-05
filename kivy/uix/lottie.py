'''
LottieWidget
============

A Kivy widget for displaying and controlling Lottie animations.

.. rubric:: Features

- Lottie JSON loading from :attr:`~LottieWidget.source` (local file path)
- Playback control via :attr:`state` (``'play'``, ``'pause'``, ``'stop'``),
  :meth:`seek`, and :attr:`progress` (0.0-1.0 normalised position)
- Standard image display properties: :attr:`fit_mode`, :attr:`color`,
  :attr:`norm_image_size`

- **Runtime DOM manipulation**
- **Segments and markers** - divide an animation into named or custom ranges
  and play them independently: :attr:`markers`, :meth:`play_segment`,
  :meth:`play_marker`
- **Slot overrides** - change colours, opacity, text, and images on named
  slots at runtime without reloading the file: :attr:`slots`,
  :meth:`has_slot`, :meth:`set_color`, :meth:`set_opacity`,
  :meth:`set_text`, :meth:`set_image`, :meth:`apply_slot`,
  :meth:`reset_slot`
- **Rendering quality** - tune the fidelity of blur and shadow effects:
  :meth:`set_quality`

.. rubric:: Basic usage

::

    from kivy.uix.lottie import LottieWidget

    w = LottieWidget(source='animation.json', size_hint=(None, None),
                     size=(400, 400), state='play')

KV::

    LottieWidget:
        source: 'animation.json'
        fit_mode: 'contain'
        state: 'play'
        eos: 'loop'
        on_load: print('ready', self.duration, 'seconds')
        on_eos: print('loop!')

.. rubric:: Slot colour override

::

    w = LottieWidget(source='branded.json')
    w.bind(on_load=lambda *a: w.set_color('brand_color', (0.2, 0.6, 1.0)))

.. versionadded:: 3.0.0
'''

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.properties import (
    AliasProperty,
    BooleanProperty,
    ColorProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
)
from kivy.resources import resource_find
from kivy.uix.widget import Widget

__all__ = ('LottieWidget',)

_Lottie = None


def _get_lottie():
    # lazy load and cache the Lottie class
    global _Lottie
    if _Lottie is None:
        from kivy.core.lottie import Lottie
        _Lottie = Lottie
    return _Lottie


class LottieWidget(Widget):
    '''Widget that displays a Lottie animation.

    The animation is rasterized to a
    :class:`~kivy.graphics.texture.Texture` by the configured Lottie
    provider (:mod:`kivy.core.lottie`).  The texture is shared with the
    canvas drawing instructions added by the KV rule in
    ``kivy/data/style.kv`` - the same rule that drives
    :class:`~kivy.uix.image.Image` and
    :class:`~kivy.uix.svg.SvgWidget`.

    All DOM manipulation methods delegate transparently to the underlying
    :class:`~kivy.core.lottie.LottieBase` provider.
    '''

    # ------------------------------------------------------------------
    # Display properties (mirrors Image / SvgWidget)
    # ------------------------------------------------------------------

    source = StringProperty('')
    '''Path to the Lottie JSON file.

    Changing this property automatically loads the new animation.

    :attr:`source` is a :class:`~kivy.properties.StringProperty` and
    defaults to ``''``.
    '''

    texture = ObjectProperty(None, allownone=True)
    '''Current rasterized :class:`~kivy.graphics.texture.Texture`.

    Updated on every :attr:`on_frame` event dispatched by the provider.

    :attr:`texture` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to ``None``.
    '''

    texture_size = ListProperty([0, 0])
    '''Pixel dimensions ``[w, h]`` of the current :attr:`texture`.

    Updated whenever :attr:`texture` changes.

    :attr:`texture_size` is a :class:`~kivy.properties.ListProperty` and
    defaults to ``[0, 0]``.
    '''

    fit_mode = OptionProperty(
        'contain',
        options=('scale-down', 'fill', 'contain', 'cover'),
    )
    '''Scaling mode for display within the widget bounds.

    Identical in meaning to :attr:`~kivy.uix.image.Image.fit_mode`.

    :attr:`fit_mode` is an :class:`~kivy.properties.OptionProperty` and
    defaults to ``'contain'``.
    '''

    color = ColorProperty([1, 1, 1, 1])
    '''Tint colour applied via the canvas ``Color`` instruction.

    :attr:`color` is a :class:`~kivy.properties.ColorProperty` and
    defaults to ``[1, 1, 1, 1]`` (opaque white - no tint).
    '''

    # ------------------------------------------------------------------
    # Status / state
    # ------------------------------------------------------------------

    loaded = BooleanProperty(False)
    '''``True`` once the animation has loaded successfully.

    Use this as a guard before calling DOM manipulation methods::

        if widget.loaded:
            widget.set_color('brand', (0.2, 0.6, 1.0))

    :attr:`loaded` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to ``False``.
    '''

    # ------------------------------------------------------------------
    # Playback properties
    # ------------------------------------------------------------------

    state = OptionProperty('stop', options=('play', 'pause', 'stop'))
    '''String, indicates whether to play, pause, or stop the animation::

        # start playing immediately at construction
        w = LottieWidget(source='anim.json', state='play')

        # start later
        w = LottieWidget(source='anim.json')
        w.state = 'play'

    :attr:`state` is an :class:`~kivy.properties.OptionProperty` and
    defaults to ``'stop'``.
    '''

    position = NumericProperty(0.0)
    '''Current playback position in seconds.

    Setting this property seeks the animation.

    :attr:`position` is a :class:`~kivy.properties.NumericProperty` and
    defaults to ``0.0``.
    '''

    duration = NumericProperty(0.0)
    '''Total animation duration in seconds (read-only after load).

    :attr:`duration` is a :class:`~kivy.properties.NumericProperty` and
    defaults to ``0.0``.
    '''

    total_frames = NumericProperty(0.0)
    '''Total number of frames in the animation (read-only after load).

    :attr:`total_frames` is a :class:`~kivy.properties.NumericProperty`
    and defaults to ``0.0``.
    '''

    def _get_progress(self):
        if self.duration <= 0:
            return 0.0
        return max(0.0, min(1.0, self.position / self.duration))

    def _set_progress(self, value):
        value = max(0.0, min(1.0, float(value)))
        if self.duration > 0:
            self.position = value * self.duration
        return True

    progress = AliasProperty(
        _get_progress,
        _set_progress,
        bind=('position', 'duration'),
        cache=True,
    )
    '''Normalised playback position in the range 0.0-1.0.

    A computed view of :attr:`position` / :attr:`duration`.  Setting it
    seeks the animation to the corresponding time.  Useful for binding
    directly to a :class:`~kivy.uix.slider.Slider`::

        Slider:
            min: 0
            max: 1
            value: anim.progress
            on_value: anim.progress = self.value

    :attr:`progress` is an :class:`~kivy.properties.AliasProperty` and
    defaults to ``0.0``.
    '''

    eos = OptionProperty('loop', options=('loop', 'stop', 'pause'))
    '''End-of-animation behaviour.

    * ``'loop'``  - restart from the beginning (default).
    * ``'stop'``  - halt and rewind to frame 0.  Use this when the first
      frame is the natural idle state of the animation (e.g. a spinner that
      should disappear or reset when done).
    * ``'pause'`` - halt and remain on the last frame.  Use this for
      one-shot animations that end in a new visual state (e.g. a character
      settling into a new pose).

    Both ``'stop'`` and ``'pause'`` cancel the playback clock; the only
    difference is whether the playhead rewinds to frame 0 (``'stop'``) or
    stays at the final frame (``'pause'``).

    :attr:`eos` is an :class:`~kivy.properties.OptionProperty` and
    defaults to ``'loop'``.
    '''

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    __events__ = ('on_load', 'on_eos', 'on_frame', 'on_error')

    # ------------------------------------------------------------------
    # Image display helpers (mirrors SvgWidget)
    # ------------------------------------------------------------------

    def _get_image_ratio(self):
        if self.texture:
            w, h = self.texture.size
            return w / max(1.0, h)
        return 1.0

    image_ratio = AliasProperty(
        _get_image_ratio,
        bind=('texture',),
        cache=True,
    )
    '''Aspect ratio of the current :attr:`texture` (width / height).

    :attr:`image_ratio` is a read-only :class:`~kivy.properties.AliasProperty`.
    '''

    def get_norm_image_size(self):
        '''Return the display size of the animation after applying
        :attr:`fit_mode`.

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
    '''The portion of the widget area actually occupied by the animation
    after :attr:`fit_mode` geometry is applied.

    :attr:`norm_image_size` is a read-only
    :class:`~kivy.properties.AliasProperty`.
    '''

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self, **kwargs):
        self._lottie = None
        self._updating_position = False  # flag to ignore position updates from provider
        fbind = self.fbind
        fbind('source', self._on_source)
        fbind('position', self._on_position_prop)
        fbind('eos', self._on_eos_prop)
        fbind('texture', self._on_texture)
        super().__init__(**kwargs)

    # ------------------------------------------------------------------
    # Property change handlers
    # ------------------------------------------------------------------

    def _on_source(self, *largs):
        source = self.source
        if not source:
            self._clear()
            return
        self.loaded = False
        path = resource_find(source) or source
        try:
            provider = _get_lottie()(
                filename=path,
                size=None,
                eos=self.eos,
            )
        except Exception as exc:
            msg = f'LottieWidget: failed to create provider for {source!r}: {exc}'
            Logger.error(msg)
            self._set_error(msg)
            return

        if provider is None:
            msg = f'LottieWidget: no Lottie provider available for {source!r}'
            Logger.error(msg)
            self._set_error(msg)
            return

        self._install_provider(provider)

    def _install_provider(self, provider):
        '''Store *provider* and hook up event bindings.'''
        if self._lottie is not None:
            self._lottie.unbind(
                on_load=self._on_provider_load,
                on_eos=self._on_provider_eos,
                on_frame=self._on_provider_frame,
            )

        self._lottie = provider
        provider.bind(
            on_load=self._on_provider_load,
            on_eos=self._on_provider_eos,
            on_frame=self._on_provider_frame,
        )

        # ThorVG loads synchronously: by the time we reach here _duration is
        # already set but _texture is still None (texture is created lazily on
        # the first _render_frame call to avoid requiring a GL context at load
        # time).  Always defer by one frame so callers have time to bind their
        # own on_load handlers after construction before the event fires.
        Clock.schedule_once(lambda dt: self._check_provider_ready(), 0)

    def _check_provider_ready(self):
        # Use _duration > 0 as the "successfully loaded" signal.  _texture is
        # intentionally None until the first render tick;
        if self._lottie and self._lottie._duration > 0 and not self.loaded:
            self._on_provider_load(self._lottie)

    def _on_provider_load(self, provider, *largs):
        if provider is not self._lottie:
            return
        self.texture = provider._texture
        self.duration = provider._duration
        self.total_frames = provider._total_frames
        self.loaded = True
        # on_state fired when state was set but _lottie was None at that point,
        # so playback was not started.  Re-apply the current state now that the
        # provider is ready.
        self.on_state(self, self.state)
        self.dispatch('on_load')

    def _on_provider_eos(self, provider, *largs):
        if provider is not self._lottie:
            return
        self.dispatch('on_eos')

    def _on_provider_frame(self, provider, *largs):
        if provider is not self._lottie:
            return
        self.texture = provider._texture
        # The texture pixels are updated in-place via blit_buffer every frame,
        # so the object reference never changes after the first render.  Kivy's
        # property binding therefore never fires after frame 1.  Ask the canvas
        # to redraw explicitly - same approach as kivy.uix.video.Video.
        self.canvas.ask_update()
        # Mirror the provider's current position back onto the widget property
        # so that derived properties (progress, on_position bindings, KV rules)
        # reflect playback.  The _updating_position flag stops _on_position_prop
        # from treating this as a user seek request.
        self._updating_position = True
        self.position = provider._position
        self._updating_position = False

    def _on_texture(self, instance, texture):
        self.texture_size = list(texture.size) if texture else [0, 0]

    def on_state(self, instance, value):
        '''Kivy property event - sync the provider whenever ``state`` changes.'''
        if self._lottie is None:
            return
        if value == 'play':
            self._lottie.play()
        elif value == 'pause':
            self._lottie.pause()
        else:
            self._lottie.stop()

    def _on_position_prop(self, instance, value):
        '''Seek when ``position`` property is changed externally.'''
        # Ignore updates that originate from _on_provider_frame mirroring the
        # provider's position back onto the widget - those are read-backs, not
        # user seek requests.
        if self._updating_position:
            return
        if self._lottie is None or self._lottie._duration <= 0:
            return
        pct = max(0.0, min(1.0, value / self._lottie._duration))
        self._lottie.seek(pct)

    def _on_eos_prop(self, instance, value):
        if self._lottie is not None:
            self._lottie.eos = value

    # ------------------------------------------------------------------
    # Playback control (public API)
    # ------------------------------------------------------------------

    def seek(self, percent):
        '''Seek to *percent* (0.0-1.0) through the animation.

        :param float percent: Position as a fraction of the total duration.
        '''
        if self._lottie is not None:
            self._lottie.seek(float(percent))
        if self._lottie is not None and self._lottie._duration > 0:
            self.position = float(percent) * self._lottie._duration

    # ------------------------------------------------------------------
    # Event handlers (defaults)
    # ------------------------------------------------------------------

    def on_load(self, *args):
        pass

    def on_eos(self, *args):
        pass

    def on_frame(self, *args):
        pass

    def on_error(self, error, *args):
        pass

    # ------------------------------------------------------------------
    # Segments and markers
    # ------------------------------------------------------------------

    @property
    def markers(self):
        '''List of marker names in the loaded animation.

        :rtype: list[str]
        '''
        if self._lottie is None:
            return []
        return self._lottie.markers

    def play_segment(self, begin, end):
        '''Restrict playback to the frame range [*begin*, *end*].

        After the call, :attr:`duration`, :attr:`total_frames`, and
        :attr:`position` are updated to reflect the new segment so that
        progress reporting and EOS detection remain accurate.

        :param float begin: First frame (inclusive).
        :param float end: Last frame (inclusive).
        '''
        if self._lottie is None:
            return
        self._lottie.play_segment(begin, end)
        self._sync_segment_props()

    def play_marker(self, name):
        '''Restrict playback to the named marker range.

        After the call, :attr:`duration`, :attr:`total_frames`, and
        :attr:`position` are updated to reflect the marker's frame range so
        that progress reporting and EOS detection remain accurate.

        :param str name: Marker name (see :attr:`markers`).
        :raises ValueError: If the marker does not exist.
        '''
        if self._lottie is None:
            return
        self._lottie.play_marker(name)
        self._sync_segment_props()

    def _sync_segment_props(self):
        '''Pull duration/total_frames/position from the provider after a
        segment or marker change and update the corresponding widget
        properties so that EOS detection, progress, and UI bindings stay
        consistent with the new playback range.
        '''
        p = self._lottie
        if p is None:
            return
        self.duration = p._duration
        self.total_frames = p._total_frames
        self.position = p._position

    # ------------------------------------------------------------------
    # Slot overrides
    # ------------------------------------------------------------------

    @property
    def slots(self):
        '''Frozenset of slot IDs in the loaded animation.

        :rtype: frozenset[str]
        '''
        if self._lottie is None:
            return frozenset()
        return self._lottie.slots

    def has_slot(self, slot_id):
        '''Return ``True`` if *slot_id* is present in the loaded animation.

        :param str slot_id: Slot ID to check.
        :rtype: bool
        '''
        if self._lottie is None:
            return False
        return self._lottie.has_slot(slot_id)

    def apply_slot(self, slot_data):
        '''Apply a raw slot override from a JSON string and return the slot handle.

        Prefer the typed helpers (:meth:`set_color`, :meth:`set_opacity`,
        :meth:`set_text`, :meth:`set_image`) for common cases.  Use this
        method when you need to apply a slot structure that the helpers do
        not cover.

        :param str slot_data: Slot override as a JSON string.
        :returns: Slot handle (pass to :meth:`reset_slot` to remove), or
            ``None`` on failure or when no animation is loaded.
        :rtype: int or None
        '''
        if self._lottie is None:
            return None
        return self._lottie.apply_slot(slot_data)

    def reset_slot(self, slot_id=None):
        '''Remove a slot override or clear all overrides.

        :param slot_id: Slot ID string, or ``None`` to clear all.
        :type slot_id: str or None
        '''
        if self._lottie is not None:
            self._lottie.reset_slot(slot_id)

    def set_color(self, slot_id, color):
        '''Override the fill colour of a slot.

        :param str slot_id: Slot ID.
        :param color: ``(r, g, b)`` or ``(r, g, b, a)`` floats 0.0-1.0.
        :returns: Slot handle or ``None``.
        :rtype: int or None
        '''
        if self._lottie is None:
            return None
        return self._lottie.set_color(slot_id, color)

    def set_opacity(self, slot_id, opacity):
        '''Override the opacity of a slot.

        :param str slot_id: Slot ID.
        :param float opacity: 0.0 (transparent) - 1.0 (opaque).
        :returns: Slot handle or ``None``.
        :rtype: int or None
        '''
        if self._lottie is None:
            return None
        return self._lottie.set_opacity(slot_id, opacity)

    def set_text(self, slot_id, text):
        '''Override the text content of a text slot.

        :param str slot_id: Slot ID.
        :param str text: New text string.
        :returns: Slot handle or ``None``.
        :rtype: int or None
        '''
        if self._lottie is None:
            return None
        return self._lottie.set_text(slot_id, text)

    def set_image(self, slot_id, source):
        '''Override the image of an image slot.

        :param str slot_id: Slot ID.
        :param str source: Absolute path to the replacement image.
        :returns: Slot handle or ``None``.
        :rtype: int or None
        '''
        if self._lottie is None:
            return None
        return self._lottie.set_image(slot_id, source)

    # ------------------------------------------------------------------
    # Rendering quality
    # ------------------------------------------------------------------

    def set_quality(self, value):
        '''Set the rendering quality level (0-100).

        :param int value: 0 = fastest, 100 = best.
        '''
        if self._lottie is not None:
            self._lottie.set_quality(value)

    def refresh(self):
        '''Force an immediate re-render of the current frame.'''
        if self._lottie is not None:
            self._lottie.refresh()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _clear(self):
        if self._lottie is not None:
            self._lottie.unbind(
                on_load=self._on_provider_load,
                on_eos=self._on_provider_eos,
                on_frame=self._on_provider_frame,
            )
            self._lottie.unload()
            self._lottie = None
        self.texture = None
        self.duration = 0.0
        self.total_frames = 0.0
        self.loaded = False
        self.state = 'stop'
        self.position = 0.0

    def _set_error(self, msg):
        self.loaded = False
        self.dispatch('on_error', msg)
