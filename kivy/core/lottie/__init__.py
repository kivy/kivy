'''
Lottie
======

Core provider layer for Lottie animations (.json).  This module is an
**implementation detail** - applications should use
:class:`~kivy.uix.lottie.LottieWidget` instead::

    from kivy.uix.lottie import LottieWidget

    anim = LottieWidget(source='animation.json', state='play')

This module is relevant if you are:

- writing a custom Lottie provider (subclass :class:`LottieBase`), or
- accessing the provider directly for headless / off-screen rendering.

Lottie is a JSON-based animation format produced by tools such as Adobe
After Effects (via the Bodymovin plug-in) and LottieFiles.  Unlike a video
file the animation data is vector-based and resolution-independent; the
provider rasterizes each frame on-the-fly to whatever pixel size you
request.

Provider selection
------------------

Kivy tries each registered provider in priority order and uses the first
one that loads successfully.  The only built-in provider is
``thorvg`` (backed by Kivy's internal :mod:`kivy.lib.thorvg` binding).
If no provider succeeds the ``null`` provider is used as a last resort
(it renders nothing but allows code that depends on a ``Lottie`` object
to still import and run).

DOM manipulation API
--------------------

The Lottie provider exposes a tiered API for runtime animation customisation:

**Tier 1 - Segments and markers** (playback range control):
  - :attr:`markers` - list of marker names in the file
  - :meth:`play_segment` - restrict playback to a frame range
  - :meth:`play_marker` - restrict playback to a named marker range

**Tier 2 - Slots** (dynamic property overrides via Lottie ``sid``):
  - :attr:`slots` - frozenset of slot IDs found in the file
  - :meth:`has_slot` - check whether a slot ID exists
  - :meth:`apply_slot` - apply a raw slot override JSON; returns the slot handle
  - :meth:`reset_slot` - remove a specific slot override or all overrides
  - Convenience: :meth:`set_color`, :meth:`set_opacity`, :meth:`set_text`,
    :meth:`set_image`

**Tier 3 - Rendering quality**:
  - :meth:`set_quality`

**Capability flags** (class-level, provider-specific):
  - :attr:`SUPPORTS_SLOTS`
  - :attr:`SUPPORTS_QUALITY`

.. versionadded:: 3.0.0
'''

__all__ = ('LottieBase', 'Lottie')

import json

from kivy.clock import Clock
from kivy.core import core_select_lib, get_provider_modules, make_provider_tuple
from kivy.event import EventDispatcher


class LottieBase(EventDispatcher):
    '''Abstract base class for Lottie animation providers.

    Concrete providers must subclass this and implement :meth:`load`,
    :meth:`unload`, and :meth:`_render_frame`.

    :Parameters:
        `filename`: str
            Path to the Lottie JSON file.
        `eos`: str, defaults to ``'loop'``
            Behaviour when the animation reaches its end.  One of:

            * ``'loop'``  - restart from frame 0.
            * ``'stop'``  - halt and rewind to frame 0.
            * ``'pause'`` - halt and remain on the last frame (``state``
              becomes ``'paused'``).

        `size`: tuple ``(int, int)``, defaults to ``(512, 512)``
            Rasterization size in pixels ``(width, height)``.  Providers
            may override this with the animation's native size when the
            caller passes ``None``.

    :Events:
        `on_eos`
            Fired when the animation reaches its end (before the
            ``eos`` action is taken).
        `on_load`
            Fired once the animation file has been loaded and the initial
            texture is ready.
        `on_frame`
            Fired every time a new frame has been written to the texture.
    '''

    # ------------------------------------------------------------------
    # Capability flags - overridden to True by providers that implement
    # the corresponding API tier.
    # ------------------------------------------------------------------

    SUPPORTS_SLOTS = False
    '''True when this provider supports Tier 2 slot overrides (:meth:`apply_slot`).

    File-level capability (whether the loaded file actually *has* any slots)
    is checked via :attr:`slots`.
    '''

    SUPPORTS_QUALITY = False
    '''True when this provider supports the :meth:`set_quality` hint.'''

    __events__ = ('on_eos', 'on_load', 'on_frame')

    def __init__(self, **kwargs):
        kwargs.setdefault('filename', None)
        kwargs.setdefault('eos', 'loop')
        kwargs.setdefault('size', (512, 512))

        super().__init__()

        self._filename = None
        self._texture = None
        self._state = ''
        self._position = 0.0
        self._duration = 0.0
        self._total_frames = 0.0
        self._render_size = kwargs.get('size')
        self._eos = kwargs.get('eos')
        self._clock_event = None

        self.filename = kwargs.get('filename')

    def __del__(self):
        self.unload()

    # ------------------------------------------------------------------
    # Default event handlers (no-ops; subclasses / callers can override)
    # ------------------------------------------------------------------

    def on_eos(self):
        pass

    def on_load(self):
        pass

    def on_frame(self):
        pass

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    def _get_filename(self):
        return self._filename

    def _set_filename(self, filename):
        if filename == self._filename:
            return
        self.unload()
        self._filename = filename
        if self._filename is None:
            return
        self.load()

    filename = property(
        lambda self: self._get_filename(),
        lambda self, x: self._set_filename(x),
        doc='Get/set the path of the Lottie JSON file.',
    )

    def _get_position(self):
        return self._position

    def _set_position(self, seconds):
        if self._duration > 0:
            self.seek(seconds / self._duration)

    position = property(
        lambda self: self._get_position(),
        lambda self, x: self._set_position(x),
        doc='Get/set the playback position in seconds.',
    )

    def _get_duration(self):
        return self._duration

    duration = property(
        lambda self: self._get_duration(),
        doc='Animation duration in seconds (read-only after load).',
    )

    def _get_total_frames(self):
        return self._total_frames

    total_frames = property(
        lambda self: self._get_total_frames(),
        doc='Total number of frames in the animation (read-only after load).',
    )

    def _get_texture(self):
        return self._texture

    texture = property(
        lambda self: self._get_texture(),
        doc='Current animation texture (read-only; updated on each frame).',
    )

    def _get_state(self):
        return self._state

    state = property(
        lambda self: self._get_state(),
        doc="Playback state: ``'playing'``, ``'paused'``, or ``''``.",
    )

    def _get_eos(self):
        return self._eos

    def _set_eos(self, value):
        if value not in ('loop', 'stop', 'pause'):
            raise ValueError(
                f"eos must be 'loop', 'stop', or 'pause', got {value!r}")
        self._eos = value

    eos = property(
        lambda self: self._get_eos(),
        lambda self, x: self._set_eos(x),
        doc="End-of-animation behaviour: ``'loop'``, ``'stop'``, or ``'pause'``.",
    )

    # ------------------------------------------------------------------
    # EOS
    # ------------------------------------------------------------------

    def _do_eos(self):
        self.dispatch('on_eos')
        if self._eos == 'loop':
            self._position = 0.0
            frame = 0.0
            self._render_frame(frame)
        elif self._eos == 'stop':
            self.stop()
        elif self._eos == 'pause':
            self._position = self._duration
            self.pause()

    # ------------------------------------------------------------------
    # Clock-driven update
    # ------------------------------------------------------------------

    def _update(self, dt):
        if self._state != 'playing' or self._duration <= 0:
            return

        self._position += dt

        if self._position >= self._duration:
            self._do_eos()
            return

        frame = (self._position / self._duration) * self._total_frames
        self._render_frame(frame)

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------

    def _render_frame(self, frame):
        '''Render *frame* (float, 0 to total_frames) to ``self._texture``.

        Concrete providers must override this method.  After rendering,
        they should call ``self.dispatch('on_frame')``.
        '''
        pass

    def _refresh(self):
        '''Re-render the current frame without advancing the clock.

        Computes the frame number from the current :attr:`position` and
        calls :meth:`_render_frame`.  Use this after any DOM mutation
        (slot override, expression variable change, etc.) to update the
        texture without waiting for the next clock tick.
        '''
        if self._duration <= 0 or self._total_frames <= 0:
            return
        frame = (self._position / self._duration) * self._total_frames
        self._render_frame(frame)

    def refresh(self):
        '''Public alias for :meth:`_refresh`.

        Forces an immediate re-render of the current frame.  Useful
        after external DOM mutations that bypass the normal property
        setters.
        '''
        self._refresh()

    # ------------------------------------------------------------------
    # Playback control
    # ------------------------------------------------------------------

    def seek(self, percent, precise=True):
        '''Seek to *percent* (0.0-1.0) through the animation.

        The ``precise`` parameter is accepted for API compatibility with
        :class:`~kivy.core.video.VideoBase` but is not used; Lottie
        rendering is always frame-accurate.
        '''
        percent = max(0.0, min(1.0, float(percent)))
        self._position = percent * self._duration
        frame = percent * self._total_frames
        self._render_frame(frame)

    def play(self):
        '''Start or resume playing the animation.'''
        if self._state == 'playing':
            return
        self._state = 'playing'
        if self._clock_event is None and self._filename is not None:
            self._clock_event = Clock.schedule_interval(self._update, 0)

    def pause(self):
        '''Pause the animation at the current position.'''
        if self._state != 'playing':
            return
        self._state = 'paused'
        if self._clock_event is not None:
            self._clock_event.cancel()
            self._clock_event = None

    def stop(self):
        '''Stop playback and reset to the beginning.'''
        self._state = ''
        self._position = 0.0
        if self._clock_event is not None:
            self._clock_event.cancel()
            self._clock_event = None
        # Rewind time without drawing would leave the last frame in the texture;
        # refresh so frame 0 matches ``_position`` (EOS ``'stop'``, initial
        # ``state: 'stop'``, etc.).
        self._refresh()

    # ------------------------------------------------------------------
    # Load / unload
    # ------------------------------------------------------------------

    def load(self):
        '''Load the animation from :attr:`filename`.

        Concrete providers must override this method.  On success they
        should populate ``_duration``, ``_total_frames``, and
        ``_texture``, then call ``self.dispatch('on_load')``.
        '''
        pass

    def unload(self):
        '''Unload the animation and release all resources.'''
        self.stop()
        self._texture = None
        self._duration = 0.0
        self._total_frames = 0.0

    # ------------------------------------------------------------------
    # Tier 1: Segments and markers
    # ------------------------------------------------------------------

    @property
    def markers(self):
        '''List of marker names defined in the loaded Lottie file.

        Returns an empty list if the file has not been loaded or no
        markers are defined.

        :rtype: list[str]
        '''
        return []

    def play_segment(self, begin, end):
        '''Restrict playback to the frame range [*begin*, *end*].

        After calling this method the :attr:`total_frames` and
        :attr:`duration` are remapped to cover only the specified segment,
        so existing clock-driven playback and :meth:`seek` continue to
        work without modification.

        Pass ``begin=0`` and ``end=total_frames`` to reset to the full
        animation.

        :param float begin: First frame of the segment (inclusive).
        :param float end: Last frame of the segment (inclusive).
        '''
        pass

    def play_marker(self, name):
        '''Restrict playback to the named marker range.

        Convenience wrapper around :meth:`play_segment` that looks up the
        frame range of the named marker.

        :param str name: Marker name as returned by :attr:`markers`.
        :raises ValueError: If *name* is not found in :attr:`markers`.
        '''
        pass


    # ------------------------------------------------------------------
    # Tier 2: Slots
    # ------------------------------------------------------------------

    @property
    def slots(self):
        '''Frozenset of slot IDs (``sid`` values) found in the loaded file.

        Empty if the file has not been loaded or has no slots.

        :rtype: frozenset[str]
        '''
        return frozenset()

    def has_slot(self, slot_id):
        '''Return ``True`` if *slot_id* is present in the loaded file.

        This is a concrete convenience method based on :attr:`slots`.

        :param str slot_id: The slot ID to check.
        :rtype: bool
        '''
        return slot_id in self.slots

    def apply_slot(self, slot_data):
        '''Apply a raw slot override and return the slot handle.

        *slot_data* must be a JSON string mapping slot IDs to property
        values in Lottie slot format::

            '{"sid": {"p": {"a": 0, "k": value}}}'

        where *sid* is the slot ID, ``"p"`` is the property, ``"a"`` is
        0 for a static (non-animated) value, and ``"k"`` is the new value.

        Returns an integer slot handle (> 0) on success, or ``None`` if
        the provider does not support slots or the JSON is invalid.

        :param str slot_data: Slot override as a JSON string.
        :rtype: int or None
        '''
        return None

    def reset_slot(self, slot_id=None):
        '''Remove a slot override or clear all overrides.

        If *slot_id* is given, only the override for that slot is removed.
        If *slot_id* is ``None``, all active slot overrides are removed.

        :param slot_id: Slot ID string, or ``None`` to clear all.
        :type slot_id: str or None
        '''
        pass

    # ------------------------------------------------------------------
    # Tier 2: Convenience slot setters
    # ------------------------------------------------------------------

    def set_color(self, slot_id, color):
        '''Override the fill colour of a slot.

        Constructs a slot override JSON for a static colour and calls
        :meth:`apply_slot`.

        :param str slot_id: The slot ID (``sid`` value in the Lottie JSON).
        :param color: ``(r, g, b)`` or ``(r, g, b, a)`` floats 0.0-1.0.
            Per the Lottie spec the alpha component, if provided, is stored
            in the slot data but may be ignored by some renderers.
        :type color: tuple or list
        :returns: Slot handle (int > 0) on success, ``None`` otherwise.
        :rtype: int or None
        '''
        r, g, b = float(color[0]), float(color[1]), float(color[2])
        slot_json = json.dumps(
            {slot_id: {'p': {'a': 0, 'k': [r, g, b]}}}
        )
        return self.apply_slot(slot_json)

    def set_opacity(self, slot_id, opacity):
        '''Override the opacity of a slot.

        :param str slot_id: The slot ID.
        :param float opacity: Opacity value 0.0 (transparent) - 1.0 (opaque).
            Converted to a Lottie 0-100 range internally.
        :returns: Slot handle (int > 0) on success, ``None`` otherwise.
        :rtype: int or None
        '''
        value = max(0.0, min(100.0, float(opacity) * 100.0))
        slot_json = json.dumps(
            {slot_id: {'p': {'a': 0, 'k': value}}}
        )
        return self.apply_slot(slot_json)

    def set_text(self, slot_id, text):
        '''Override the text content of a text slot.

        The slot must reference a Lottie text layer.  The value is passed
        as a plain string; ThorVG will apply it to the text document.

        :param str slot_id: The slot ID.
        :param str text: New text string.
        :returns: Slot handle (int > 0) on success, ``None`` otherwise.
        :rtype: int or None
        '''
        slot_json = json.dumps(
            {slot_id: {'p': {'a': 0, 'k': str(text)}}}
        )
        return self.apply_slot(slot_json)

    def set_image(self, slot_id, source):
        '''Override the image source of an image slot.

        The slot must reference a Lottie image layer.  *source* should be
        an absolute file path to the replacement image.

        :param str slot_id: The slot ID.
        :param str source: Absolute file path of the replacement image.
        :returns: Slot handle (int > 0) on success, ``None`` otherwise.
        :rtype: int or None
        '''
        slot_json = json.dumps(
            {slot_id: {'p': {'a': 0, 'k': str(source)}}}
        )
        return self.apply_slot(slot_json)

    # ------------------------------------------------------------------
    # Tier 3: Rendering quality
    # ------------------------------------------------------------------

    def set_quality(self, value):
        '''Set the rendering quality level for Lottie effects.

        Controls how accurately blur, drop-shadow, and similar effects are
        rendered.  Lower values favour performance; higher values favour
        quality.

        :param int value: Quality level 0-100 (0 = fastest, 100 = best).
            Default is 50.
        '''
        pass


# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------

all_providers = get_provider_modules('lottie')
lottie_providers = [
    make_provider_tuple('thorvg', all_providers, 'LottieThorvg'),
    make_provider_tuple('null',   all_providers, 'LottieNull'),
]

Lottie: LottieBase = core_select_lib('lottie', lottie_providers)
