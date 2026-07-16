'''
ThorVG Lottie provider
======================

Rasterizes Lottie animations to a Kivy :class:`~kivy.graphics.texture.Texture`
using Kivy's internal ThorVG binding (:mod:`kivy.lib.thorvg`) and its
software renderer.

No external installation is required: the ThorVG library and its Cython
wrapper ship with Kivy and are compiled into the binary wheels.  If this
build of Kivy was compiled without ThorVG support, the
``import kivy.lib.thorvg`` below raises ``ImportError`` and this provider
is skipped; Kivy will fall back to the next provider in the priority list
(ultimately the ``null`` provider).

Rasterization size
------------------

The default render size is 512 x 512 pixels.  You can override it globally
via the ``[lottie] default_size`` Kivy config key::

    # ~/.kivy/config.ini
    [lottie]
    default_size = 256

or per-widget via the ``render_size`` keyword argument on
:class:`~kivy.uix.lottie.LottieWidget`::

    LottieWidget(source='animation.json', render_size=(256, 256))

When ``render_size`` is ``None`` the provider uses the Lottie composition's
native size, scaled up if its shortest axis is below ``default_size``.

Colorspace note
---------------

ThorVG's default colorspace is ``ABGR8888``.  On all little-endian platforms
supported by Kivy (x86-64, ARM64) the byte layout in memory is R, G, B, A -
exactly Kivy's ``'rgba'`` format - so no channel swapping is needed.

.. versionadded:: 3.0.0
'''

__all__ = ('LottieThorvg',)

import json

try:
    from kivy.lib import thorvg as tvg
    from kivy.lib.thorvg import Result
except ImportError:
    raise

from kivy.config import Config
from kivy.core.lottie import LottieBase
from kivy.graphics.texture import Texture
from kivy.logger import Logger
from kivy.resources import resource_find

Logger.info(
    'LottieThorvg: Using kivy.lib.thorvg (ThorVG {})'.format(
        tvg.engine_version()))

_DEFAULT_SIZE = 512


def _resolve_render_size(picture, render_size):
    '''Return the ``(w, h)`` pixel dimensions to rasterize at.

    *render_size* (from the ``size`` kwarg) is used as a **minimum floor**
    when provided.  When ``None``, ``[lottie] default_size`` (or the module
    default of 512) is used as the floor.  The Lottie composition's native
    size is used when it already exceeds the floor; otherwise the frame is
    scaled up while preserving the aspect ratio.
    '''
    if render_size is not None:
        floor = max(int(render_size[0]), int(render_size[1]))
    else:
        floor = Config.getdefaultint('lottie', 'default_size', _DEFAULT_SIZE)

    result, native_w, native_h = picture.get_size()
    if result != Result.SUCCESS or native_w <= 0 or native_h <= 0:
        return floor, floor

    if native_w >= floor and native_h >= floor:
        return int(native_w), int(native_h)

    scale = max(floor / native_w, floor / native_h)
    return int(native_w * scale), int(native_h * scale)


def _marker_names_from_animation(anim):
    '''Return an ordered list of marker names from the loaded animation.

    Uses ``get_markers_cnt`` and ``get_marker`` on the
    :class:`kivy.lib.thorvg.LottieAnimation` instance.
    '''
    names = []
    r, cnt = anim.get_markers_cnt()
    if r not in (Result.SUCCESS, Result.INSUFFICIENT_CONDITION):
        Logger.warning(f'LottieThorvg: get_markers_cnt failed: {r}')
        return names
    n = int(cnt)
    if n <= 0:
        return names
    for i in range(n):
        r, name = anim.get_marker(i)
        if r not in (Result.SUCCESS, Result.INSUFFICIENT_CONDITION):
            Logger.warning(f'LottieThorvg: get_marker({i}) failed: {r}')
            continue
        if isinstance(name, str) and name:
            names.append(name)
    return names


def _collect_slot_ids(lottie_bytes):
    '''Scan Lottie JSON bytes for all ``"sid"`` values.

    The ``"sid"`` key appears on individual animated properties (e.g. fill
    color, opacity) and marks them as overridable at runtime via the slot API.
    This helper does a shallow scan without full JSON parsing so it is fast
    even on large files.

    :param bytes lottie_bytes: Raw Lottie JSON file contents.
    :rtype: frozenset[str]
    '''
    try:
        data = json.loads(lottie_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        Logger.warning(f'LottieThorvg: failed to parse JSON for slot scan: {exc}')
        return frozenset()

    ids = set()

    def _walk(obj):
        if isinstance(obj, dict):
            if 'sid' in obj:
                sid = obj['sid']
                if isinstance(sid, str) and sid:
                    ids.add(sid)
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(data)
    return frozenset(ids)


class LottieThorvg(LottieBase):
    '''Lottie animation provider backed by :mod:`kivy.lib.thorvg`.

    This class keeps a ThorVG :class:`~kivy.lib.thorvg.SwCanvas` and
    :class:`~kivy.lib.thorvg.LottieAnimation` alive for the lifetime of the
    loaded animation so that :meth:`_render_frame` can rasterize individual
    frames efficiently without re-creating those objects on every tick.

    Requires Kivy to be built with ThorVG support (the default for the
    official wheels on desktop platforms).
    '''

    SUPPORTS_SLOTS = True
    SUPPORTS_QUALITY = True

    def __init__(self, **kwargs):
        self._tvg_canvas = None
        self._tvg_anim = None
        self._render_w = 0
        self._render_h = 0
        self._composition_total_frames = None  # full comp; preserved when markers run
        self._slot_ids = frozenset()
        self._marker_names = []   # ordered list from LottieAnimation API
        self._active_slots = {}   # slot_id str -> ThorVG slot handle int
        super().__init__(**kwargs)

    # ------------------------------------------------------------------
    # Load / unload
    # ------------------------------------------------------------------

    def load(self):
        self._teardown()

        path = resource_find(self._filename) or self._filename
        if path is None:
            Logger.warning(f'LottieThorvg: file not found <{self._filename}>')
            return

        # Failure path: any error below falls through to the ``except`` at the
        # bottom which re-runs ``_teardown()``. The ``canvas`` and ``anim``
        # locals are owned by this function until we assign them to
        # ``self`` (last step before dispatching ``on_load``), so if we
        # return early their reference count drops to zero and their
        # ``__dealloc__`` tears ThorVG down cleanly - no explicit
        # ``canvas.destroy()`` / ``engine.term()`` needed.
        try:
            canvas = tvg.SwCanvas()
            anim = tvg.LottieAnimation()
            picture = anim.get_picture()

            result = picture.load(path)
            if result != Result.SUCCESS:
                Logger.warning(
                    f'LottieThorvg: Picture.load failed <{path}>: {result}')
                return

            # Resolve animation metadata.
            res_dur,    duration     = anim.get_duration()
            res_frames, total_frames = anim.get_total_frame()
            if res_dur != Result.SUCCESS or res_frames != Result.SUCCESS:
                Logger.warning(
                    f'LottieThorvg: could not read metadata <{path}>')
                return

            if duration <= 0 or total_frames <= 0:
                Logger.warning(
                    f'LottieThorvg: animation has zero duration or frames '
                    f'<{path}> (duration={duration}, frames={total_frames})')
                return

            # Resolve rasterization size.
            w, h = _resolve_render_size(picture, self._render_size)

            # Size the picture to the raster target.
            result = picture.set_size(float(w), float(h))
            if result != Result.SUCCESS:
                Logger.warning(
                    f'LottieThorvg: Picture.set_size failed <{path}>: {result}')
                return

            # Allocate the SwCanvas pixel buffer.
            result = canvas.set_target(w, h)
            if result != Result.SUCCESS:
                Logger.warning(
                    f'LottieThorvg: SwCanvas.set_target failed <{path}>: {result}')
                return

            # Add the picture to the canvas scene (once; reused every frame).
            result = canvas.add(picture)
            if result != Result.SUCCESS:
                Logger.warning(
                    f'LottieThorvg: canvas.add failed <{path}>: {result}')
                return

            # Slot IDs still require a JSON scan (no ThorVG enumeration API).
            try:
                with open(path, 'rb') as fh:
                    lottie_bytes = fh.read()
                self._slot_ids = _collect_slot_ids(lottie_bytes)
            except OSError:
                self._slot_ids = frozenset()

            self._marker_names = _marker_names_from_animation(anim)

            self._tvg_canvas = canvas
            self._tvg_anim   = anim
            self._render_w   = w
            self._render_h   = h
            self._duration     = duration
            self._total_frames = total_frames
            self._composition_total_frames = float(total_frames)
            self._position     = 0.0

            # Texture is created lazily in _render_frame() so that load()
            # can succeed in headless / unit-test environments without a
            # GL context.  The first render happens when play() starts the
            # Clock or when refresh() is called explicitly.
            self.dispatch('on_load')

            Logger.info(
                f'LottieThorvg: loaded <{path}> '
                f'{w}x{h}px  {total_frames:.0f} frames  {duration:.3f}s  '
                f'slots={len(self._slot_ids)}')

        except Exception as e:
            Logger.warning(
                f'LottieThorvg: exception while loading <{path}>: {e}')
            self._teardown()

    def unload(self):
        super().unload()
        self._teardown()

    def _teardown(self):
        '''Release ThorVG objects and reset internal state.

        The SwCanvas and LottieAnimation own their native ThorVG handles
        and free them in ``__dealloc__``, so dropping the Python references
        is sufficient - there is no global engine term step to run. This
        matches the other ThorVG-backed providers (``svg_thorvg``,
        ``img_thorvg_svg``) and the :mod:`kivy.lib.thorvg` binding which
        initialises/terminates the ThorVG engine itself at module load /
        interpreter shutdown.
        '''
        self._tvg_canvas = None
        self._tvg_anim = None
        self._render_w = 0
        self._render_h = 0
        self._composition_total_frames = None
        self._slot_ids = frozenset()
        self._marker_names = []
        self._active_slots = {}

    # ------------------------------------------------------------------
    # Per-frame rendering
    # ------------------------------------------------------------------

    def _render_frame(self, frame):
        '''Rasterize *frame* (float) to ``self._texture`` via ThorVG.

        Must be called on the main thread (the Kivy Clock guarantees this for
        clock-driven playback; DOM mutation methods should also be called from
        the main thread since they update the OpenGL texture directly).

        The Kivy :class:`~kivy.graphics.texture.Texture` is created lazily
        on the first call so that :meth:`load` can complete without a GL
        context (e.g. in unit tests).
        '''
        if self._tvg_anim is None or self._tvg_canvas is None:
            return

        # Lazy texture creation: only allocate the GL texture on the first
        # actual render call, which happens inside a running Kivy app.
        if self._texture is None:
            self._texture = Texture.create(
                size=(self._render_w, self._render_h), colorfmt='rgba')
            self._texture.flip_vertical()

        result = self._tvg_anim.set_frame(float(frame))
        if result not in (Result.SUCCESS, Result.INSUFFICIENT_CONDITION):
            Logger.warning(
                f'LottieThorvg: set_frame({frame:.3f}) failed: {result}')
            return

        for op, args, name in (
            (self._tvg_canvas.update, (),       'update'),
            (self._tvg_canvas.draw,   (True,),  'draw'),
            (self._tvg_canvas.sync,   (),       'sync'),
        ):
            res = op(*args)
            if res not in (Result.SUCCESS, Result.INSUFFICIENT_CONDITION):
                Logger.warning(
                    f'LottieThorvg: canvas.{name} failed: {res}')
                return

        # Zero-copy upload: ``SwCanvas`` implements the Python buffer
        # protocol over ThorVG's own pixel buffer, and ``blit_buffer``
        # accepts any buffer-protocol object. Passing the canvas directly
        # skips the ``bytes(canvas.buffer_arr)`` copy that would otherwise
        # allocate ``w * h * 4`` bytes per frame (~1 MB at 512x512,
        # ~67 MB at 4K) on every tick of the Lottie clock.
        self._texture.blit_buffer(self._tvg_canvas, colorfmt='rgba')
        self.dispatch('on_frame')

    # ------------------------------------------------------------------
    # Tier 1: Segments and markers
    # ------------------------------------------------------------------

    @property
    def markers(self):
        '''List of marker names defined in the loaded Lottie file.

        Populated at load time via ``LottieAnimation.get_markers_cnt`` and
        ``get_marker(index)``.

        :rtype: list[str]
        '''
        return list(self._marker_names)

    def play_segment(self, begin, end):
        '''Restrict playback to the frame range [*begin*, *end*].

        :param float begin: First frame (inclusive).
        :param float end: Last frame (inclusive).
        '''
        if self._tvg_anim is None:
            return
        result = self._tvg_anim.set_segment(float(begin), float(end))
        if result not in (Result.SUCCESS, Result.INSUFFICIENT_CONDITION):
            Logger.warning(
                f'LottieThorvg: set_segment({begin}, {end}) failed: {result}')
            return
        self._sync_segment_metadata()
        self._refresh()

    def play_marker(self, name):
        '''Restrict playback to the named marker range.

        :param str name: Marker name.
        :raises ValueError: If *name* is not found.
        '''
        if self._tvg_anim is None:
            return
        # ThorVG can leave segment state inconsistent when switching from one
        # marker to another (or replaying a marker). Reset to the full
        # composition frame range before ``set_marker`` so each marker applies
        # from a clean timeline (same as calling ``play_segment(0, last)``).
        ct = self._composition_total_frames
        if ct is not None and ct > 0:
            last = max(0.0, ct - 1.0)
            r = self._tvg_anim.set_segment(0.0, last)
            if r not in (Result.SUCCESS, Result.INSUFFICIENT_CONDITION):
                Logger.warning(
                    f'LottieThorvg: set_segment(0, {last}) before marker failed: {r}')
            else:
                self._sync_segment_metadata()
        result = self._tvg_anim.set_marker(name)
        if result == Result.INVALID_ARGUMENT:
            raise ValueError(
                f'LottieThorvg: marker {name!r} not found in animation')
        if result not in (Result.SUCCESS, Result.INSUFFICIENT_CONDITION):
            Logger.warning(
                f'LottieThorvg: set_marker({name!r}) failed: {result}')
            return
        self._sync_segment_metadata()
        self._refresh()

    def _sync_segment_metadata(self):
        '''Re-query duration and total frames from ThorVG after a segment or
        marker change, then reset the playback position to the start of the
        new segment.

        ThorVG updates its reported duration and frame count whenever
        ``set_segment`` or ``set_marker`` is called, so re-querying here
        gives us the correct values for ``_update``'s frame computation.
        '''
        r_dur, duration = self._tvg_anim.get_duration()
        r_fr, total_frames = self._tvg_anim.get_total_frame()
        if r_dur == Result.SUCCESS and r_fr == Result.SUCCESS:
            self._duration = duration
            self._total_frames = total_frames
        self._position = 0.0

    # ------------------------------------------------------------------
    # Slot overrides
    # ------------------------------------------------------------------

    @property
    def slots(self):
        '''Frozenset of slot IDs found in the loaded file.

        :rtype: frozenset[str]
        '''
        return self._slot_ids

    def apply_slot(self, slot_data):
        '''Apply a raw ThorVG slot JSON and return the slot handle.

        :param str slot_data: ThorVG slot JSON.
        :returns: Slot handle (int > 0) or ``None`` on failure.
        :rtype: int or None
        '''
        if self._tvg_anim is None:
            return None
        slot_id = self._tvg_anim.gen_slot(slot_data)
        if not slot_id:
            Logger.warning(
                f'LottieThorvg: gen_slot failed for data: {slot_data[:80]!r}')
            return None
        result = self._tvg_anim.apply_slot(slot_id)
        if result not in (Result.SUCCESS, Result.INSUFFICIENT_CONDITION):
            Logger.warning(
                f'LottieThorvg: apply_slot({slot_id}) failed: {result}')
            self._tvg_anim.del_slot(slot_id)
            return None

        # Track the handle so reset_slot can clean up by slot_id string.
        try:
            parsed = json.loads(slot_data)
            for key in parsed:
                self._active_slots[key] = slot_id
        except (json.JSONDecodeError, TypeError):
            pass

        self._refresh()
        return slot_id

    def reset_slot(self, slot_id=None):
        '''Remove a specific slot override or clear all overrides.

        :param slot_id: Slot ID string, or ``None`` to clear all.
        :type slot_id: str or None
        '''
        if self._tvg_anim is None:
            return

        if slot_id is None:
            # Reset all: apply_slot(0) is the ThorVG convention for "clear all".
            result = self._tvg_anim.apply_slot(0)
            if result not in (Result.SUCCESS, Result.INSUFFICIENT_CONDITION):
                Logger.warning(
                    f'LottieThorvg: apply_slot(0) (reset all) failed: {result}')
            self._active_slots.clear()
        else:
            handle = self._active_slots.pop(slot_id, None)
            if handle is not None:
                result = self._tvg_anim.del_slot(handle)
                if result not in (Result.SUCCESS, Result.INSUFFICIENT_CONDITION):
                    Logger.warning(
                        f'LottieThorvg: del_slot({handle}) failed: {result}')

        self._refresh()

    # ------------------------------------------------------------------
    # Rendering quality
    # ------------------------------------------------------------------

    def set_quality(self, value):
        '''Set the rendering quality level (0-100).

        :param int value: Quality 0 (fastest) to 100 (best).
        '''
        if self._tvg_anim is None:
            return
        result = self._tvg_anim.set_quality(int(value))
        if result not in (Result.SUCCESS, Result.INSUFFICIENT_CONDITION):
            Logger.warning(
                f'LottieThorvg: set_quality({value}) failed: {result}')
            return
        self._refresh()
