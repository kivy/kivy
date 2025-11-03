"""
ScrollView
==========

.. versionadded:: 1.0.4

The :class:`ScrollView` widget provides a scrollable/pannable viewport that is
clipped at the scrollview's bounding box.

.. note::
    Use :class:`~kivy.uix.recycleview.RecycleView` for generating large
    numbers of widgets in order to display many data items.


Scrolling Behavior
------------------

The ScrollView accepts only one child and applies a viewport/window to
it according to the :attr:`~ScrollView.scroll_x` and
:attr:`~ScrollView.scroll_y` properties. Touches are analyzed to
determine if the user wants to scroll or control the child in some
other manner: you cannot do both at the same time. To determine if
interaction is a scrolling gesture, these properties are used:

    - :attr:`~ScrollView.scroll_distance`: the minimum distance to travel,
      defaults to 20 pixels.
    - :attr:`~ScrollView.scroll_timeout`: the maximum time period, defaults
      to 55 milliseconds.

If a touch travels :attr:`~ScrollView.scroll_distance` pixels within the
:attr:`~ScrollView.scroll_timeout` period, it is recognized as a scrolling
gesture and translation (scroll/pan) will begin. If the timeout occurs, the
touch down event is dispatched to the child instead (no translation).

The default value for those settings can be changed in the configuration file::

    [widgets]
    scroll_timeout = 250
    scroll_distance = 20

.. versionadded:: 1.1.1

    ScrollView now animates scrolling in Y when a mousewheel is used.


Limiting to the X or Y Axis
---------------------------

By default, the ScrollView allows scrolling along both the X and Y axes. You
can explicitly disable scrolling on an axis by setting the
:attr:`~ScrollView.do_scroll_x` or :attr:`~ScrollView.do_scroll_y` properties
to False.


Managing the Content Size and Position
--------------------------------------

The ScrollView manages the position of its children similarly to a
:class:`~kivy.uix.relativelayout.RelativeLayout` but does not use the
:attr:`~kivy.uix.widget.Widget.size_hint`. You must
carefully specify the :attr:`~kivy.uix.widget.Widget.size` of your content to
get the desired scroll/pan effect.

By default, the :attr:`~kivy.uix.widget.Widget.size_hint` is (1, 1), so the
content size will fit your ScrollView
exactly (you will have nothing to scroll). You must deactivate at least one of
the size_hint instructions (x or y) of the child to enable scrolling.
Setting :attr:`~kivy.uix.widget.Widget.size_hint_min` to not be None will
also enable scrolling for that dimension when the :class:`ScrollView` is
smaller than the minimum size.

To scroll a :class:`~kivy.uix.gridlayout.GridLayout` on it's Y-axis/vertically,
set the child's width  to that of the ScrollView (size_hint_x=1), and set
the size_hint_y property to None::

    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.button import Button
    from kivy.uix.scrollview import ScrollView
    from kivy.core.window import Window
    from kivy.app import runTouchApp

    layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
    # Make sure the height is such that there is something to scroll.
    layout.bind(minimum_height=layout.setter('height'))
    for i in range(100):
        btn = Button(text=str(i), size_hint_y=None, height=40)
        layout.add_widget(btn)
    root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
    root.add_widget(layout)

    runTouchApp(root)


Kv Example::

    ScrollView:
        do_scroll_x: False
        do_scroll_y: True

        Label:
            size_hint_y: None
            height: self.texture_size[1]
            text_size: self.width, None
            padding: 10, 10
            text:
                'really some amazing text\\n' * 100

Overscroll Effects
------------------

.. versionadded:: 1.7.0

When scrolling would exceed the bounds of the :class:`ScrollView`, it
uses a :class:`~kivy.effects.scroll.ScrollEffect` to handle the
overscroll. These effects can perform actions like bouncing back,
changing opacity, or simply preventing scrolling beyond the normal
boundaries. Note that complex effects may perform many computations,
which can be slow on weaker hardware.

You can change what effect is being used by setting
:attr:`~ScrollView.effect_cls` to any effect class. Current options
include:

    - :class:`~kivy.effects.scroll.ScrollEffect`: Does not allow
      scrolling beyond the :class:`ScrollView` boundaries.
    - :class:`~kivy.effects.dampedscroll.DampedScrollEffect`: The
      current default. Allows the user to scroll beyond the normal
      boundaries, but has the content spring back once the
      touch/click is released.
    - :class:`~kivy.effects.opacityscroll.OpacityScrollEffect`: Similar
      to the :class:`~kivy.effect.dampedscroll.DampedScrollEffect`, but
      also reduces opacity during overscroll.

You can also create your own scroll effect by subclassing one of these,
then pass it as the :attr:`~ScrollView.effect_cls` in the same way.

Alternatively, you can set :attr:`~ScrollView.effect_x` and/or
:attr:`~ScrollView.effect_y` to an *instance* of the effect you want to
use. This will override the default effect set in
:attr:`~ScrollView.effect_cls`.

All the effects are located in the :mod:`kivy.effects`.

Nested ScrollViews
------------------
An application can have multiple levels of nested ScrollViews.  The
ScrollView class manages the hierarchy of nested ScrollViews.

It is important to set the :attr:`do_scroll_x` and :attr:`do_scroll_y`
properties to the correct values for the nested ScrollViews.
The nested scrolling behavior, described below, is only applied if the
:attr:`do_scroll_x` and :attr:`do_scroll_y` properties are set to the
appropriate values.

To achieve orthogonal scrolling, for example, the outer
ScrollView should have :attr:`do_scroll_x` set to False and the inner
ScrollView should have :attr:`do_scroll_y` set to True, or vice versa.

For Parallel scrolling, both ScrollViews should have the same value for
:attr:`do_scroll_x` and :attr:`do_scroll_y`.  This can allow vertical in
vertical,  horizontal in horizontal, or XY in XY scrolling.

For mixed scrolling, the outer ScrollView should have :attr:`do_scroll_x`
and :attr:`do_scroll_y` set to True, and the inner ScrollView should have
either :attr:`do_scroll_x` or :attr:`do_scroll_y` set to False.


**Orthogonal Scrolling** (outer and inner scroll in different directions):
    - Touch: Each ScrollView scrolls only in its direction
    - Wheel: Innermost ScrollView scrolls if it supports that axis
    - Example: Vertical outer + Horizontal inner

**Parallel Scrolling** (outer and inner scroll in the same direction):
    - Touch: Web-style boundary delegation (see below)
    - Wheel: Innermost ScrollView scrolls, no delegation to outer
    - Scrollbar: Scroll does not affect other ScrollView
    - Example: Vertical outer + Vertical inner

**Mixed Scrolling** (outer scrolls XY, inner one axis, or vice versa):
    - Shared axis: Web-style boundary delegation
    - Exclusive axes: Immediate delegation or inner-only scrolling
    - Wheel: Innermost ScrollView scrolls if it supports the axis
    - Example: XY outer + Horizontal inner


Web-Style Boundary Delegation
----------------------------

For parallel and shared-axis scrolling, ScrollView uses web-style
delegation:

    - If a touch starts at the inner boundary and moves out, it delegates
      scrolling to the outer ScrollView right away.
    - If a touch starts at the inner boundary and moves in, only the inner
      ScrollView scrolls.
    - If a touch starts not at a boundary, only the inner ScrollView
      scrolls, even if the gesture later reaches a boundary. Delegation to
      the outer never occurs mid-gesture in this case.
    - A new touch starting at the boundary is required to delegate to the
      outer.

Disable this behavior by setting :attr:`parallel_delegation` to False.

Wheel Behavior in Nested ScrollViews
------------------------------------

When the mouse scroll wheel or a trackpad is used, ScrollView always
applies web-style delegation:

  - Only the innermost ScrollView under the pointer/cursor will handle
    the wheel event.
  - If that ScrollView cannot scroll further along the wheel axis, the
    event is not propagated to outer ScrollViews. This matches standard
    browser and OS behavior.
  - Outer ScrollViews never respond to wheel events unless the pointer is
    over their scrollbars or unless there are no deeper nested
    ScrollViews.

This prevents "scroll hijacking" and provides an intuitive nested scroll
experience.

**Examples:**
  - In a vertical ScrollView containing a horizontal ScrollView, using the
    wheel over the horizontal ScrollView means only the vertical (outer)
    ScrollView scrolls, if its direction matches the wheel.
  - For two nested vertical ScrollViews, the innermost one under the
    pointer will scroll with the wheel until it cannot scroll further;
    wheel events are not delegated to the parent.

Wheel behavior is always active and is NOT affected by the
:attr:`parallel_delegation` or :attr:`delegate_to_outer` properties.
Those only control touch and touchpad gesture behavior.

    .. versionchanged:: VERSION_NEXT
    The ScrollView widgetnow supports nesting to arbitrary levels
    and configurations.
"""

__all__ = ("ScrollView",)

from functools import partial
from math import isclose
from enum import Enum

from kivy.animation import Animation
from kivy.config import Config
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.graphics import PushMatrix, Translate, PopMatrix, Canvas
from kivy.uix.stencilview import StencilView
from kivy.metrics import dp
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.properties import (
    NumericProperty,
    BooleanProperty,
    AliasProperty,
    ObjectProperty,
    ListProperty,
    ReferenceListProperty,
    OptionProperty,
    ColorProperty,
)
from kivy.uix.behaviors import FocusBehavior


# =============================================================================
# STATE MACHINE ENUMS
# =============================================================================


class ScrollMode(str, Enum):
    # Touch intent detection state machine.

    # Tracks whether a touch gesture is a tap/click or a scroll gesture
    # based on movement distance and timeout thresholds.

    # State Transition Diagram:
    #
    #                          movement > scroll_distance
    #                    ┌──────────────────────────────────┐
    #                    │                                  │
    #                    │                                  v
    #              ┌─────────┐                        ┌────────┐
    #              │ UNKNOWN │                        │ SCROLL │
    #              └─────────┘                        └────────┘
    #                    │                                 ^
    #                    │ timeout expires                 │
    #                    v                                 │
    #         try _simulate_touch_down()                   │
    #                    │                                 │
    #         ┌──────────┴──────────┐                      │
    #         │                     │                      │
    #    child grabbed         no child grabbed            │
    #         │                     │                      │
    #         v                     └──────────────────────┘
    #   hand off to child         transition to SCROLL mode
    #   (button, etc.)            (label, empty space, etc.)
    #
    # State Descriptions:
    # - UNKNOWN: Initial state, accumulating movement to detect intent
    # - SCROLL: Scroll gesture confirmed - either movement exceeded threshold
    #           OR timeout expired without child widget consuming the touch
    UNKNOWN = "unknown"  # Detecting intent - accumulating movement
    SCROLL = "scroll"  # Confirmed scroll gesture - movement exceeded threshold


class DelegationMode(str, Enum):
    # """Web-style boundary delegation state machine.

    # Controls when an inner ScrollView delegates scrolling to its outer
    # ScrollView in parallel nested configurations (both scrolling same axis).

    # State Descriptions:
    # - UNLOCKED: Normal scrolling, no delegation. Inner scrolls freely.
    # - START_AT_BOUNDARY: Touch began at inner's boundary.
    #                      Watching movement direction.
    # - LOCKED: Touch trying to scroll beyond boundary.
    #           Outer takes over, inner blocked.

    # State Transition Diagram:

    # Touch starts NOT at boundary:
    #     ┌──────────┐
    #     │ UNLOCKED │ (stays UNLOCKED entire gesture, inner scrolls freely)
    #     └──────────┘

    # Touch starts AT boundary:
    #     ┌──────────────────┐
    #     │ START_AT_BOUNDARY│─────┐
    #     └──────────────────┘     │
    #             │                │
    #             │                │
    #     move into content  scroll beyond boundary
    #             │                │
    #             v                v
    #     ┌──────────┐         ┌────────┐
    #     │ UNLOCKED │         │ LOCKED │ (stays LOCKED entire gesture)
    #     └──────────┘         └────────┘

    # Key: Once LOCKED, stays LOCKED until touch release (no transitions out)

    # Example (Vertical Parallel):
    # 1. User touches inner ScrollView at bottom (scroll_y = 1.0)
    #    -> START_AT_BOUNDARY
    # 2a. User drags down (into content) -> UNLOCKED (inner scrolls normally)
    # 2b. User drags up (beyond bottom edge) -> LOCKED (outer takes over)
    # 3. If LOCKED: stays LOCKED, outer handles all further movement

    UNLOCKED = "unlocked"  # Normal scrolling, no delegation active
    START_AT_BOUNDARY = "start_at_boundary"  # Touch began at scroll boundary
    LOCKED = "locked"  # At boundary trying to scroll beyond - delegate to outer


# =============================================================================
# HIERARCHY MANAGEMENT CLASS
# =============================================================================


class ScrollViewHierarchy:
    # INTERNAL CLASS - Manages the hierarchy of nested ScrollViews for a
    # touch gesture.
    #
    # Stores ScrollViews from outermost (index 0) to innermost (index n).
    # Each ScrollView can use its index to find its parent and navigate
    # the chain.
    #
    # Design Philosophy:
    # - ScrollViews are stored in a list
    #   (scrollviews[0] = outer, scrollviews[-1] = inner)
    # - Relationship data (classification, axis_config) stored separately
    # - Classifications describe relationships BETWEEN levels,
    #   not properties OF levels
    # - Index arithmetic is encapsulated in methods for safety
    #
    # Example for 3-level hierarchy (outer → middle → inner):
    #     scrollviews = [outer, middle, inner]
    #     _parent_child_data = [
    #         {classification: 'parallel', axis_config: None},  # outer→middle
    #         {classification: 'orthogonal', axis_config: None} # middle→inner
    #     ]

    def __init__(self, outer_sv):
        # Initialize hierarchy with the outermost ScrollView.
        # Args:
        #   outer_sv: The outermost ScrollView in the hierarchy
        self.scrollviews = [outer_sv]  # List from outer to inner
        self._parent_child_data = (
            []
        )  # Relationship data between adjacent levels
        self.touched_index = 0  # Index of ScrollView where touch started

    def add_child(self, child_sv, classification, axis_config=None):
        # Add a child ScrollView to the hierarchy.
        # Args:
        #   child_sv: The child ScrollView to add
        #   classification: 'orthogonal', 'parallel', or 'mixed'
        #   axis_config: Dict with axis configuration (only for mixed)
        self.scrollviews.append(child_sv)
        self._parent_child_data.append(
            {"classification": classification, "axis_config": axis_config}
        )
        self.touched_index = len(self.scrollviews) - 1

    def get_parent(self, current_index):
        # Get parent ScrollView for given index.
        # Args:
        #   current_index: Index of the child ScrollView
        # Returns:
        #   Parent ScrollView, or None if at root (index 0)
        if current_index > 0:
            return self.scrollviews[current_index - 1]
        return None

    def get_relationship(self, child_index):
        # Get relationship data between child at child_index and its parent.
        # Encapsulates the index arithmetic for accessing relationship data.
        # Args:
        #   child_index: Index of the child ScrollView
        # Returns:
        #   Dict with 'classification' and 'axis_config', or None if no parent
        if 0 < child_index < len(self.scrollviews):
            return self._parent_child_data[child_index - 1]
        return None

    def get_classification(self, child_index):
        # Get classification between child and its parent.
        # Args:
        #   child_index: Index of the child ScrollView
        # Returns:
        #   Classification string ('orthogonal', 'parallel', 'mixed'),
        #   or None if child_index is 0 (no parent)
        rel = self.get_relationship(child_index)
        return rel["classification"] if rel else None

    def get_axis_config(self, child_index):
        # Get axis configuration for mixed classification.
        # Args:
        #   child_index: Index of the child ScrollView
        # Returns:
        #   Axis config dict for mixed cases, or None
        rel = self.get_relationship(child_index)
        return rel["axis_config"] if rel else None

    @property
    def depth(self):
        # Total depth of hierarchy (number of levels).
        return len(self.scrollviews)

    @property
    def outer(self):
        # Outermost ScrollView (index 0).
        return self.scrollviews[0]

    @property
    def inner(self):
        # Innermost ScrollView (last in list).
        return self.scrollviews[-1]


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# Boundary threshold for web-style delegation
# (normalized scroll position 0.0 to 1.0)
# A ScrollView is considered "at boundary" if scroll position is
# within this threshold of the minimum (0.0) or maximum (1.0) position.
# Used for parallel nested scrolling to determine when to delegate
# to outer ScrollView.
# Note: Set to 15% to account for elastic overscroll bounce-back
_BOUNDARY_THRESHOLD = 0.15  # 15% from edge

# When we are generating documentation, Config doesn't exist
_scroll_timeout = _scroll_distance = 0
if Config:
    _scroll_timeout = Config.getint("widgets", "scroll_timeout")
    _scroll_distance = "{}sp".format(
        Config.getint("widgets", "scroll_distance")
    )


class ScrollView(StencilView):
    """ScrollView class. See module documentation for more information.

    :Events:
        `on_scroll_start`
            Dispatch when scrolling is detected.
        `on_scroll_move`
            Dispatched when scrolling continues.
            Fires continuously during scrolling.
        `on_scroll_stop`
            Dispatched when scrolling stops. Fires when velocity reaches zero
            and scroll position stabilizes for 3 consecutive frames.

    .. versionchanged:: VERSION_NEXT
        `on_scroll_start`, `on_scroll_move` and `on_scroll_stop` events are
        now dispatched for nested and non-nested ScrollViews. The behavior
        has been updated.  Previously these events mirrored the behavior of the
        on_touch_* methods.
        Now they fire when scrolling starts, continues and stops.

    .. versionchanged:: 1.9.0
        `on_scroll_start`, `on_scroll_move` and `on_scroll_stop` events are
        now dispatched when scrolling to handle nested ScrollViews.

    .. versionchanged:: 1.7.0
        `auto_scroll`, `scroll_friction`, `scroll_moves`, `scroll_stoptime' has
        been deprecated, use :attr:`effect_cls` instead.
    """

    scroll_distance = NumericProperty(_scroll_distance)
    """Distance to move before scrolling the :class:`ScrollView`, in pixels. As
    soon as the distance has been traveled, the :class:`ScrollView` will start
    to scroll, and no touch event will go to children.
    It is advisable that you base this value on the dpi of your target device's
    screen.

    :attr:`scroll_distance` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 20 (pixels), according to the default value in user
    configuration.
    """

    scroll_wheel_distance = NumericProperty("20sp")
    """Distance to move when scrolling with a mouse wheel.
    It is advisable that you base this value on the dpi of your target device's
    screen.

    .. versionadded:: 1.8.0

    :attr:`scroll_wheel_distance` is a
    :class:`~kivy.properties.NumericProperty` , defaults to 20 pixels.
    """

    scroll_timeout = NumericProperty(_scroll_timeout)
    """Timeout allowed to trigger the :attr:`scroll_distance`, in milliseconds.
    If the user has not moved :attr:`scroll_distance` within the timeout,
    the scrolling will be disabled, and the touch event will go to the
    children.

    :attr:`scroll_timeout` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 55 (milliseconds) according to the default value in user
    configuration.

    .. versionchanged:: 1.5.0
        Default value changed from 250 to 55.
    """

    scroll_x = NumericProperty(0.0)
    """X scrolling value, between 0 and 1. If 0, the content's left side will
    touch the left side of the ScrollView. If 1, the content's right side will
    touch the right side.

    This property is controlled by :class:`ScrollView` only if
    :attr:`do_scroll_x` is True.

    :attr:`scroll_x` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    """

    scroll_y = NumericProperty(1.0)
    """Y scrolling value, between 0 and 1. If 0, the content's bottom side will
    touch the bottom side of the ScrollView. If 1, the content's top side will
    touch the top side.

    This property is controlled by :class:`ScrollView` only if
    :attr:`do_scroll_y` is True.

    :attr:`scroll_y` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 1.
    """

    do_scroll_x = BooleanProperty(True)
    """Allow scroll on X axis.

    :attr:`do_scroll_x` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    """

    do_scroll_y = BooleanProperty(True)
    """Allow scroll on Y axis.

    :attr:`do_scroll_y` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    """

    def _get_do_scroll(self):
        return (self.do_scroll_x, self.do_scroll_y)

    def _set_do_scroll(self, value):
        if isinstance(value, (list, tuple)):
            self.do_scroll_x, self.do_scroll_y = value
        else:
            self.do_scroll_x = self.do_scroll_y = bool(value)

    do_scroll = AliasProperty(
        _get_do_scroll,
        _set_do_scroll,
        bind=("do_scroll_x", "do_scroll_y"),
        cache=True,
    )
    """Allow scroll on X or Y axis.

    :attr:`do_scroll` is a :class:`~kivy.properties.AliasProperty` of
    (:attr:`do_scroll_x` + :attr:`do_scroll_y`)
    """

    always_overscroll = BooleanProperty(True)
    """Make sure user can overscroll even if there is not enough content
    to require scrolling.

    This is useful if you want to trigger some action on overscroll, but
    there is not always enough content to trigger it.

    :attr:`always_overscroll` is a
    :class:`~kivy.properties.BooleanProperty` and defaults to `True`.

    .. versionadded:: 2.0.0

    The option was added and enabled by default, set to False to get the
    previous behavior of only allowing to overscroll when there is
    enough content to allow scrolling.
    """

    def _get_vbar(self):
        # must return (y, height) in %
        # calculate the viewport size / scrollview size %
        if self._viewport is None:
            return 0, 1.0
        vh = self._viewport.height
        h = self.height
        if vh < h or vh == 0:
            return 0, 1.0
        ph = max(0.01, h / float(vh))
        sy = min(1.0, max(0.0, self.scroll_y))
        py = (1.0 - ph) * sy
        return (py, ph)

    vbar = AliasProperty(
        _get_vbar,
        bind=("scroll_y", "_viewport", "viewport_size", "height"),
        cache=True,
    )
    """Return a tuple of (position, size) of the vertical scrolling bar.

    .. versionadded:: 1.2.0

    The position and size are normalized between 0-1, and represent a
    proportion of the current scrollview height. This property is used
    internally for drawing the little vertical bar when you're scrolling.

    :attr:`vbar` is a :class:`~kivy.properties.AliasProperty`, readonly.
    """

    def _get_hbar(self):
        # must return (x, width) in %
        # calculate the viewport size / scrollview size %
        if self._viewport is None:
            return 0, 1.0
        vw = self._viewport.width
        w = self.width
        if vw < w or vw == 0:
            return 0, 1.0
        pw = max(0.01, w / float(vw))
        sx = min(1.0, max(0.0, self.scroll_x))
        px = (1.0 - pw) * sx
        return (px, pw)

    hbar = AliasProperty(
        _get_hbar,
        bind=("scroll_x", "_viewport", "viewport_size", "width"),
        cache=True,
    )
    """Return a tuple of (position, size) of the horizontal scrolling bar.

    .. versionadded:: 1.2.0

    The position and size are normalized between 0-1, and represent a
    proportion of the current scrollview height. This property is used
    internally for drawing the little horizontal bar when you're scrolling.

    :attr:`hbar` is a :class:`~kivy.properties.AliasProperty`, readonly.
    """

    bar_color = ColorProperty([0.7, 0.7, 0.7, 0.9])
    """Color of horizontal / vertical scroll bar, in RGBA format.

    .. versionadded:: 1.2.0

    :attr:`bar_color` is a :class:`~kivy.properties.ColorProperty` and defaults
    to [.7, .7, .7, .9].

    .. versionchanged:: 2.0.0
        Changed from :class:`~kivy.properties.ListProperty` to
        :class:`~kivy.properties.ColorProperty`.
    """

    bar_inactive_color = ColorProperty([0.7, 0.7, 0.7, 0.2])
    """Color of horizontal / vertical scroll bar (in RGBA format), when no
    scroll is happening.

    .. versionadded:: 1.9.0

    :attr:`bar_inactive_color` is a
    :class:`~kivy.properties.ColorProperty` and defaults to [.7, .7, .7, .2].

    .. versionchanged:: 2.0.0
        Changed from :class:`~kivy.properties.ListProperty` to
        :class:`~kivy.properties.ColorProperty`.
    """

    bar_width = NumericProperty("2dp")
    """Width of the horizontal / vertical scroll bar. The width is interpreted
    as a height for the horizontal bar.

    .. versionadded:: 1.2.0

    :attr:`bar_width` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 2.
    """

    bar_pos_x = OptionProperty("bottom", options=("top", "bottom"))
    """Which side of the ScrollView the horizontal scroll bar should go
    on. Possible values are 'top' and 'bottom'.

    .. versionadded:: 1.8.0

    :attr:`bar_pos_x` is an :class:`~kivy.properties.OptionProperty`,
    defaults to 'bottom'.

    """

    bar_pos_y = OptionProperty("right", options=("left", "right"))
    """Which side of the ScrollView the vertical scroll bar should go
    on. Possible values are 'left' and 'right'.

    .. versionadded:: 1.8.0

    :attr:`bar_pos_y` is an :class:`~kivy.properties.OptionProperty` and
    defaults to 'right'.

    """

    bar_pos = ReferenceListProperty(bar_pos_x, bar_pos_y)
    """Which side of the scroll view to place each of the bars on.

    :attr:`bar_pos` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`bar_pos_x`, :attr:`bar_pos_y`)
    """

    bar_margin = NumericProperty(0)
    """Margin between the bottom / right side of the scrollview when drawing
    the horizontal / vertical scroll bar.

    .. versionadded:: 1.2.0

    :attr:`bar_margin` is a :class:`~kivy.properties.NumericProperty`, default
    to 0
    """

    effect_cls = ObjectProperty(DampedScrollEffect, allownone=True)
    """Class effect to instantiate for X and Y axis.

    .. versionadded:: 1.7.0

    :attr:`effect_cls` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to :class:`DampedScrollEffect`.

    .. versionchanged:: 1.8.0
        If you set a string, the :class:`~kivy.factory.Factory` will be used to
        resolve the class.

    """

    effect_x = ObjectProperty(None, allownone=True)
    """Effect to apply for the X axis. If None is set, an instance of
    :attr:`effect_cls` will be created.

    .. versionadded:: 1.7.0

    :attr:`effect_x` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    """

    effect_y = ObjectProperty(None, allownone=True)
    """Effect to apply for the Y axis. If None is set, an instance of
    :attr:`effect_cls` will be created.

    .. versionadded:: 1.7.0

    :attr:`effect_y` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None, read-only.
    """

    viewport_size = ListProperty([0, 0])
    """(internal) Size of the internal viewport. This is the size of your only
    child in the scrollview.
    """

    scroll_type = OptionProperty(
        ["content"],
        options=(
            ["content"],
            ["bars"],
            ["bars", "content"],
            ["content", "bars"],
        ),
    )
    """Sets the type of scrolling to use for the content of the scrollview.
    Available options are: ['content'], ['bars'], ['bars', 'content'].

    +---------------------+------------------------------------------------+
    | ['content']         | Content is scrolled by dragging or swiping the |
    |                     | content directly.                              |
    +---------------------+------------------------------------------------+
    | ['bars']            | Content is scrolled by dragging or swiping the |
    |                     | scroll bars.                                   |
    +---------------------+------------------------------------------------+
    | ['bars', 'content'] | Content is scrolled by either of the above     |
    |                     | methods.                                       |
    +---------------------+------------------------------------------------+

    .. versionadded:: 1.8.0

    :attr:`scroll_type` is an :class:`~kivy.properties.OptionProperty` and
    defaults to ['content'].
    """

    smooth_scroll_end = NumericProperty(None, allownone=True)
    """Whether smooth scroll end should be used when scrolling with the
    mouse-wheel and the factor of transforming the scroll distance to
    velocity. This option also enables velocity addition meaning if you
    scroll more, you will scroll faster and further. The recommended value
    is `10`. The velocity is calculated as :attr:`scroll_wheel_distance` *
    :attr:`smooth_scroll_end`.

    .. versionadded:: 1.11.0

    :attr:`smooth_scroll_end` is a :class:`~kivy.properties.NumericProperty`
    and defaults to None.
    """

    slow_device_support = BooleanProperty(False)
    """Enable slow device support for scroll gesture detection.

    On very slow devices, at least 3 frames are needed to accumulate
    velocity data for scroll effects to work properly. When enabled,
    after the scroll timeout expires, the gesture handoff will be delayed
    until at least 3 frames have rendered, ensuring sufficient velocity
    data accumulation.

    This addresses issues #1464 and #1499 for low-performance devices.
    Disable this on modern hardware to improve touch responsiveness.

    :attr:`slow_device_support` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to False.

    .. versionadded:: NEXT_VERSION
    """
    parallel_delegation = BooleanProperty(True)
    """Controls boundary delegation behavior for parallel nested ScrollViews.

    When True (default, web-style):
        - Touch starting at inner boundary, moving away → delegates to outer
        - Touch starting not at boundary → scrolls inner only, never delegates

    When False:
        - No delegation, only touched ScrollView scrolls

    :attr:`parallel_delegation` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to True.

    .. versionadded:: NEXT_VERSION
    """

    delegate_to_outer = BooleanProperty(True)
    """Controls whether touch scroll gestures delegate to outer ScrollViews.

    When True (default):
        - Orthogonal: Cross-axis gestures immediately delegate to outer
          (e.g., horizontal swipe in vertical-only ScrollView)
        - Parallel: At boundaries, delegates to outer
          (respects parallel_delegation)
        - Arbitrary depth: Continues searching up hierarchy for
          capable ScrollView

    When False:
        - No delegation to outer ScrollViews
        - Only the directly touched ScrollView handles the gesture

    NOTE: Mouse wheel events are NOT affected by this property. Wheel scrolling
    always uses web-style behavior: scroll the innermost ScrollView under cursor
    that can handle the direction.

    Example use cases:
        - Set False to lock touch scrolling to a specific nested level
        - Set False to prevent inner touch scroll from affecting outer scroll

    :attr:`delegate_to_outer` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to True.

    .. versionadded:: NEXT_VERSION
    """

    # Class constants for mouse wheel scroll button sets
    _MOUSE_WHEEL_HORIZONTAL = {"scrollleft", "scrollright"}
    _MOUSE_WHEEL_VERTICAL = {"scrolldown", "scrollup"}
    _MOUSE_WHEEL_DECREASE = {"scrolldown", "scrollleft"}  # negative direction
    _MOUSE_WHEEL_INCREASE = {"scrollup", "scrollright"}  # positive direction

    _viewport = ObjectProperty(None, allownone=True)
    _bar_color = ListProperty([0, 0, 0, 0])

    def _set_viewport_size(self, instance, value):
        self.viewport_size = value

    def on__viewport(self, instance, value):
        if value:
            value.bind(size=self._set_viewport_size)
            self.viewport_size = value.size

    def __init__(self, **kwargs):
        self._touch = None
        self._nested_sv_active_touch = (
            None  # Stores the touch that's currently active in nested scenario
        )
        self._trigger_update_from_scroll = Clock.create_trigger(
            self.update_from_scroll, -1
        )
        # For velocity-based stop detection for on_scroll_stop
        self._velocity_check_ev = None
        self._position_check_ev = None
        self._last_scroll_pos = None
        self._stable_frames = 0
        # For scroll effect tracking
        self._effect_x_start_width = None
        self._effect_y_start_height = None
        self._update_effect_bounds_ev = None
        self._bind_inactive_bar_color_ev = None
        # create a specific canvas for the viewport
        self.canvas_viewport = Canvas()
        self.canvas = Canvas()
        with self.canvas_viewport.before:
            PushMatrix()
            self.g_translate = Translate(0, 0)
        with self.canvas_viewport.after:
            PopMatrix()

        super(ScrollView, self).__init__(**kwargs)

        self.register_event_type("on_scroll_start")
        self.register_event_type("on_scroll_move")
        self.register_event_type("on_scroll_stop")

        # Bind scroll position changes to dispatch on_scroll_move
        self.fbind("scroll_x", self._on_scroll_pos_changed)
        self.fbind("scroll_y", self._on_scroll_pos_changed)

        # now add the viewport canvas to our canvas
        self.canvas.add(self.canvas_viewport)

        effect_cls = self.effect_cls
        if isinstance(effect_cls, str):
            effect_cls = Factory.get(effect_cls)
        if self.effect_x is None and effect_cls is not None:
            self.effect_x = effect_cls(target_widget=self._viewport)
        if self.effect_y is None and effect_cls is not None:
            self.effect_y = effect_cls(target_widget=self._viewport)

        trigger_update_from_scroll = self._trigger_update_from_scroll
        update_effect_widget = self._update_effect_widget
        update_effect_x_bounds = self._update_effect_x_bounds
        update_effect_y_bounds = self._update_effect_y_bounds
        fbind = self.fbind
        fbind("width", update_effect_x_bounds)
        fbind("height", update_effect_y_bounds)
        fbind("viewport_size", self._update_effect_bounds)
        fbind("_viewport", update_effect_widget)
        fbind("scroll_x", trigger_update_from_scroll)
        fbind("scroll_y", trigger_update_from_scroll)
        fbind("pos", trigger_update_from_scroll)
        fbind("size", trigger_update_from_scroll)

        trigger_update_from_scroll()
        update_effect_widget()
        update_effect_x_bounds()
        update_effect_y_bounds()

    def on_effect_x(self, instance, value):
        if value:
            value.bind(scroll=self._update_effect_x)
            value.target_widget = self._viewport

    def on_effect_y(self, instance, value):
        if value:
            value.bind(scroll=self._update_effect_y)
            value.target_widget = self._viewport

    def on_effect_cls(self, instance, cls):
        if isinstance(cls, str):
            cls = Factory.get(cls)
        self.effect_x = cls(target_widget=self._viewport)
        self.effect_x.bind(scroll=self._update_effect_x)
        self.effect_y = cls(target_widget=self._viewport)
        self.effect_y.bind(scroll=self._update_effect_y)

    def _update_effect_widget(self, *args):
        if self.effect_x:
            self.effect_x.target_widget = self._viewport
        if self.effect_y:
            self.effect_y.target_widget = self._viewport

    def _update_effect_x_bounds(self, *args):
        if not self._viewport or not self.effect_x:
            return
        scrollable_width = self.width - self.viewport_size[0]
        self.effect_x.min = 0
        self.effect_x.max = min(0, scrollable_width)
        self.effect_x.value = scrollable_width * self.scroll_x

    def _update_effect_y_bounds(self, *args):
        if not self._viewport or not self.effect_y:
            return
        scrollable_height = self.height - self.viewport_size[1]
        self.effect_y.min = 0 if scrollable_height < 0 else scrollable_height
        self.effect_y.max = scrollable_height
        self.effect_y.value = self.effect_y.max * self.scroll_y

    def _update_effect_bounds(self, *args):
        # "sync up the physics with reality" method
        # keeps the smooth scrolling effects aligned with the actual SV state
        self._update_effect_x_bounds()
        self._update_effect_y_bounds()

    def _update_effect_x(self, *args):
        vp = self._viewport
        if not vp or not self.effect_x:
            return

        if self.effect_x.is_manual:
            sw = vp.width - self._effect_x_start_width
        else:
            sw = vp.width - self.width
        if sw < 1 and not (self.always_overscroll and self.do_scroll_x):
            return
        if sw != 0:
            sx = self.effect_x.scroll / sw
            self.scroll_x = -sx
        self._trigger_update_from_scroll()

    def _update_effect_y(self, *args):
        vp = self._viewport
        if not vp or not self.effect_y:
            return
        if self.effect_y.is_manual:
            sh = vp.height - self._effect_y_start_height
        else:
            sh = vp.height - self.height

        if sh < 1 and not (self.always_overscroll and self.do_scroll_y):
            return
        if sh != 0:
            sy = self.effect_y.scroll / sh
            self.scroll_y = -sy
        self._trigger_update_from_scroll()

    def to_local(self, x, y, **k):
        tx, ty = self.g_translate.xy
        return x - tx, y - ty

    def to_parent(self, x, y, **k):
        tx, ty = self.g_translate.xy
        return x + tx, y + ty

    def _apply_transform(self, m, pos=None):
        tx, ty = self.g_translate.xy
        m.translate(tx, ty, 0)
        return super(ScrollView, self)._apply_transform(m, (0, 0))

    def _simulate_touch_down(self, touch):
        # CONTROLLED TOUCH RE-DISPATCH TO CHILD WIDGETS
        # ==============================================
        # This method safely re-dispatches touch events to child widgets,
        # typically used when a touch gesture is determined to be a
        # click rather than a scroll.
        #
        # Returns:
        #     bool: True if a child widget handled/consumed the touch,
        #           False otherwise.
        #           This indicates whether the touch was accepted by
        #           a child widget
        #           (e.g., a button, text input, etc.).
        touch.push()
        touch.apply_transform_2d(self.to_local)

        # Dispatch touch to children
        ret = super(ScrollView, self).on_touch_down(touch)

        touch.pop()
        return ret

    def on_motion(self, etype, me):
        if me.type_id in self.motion_filter and "pos" in me.profile:
            me.push()
            me.apply_transform_2d(self.to_local)
            ret = super().on_motion(etype, me)
            me.pop()
            return ret
        return super().on_motion(etype, me)

    def _delegate_to_children(self, touch, method_name, check_collision=True):
        # Generic helper function to safely delegate touch events to child
        # widgets.
        # Handles coordinate transformation and returns the result.
        # Args:
        #   touch: The touch event to delegate
        #   method_name: The method name to call (e.g., 'on_touch_move')
        #   check_collision: Whether to check collision before delegating
        # Returns: True if any child handled the touch, False otherwise
        if check_collision and not self.collide_point(*touch.pos):
            return False

        touch.push()
        touch.apply_transform_2d(self.to_local)
        res = getattr(super(ScrollView, self), method_name)(touch)
        touch.pop()
        return res

    def _delegate_touch_up_to_children_widget_coords(self, touch):
        # Delegate touch_up to children using widget coordinates
        # (no collision check).
        touch.push()
        touch.apply_transform_2d(self.to_widget)
        res = super(ScrollView, self).on_touch_up(touch)
        touch.pop()
        return res

    def _find_child_scrollview_at_touch(self, touch):
        # Find the child ScrollView that collides with the touch position.
        #
        # Strategy: When we encounter a Layout,
        # we first identify which specific child collides with the touch,
        # then only explore that child's subtree. This naturally handles
        # arbitrary depth and prevents finding ScrollViews from unrelated
        # sibling branches.
        #
        # Returns:
        #     ScrollView: The first child ScrollView that collides with touch,
        #                 or None

        viewport = self._viewport

        # Safety checks: viewport must exist and have children
        if not viewport:
            return None
        if not hasattr(viewport, "children"):
            return None
        if not viewport.children:
            return None

        # Transform touch to viewport space
        touch.push()
        touch.apply_transform_2d(viewport.to_widget)

        result = self._find_scrollview_in_widget(viewport, touch)

        touch.pop()
        return result

    def _find_scrollview_in_widget(self, widget, touch):
        # Recursively find ScrollView under touch, narrowing by Layout children.
        #
        # When we encounter a widget with children (a Layout), we first
        # identify which specific child collides with the touch point, then
        # only explore that child's subtree. This prevents finding ScrollViews
        # from unrelated sibling branches.
        #
        # Args:
        #     widget: The widget to search within
        #     touch: The touch event (already transformed to appropriate space)
        #
        # Returns:
        #     ScrollView or None: The first ScrollView found under touch
        # If this widget has children,
        # narrow down which child contains the touch
        if hasattr(widget, "children") and widget.children:
            for child in widget.children:
                # Skip children that don't collide with touch
                if not child.collide_point(*touch.pos):
                    continue

                # Found a colliding child - is it a ScrollView?
                if isinstance(child, ScrollView):
                    return child

                # Not a ScrollView, but it collides -
                # recursively search its subtree
                result = self._find_scrollview_in_widget(child, touch)
                if result:
                    return result

        # No children or no colliding children with ScrollViews
        return None

    def _build_hierarchy_recursive(self, touch):
        # Build complete ScrollView hierarchy from this (outer) to innermost.
        #
        # Recursively finds all nested ScrollViews under the touch point and
        # builds a ScrollViewHierarchy object with classifications for each
        # parent-child relationship.
        #
        # Args:
        #     touch: The touch event
        #
        # Returns:
        #     ScrollViewHierarchy or None: Complete hierarchy from this (outer)
        #                                 to innermost, or None if no children
        # Find immediate child
        child_sv = self._find_child_scrollview_at_touch(touch)

        if not child_sv:
            return None

        # Start building hierarchy with self as outer
        hierarchy = ScrollViewHierarchy(self)

        # Recursively build the chain
        current_sv = child_sv
        parent_sv = self

        while current_sv:
            # Classify this parent-child relationship
            config_type, axis_config = (
                parent_sv._classify_nested_configuration(current_sv))

            # Add to hierarchy
            hierarchy.add_child(current_sv, config_type, axis_config)

            # Look for next level down
            parent_sv = current_sv
            current_sv = current_sv._find_child_scrollview_at_touch(touch)

        return hierarchy

    def _get_nested_data(self, touch):
        # Extract nested coordination data for this ScrollView from touch.
        #
        # Provides convenient access to hierarchy, current index, and parent
        # for arbitrary depth nesting. This method makes it easy for any
        # ScrollView in the hierarchy to find its place and navigate.
        #
        # NOTE: This method is for FUTURE arbitrary nesting support (Phase 3+).
        # Currently NOT USED by 2-level delegation logic. Will be integrated
        # when chain delegation is implemented.
        #
        # Args:
        #     touch: The touch event
        #
        # Returns:
        #     tuple: (hierarchy, my_index, parent_sv) where:
        #         - hierarchy: ScrollViewHierarchy object
        #         - my_index: Index of this ScrollView in the hierarchy
        #         - parent_sv: Parent ScrollView, or None if this is outermost
        #
        #         Returns (None, None, None) if not in a nested configuration
        #         or if this ScrollView is not found in the hierarchy.
        if "nested" not in touch.ud:
            return None, None, None

        if "hierarchy" not in touch.ud["nested"]:
            return None, None, None

        hierarchy = touch.ud["nested"]["hierarchy"]

        # Find our index in the hierarchy
        my_index = None
        for i, sv in enumerate(hierarchy.scrollviews):
            if sv is self:
                my_index = i
                break

        if my_index is None:
            return None, None, None

        parent_sv = hierarchy.get_parent(my_index)

        return hierarchy, my_index, parent_sv

    def _get_primary_scroll_axis(self, touch):
        # Determine which axis has dominant touch movement.
        #
        # Compares absolute X and Y deltas to determine the primary direction
        # of the current touch movement. Used for axis-specific scroll logic.
        #
        # Args:
        #     touch: Touch event with dx and dy attributes
        #
        # Returns:
        #     str: 'x' if horizontal movement dominates,
        #          'y' if vertical movement dominates,
        #          None if no clear dominance
        abs_dx = abs(touch.dx)
        abs_dy = abs(touch.dy)

        if abs_dx > abs_dy:
            return "x"
        elif abs_dy > abs_dx:
            return "y"
        return None

    def _classify_nested_configuration(self, child_sv):
        # Classify the nested ScrollView configuration type.
        #
        # Determines if the outer/inner relationship is:
        # - Orthogonal: Different axes (e.g., outer=vertical, inner=horizontal)
        # - Parallel: Same axes (e.g., both vertical)
        # - Mixed: Combination (e.g., outer=xy, inner=vertical)
        #
        # Args:
        #     child_sv: The inner ScrollView
        #
        # Returns:
        #     tuple: (config_type, axis_config)
        #         config_type: 'orthogonal', 'parallel', or 'mixed'
        #         axis_config: dict with 'shared', 'outer_exclusive',
        #         'inner_exclusive'
        #                     (only for mixed configurations, None otherwise)

        outer_axes = (self.do_scroll_x, self.do_scroll_y)
        inner_axes = (child_sv.do_scroll_x, child_sv.do_scroll_y)

        # Determine configuration type
        is_orthogonal = (
                outer_axes[0] != inner_axes[0]
                and outer_axes[1] != inner_axes[1]
                and (outer_axes[0] or outer_axes[1])
                and (inner_axes[0] or inner_axes[1])
        )

        if is_orthogonal:
            return ("orthogonal", None)

        is_parallel = outer_axes == inner_axes
        if is_parallel:
            return ("parallel", None)

        # Mixed configuration - determine axis capabilities
        shared = []
        outer_exclusive = []
        inner_exclusive = []

        # Check X axis
        if outer_axes[0] and inner_axes[0]:
            shared.append("x")
        elif outer_axes[0] and not inner_axes[0]:
            outer_exclusive.append("x")
        elif not outer_axes[0] and inner_axes[0]:
            inner_exclusive.append("x")

        # Check Y axis
        if outer_axes[1] and inner_axes[1]:
            shared.append("y")
        elif outer_axes[1] and not inner_axes[1]:
            outer_exclusive.append("y")
        elif not outer_axes[1] and inner_axes[1]:
            inner_exclusive.append("y")

        axis_config = {
            "shared": shared,
            "outer_exclusive": outer_exclusive,
            "inner_exclusive": inner_exclusive,
        }

        return ("mixed", axis_config)

    def _initialize_nested_inner(self, touch, child_sv):
        # Initialize scrolling on the inner ScrollView with proper coordinate
        # transformation.
        #
        #
        # Args:
        #     touch: The touch/mouse event
        #     child_sv: The inner ScrollView to initialize
        #
        # Returns:
        #     bool: True if scrolling was successfully initialized,
        #           False if both rejected the touch

        is_wheel = "button" in touch.profile and touch.button.startswith(
            "scroll"
        )

        # Transform touch to inner's PARENT coordinate space
        # (NOT viewport, NOT window - the parent widget that contains the inner)
        touch.push()
        touch.apply_transform_2d(child_sv.parent.to_widget)
        result = child_sv._scroll_initialize(touch)
        touch.pop()

        if result:
            # Inner accepted scrolling (or delegated to child widget)
            # Check if inner actually set up scroll state
            # (not just delegated to button)
            inner_uid = child_sv._get_uid()
            if inner_uid in touch.ud:
                # Inner actually set up scroll state - this is real scrolling
                # For MOUSE WHEEL: Don't grab or set _touch
                # (each wheel event is independent)
                # For REGULAR TOUCH: Outer grabs, inner's _touch is set for
                # coordination
                if not is_wheel:
                    # Regular touch: outer grabs, inner tracks the touch
                    touch.grab(self)
                    child_sv._touch = touch
                    self._nested_sv_active_touch = (
                        touch  # Store the active touch for nested scenario
                    )
                    # Wheel events are handled immediately,
                    # no grab/touch tracking needed
                # Inner set up scroll state - claim the touch
                return True
            else:
                # Inner delegated to a child widget (button, etc) -
                # DON'T claim the touch...
                # Let it propagate so the button can grab and handle it
                return False

        # Inner rejected the touch
        # For MOUSE WHEEL in orthogonal setups, try outer ScrollView
        if is_wheel:
            # Try outer with ORIGINAL touch (already popped above)
            if self._scroll_initialize(touch):
                return True

        return False

    # =========================================================================
    # TOUCH HANDLER HELPER METHODS
    # =========================================================================
    # The following helper methods support the main touch handling lifecycle.
    # They are organized by purpose: detection, delegation, intent,
    # finalization.

    def _setup_boundary_delegation(self, touch, in_bar):
        # Configure web-style boundary delegation for parallel nested scrolling.
        #
        # In parallel nested setups (both scrolling same direction), detects if
        # touch starts at this ScrollView's scroll boundary. If so, marks for
        # immediate delegation to parent on first movement away from boundary.
        #
        # For arbitrary depth: Uses hierarchy to find immediate parent,
        # not always outer.
        #
        # Only applies when:
        # - Touch is in a nested configuration
        # - Not in a scrollbar (delegation disabled for bars)
        # - parent.parallel_delegation is True
        #
        # Args:
        #     touch: The touch event with touch.ud['nested'] already set
        #     in_bar: Whether touch is in a scrollbar
        if "nested" not in touch.ud or in_bar:
            return

        # For arbitrary depth: find our immediate parent from hierarchy
        hierarchy, my_index, parent_sv = self._get_nested_data(touch)

        if not parent_sv:
            # We're the outer or not in hierarchy - no delegation needed
            return

        # Only proceed if parent has parallel_delegation enabled
        if not parent_sv.parallel_delegation:
            return

        # PARALLEL DELEGATION: Only check boundaries in directions where BOTH
        # child and parent scroll.
        # In orthogonal setups (child scrolls Y, parent scrolls X),
        # the child should freely overscroll in Y direction without delegation.

        # Check X boundary only if both child and parent scroll horizontally
        at_boundary_x = (
                self.do_scroll_x
                and parent_sv.do_scroll_x
                and self._is_at_scroll_boundary("x")
        )

        # Check Y boundary only if both child and parent scroll vertically
        at_boundary_y = (
                self.do_scroll_y
                and parent_sv.do_scroll_y
                and self._is_at_scroll_boundary("y")
        )

        # Set delegation_mode based on boundary state in PARALLEL only
        # For arbitrary depth: Store per-ScrollView delegation mode using UID
        if at_boundary_x or at_boundary_y:
            # Store per-ScrollView delegation mode
            sv_uid = self._get_uid()
            if "delegation_modes" not in touch.ud["nested"]:
                touch.ud["nested"]["delegation_modes"] = {}
            touch.ud["nested"]["delegation_modes"][
                sv_uid
            ] = DelegationMode.START_AT_BOUNDARY

            # Also set global mode for backward compatibility with 2-level code
            touch.ud["nested"][
                "delegation_mode"
            ] = DelegationMode.START_AT_BOUNDARY

    def _delegate_to_parent_scroll(self, touch, child_sv, parent_sv):
        # Delegate scrolling from child to parent ScrollView in hierarchy chain.
        #
        # Called when a child ScrollView rejects touch movement
        # (e.g., orthogonal gesture, boundary reached, or delegation decision).
        # Initializes parent's scroll state and takes over scroll handling.
        #
        # This supports arbitrary depth by delegating to immediate parent, which
        # can then delegate to ITS parent if needed.
        #
        # Args:
        #     touch: The touch event
        #     child_sv: The child ScrollView that is relinquishing control
        #     parent_sv: The parent ScrollView that will take over
        #
        # Returns:
        #     bool: Result from parent's _scroll_update
        # Initialize parent's scroll state if not already set up
        parent_uid = parent_sv._get_uid()
        if parent_uid not in touch.ud:
            touch.ud[parent_uid] = {
                "mode": ScrollMode.SCROLL,  # Already scrolling (not UNKNOWN)
                "dx": 0,
                "dy": 0,
                "scroll_action": False,
                "frames": 0,
                "can_defocus": False,
            }
            parent_sv._initialize_scroll_effects(touch, in_bar=False)
            parent_sv._touch = touch
            parent_sv.dispatch("on_scroll_start")
            if child_sv:
                # CRITICAL: Finalize child's scroll when cascading
                # This stops effects AND schedules on_scroll_stop event
                # But doesn't interfere with normal on_touch_up to
                # buttons/widgets
                child_sv._finalize_scroll_for_cascade(touch)

        # Now process the touch movement with parent
        touch.ud["sv.handled"] = {"x": False, "y": False}
        return parent_sv._scroll_update(touch)

    def _detect_scroll_intent(self, touch, ud):
        # Detect if touch movement indicates scroll intent vs click.
        #
        # Tracks cumulative movement while in 'unknown' mode. Once movement
        # exceeds scroll_distance threshold, transitions to 'scroll' mode.
        #
        # Args:
        #     touch: The touch event
        #     ud: The touch's user data dict for this ScrollView
        #
        # Returns:
        #     bool: True if processing should continue, False if rejected

        if not (self.do_scroll_x or self.do_scroll_y):
            # No scrolling enabled - trigger mode change to delegate to children
            # Touch is in parent coords, but _change_touch_mode expects
            # window coords
            touch.push()
            touch.apply_transform_2d(self.to_local)
            touch.apply_transform_2d(self.to_window)
            self._change_touch_mode()
            touch.pop()
            return False

        # Accumulate absolute movement on both axes
        ud["dx"] += abs(touch.dx)
        ud["dy"] += abs(touch.dy)

        # Transition to scroll mode if movement exceeds threshold
        if ud["dx"] > self.scroll_distance or ud["dy"] > self.scroll_distance:
            ud["mode"] = ScrollMode.SCROLL
            # Only dispatch on_scroll_start if we weren't already scrolling
            # (e.g. from scrollbar)
            if not ud["scroll_action"]:
                self.dispatch("on_scroll_start")

        return True

    def _check_nested_delegation(self, touch, not_in_bar):
        # Check if this ScrollView should delegate to its parent in hierarchy.
        #
        # Uses the hierarchy to find this ScrollView's relationship with
        # its parent and calls the appropriate delegation method.
        # Supports arbitrary depth.
        #
        # Only applies to ScrollViews scrolling content (not scrollbars).
        #
        # Args:
        #     touch: The touch event
        #     not_in_bar: Whether touch is NOT in a scrollbar
        #
        # Returns:
        #     bool: True if should delegate to parent
        #           False if should continue handling
        # Only check delegation for nested ScrollViews scrolling content
        if "nested" not in touch.ud:
            return False
        if not not_in_bar:
            return False

        # Get hierarchy and find our position
        hierarchy, my_index, parent_sv = self._get_nested_data(touch)

        # Check if delegation to outer is enabled
        if not self.delegate_to_outer:
            return False  # Delegation disabled - don't cascade to parent

        if not hierarchy or parent_sv is None:
            return False  # Not nested or we're the outer - no delegation

        # Only check delegation if we're the CURRENT handler in the hierarchy
        # For arbitrary depth: check current_index
        # Check if we're the current handler (hierarchy-based routing)
        if "current_index" not in touch.ud["nested"]:
            # No routing info - shouldn't happen but be safe
            return False

        if my_index != touch.ud["nested"]["current_index"]:
            return False  # Not our turn to handle, don't delegate

        # CROSS-AXIS DELEGATION: Check FIRST if gesture is on an axis we can't
        # handle.  This applies regardless of our relationship type with our
        # immediate child
        # Example: V outer (can't scroll X) in V→H should delegate X gestures
        # to outer XY above
        primary_axis = self._get_primary_scroll_axis(touch)

        if primary_axis == "x" and not self.do_scroll_x:
            # Horizontal gesture but we only scroll vertically - delegate upward
            return True
        if primary_axis == "y" and not self.do_scroll_y:
            # Vertical gesture but we only scroll horizontally - delegate upward
            return True

        # Get our relationship with immediate parent
        classification = hierarchy.get_classification(my_index)
        axis_config = hierarchy.get_axis_config(my_index)

        # Dispatch to appropriate delegation method based on classification
        if classification == "orthogonal":
            # Check immediate parent first (standard orthogonal delegation)
            if self._should_delegate_orthogonal(touch, parent_sv):
                return True

            # PHASE 8: Non-adjacent parallel delegation
            # If orthogonal with immediate parent but we're at boundary AND
            # trying to scroll beyond,look for a parallel ancestor further up
            # the hierarchy
            # Example: V->H->V, inner V at boundary should delegate to outer V
            primary_axis = self._get_primary_scroll_axis(touch)
            if primary_axis and self._is_scrolling_beyond_boundary(
                    primary_axis, touch
            ):
                # We're at boundary AND scrolling beyond -
                # search for parallel ancestor
                parallel_ancestor, ancestor_idx = self._find_parallel_ancestor(
                    touch, primary_axis
                )
                if parallel_ancestor and parallel_ancestor.parallel_delegation:
                    # Found ancestor that can handle this axis with
                    # parallel_delegation enabled
                    # Delegate to it
                    #  (cascade will update current_index to ancestor_idx)
                    touch.ud["nested"]["parallel_ancestor_index"] = ancestor_idx
                    return True

            return False

        elif classification == "mixed":
            return self._should_delegate_mixed(touch, parent_sv, axis_config)
        elif classification == "parallel":
            return self._should_delegate_parallel(touch, parent_sv)

        return False

    def _is_at_scroll_boundary(self, axis):
        # Check if this ScrollView is at a scroll boundary on the given axis.
        #
        # Args:
        #     axis: 'x' or 'y' - the axis to check
        #
        # Returns:
        #     bool: True if at boundary (near 0.0 or 1.0), False otherwise
        if axis == "x":
            if not self.do_scroll_x:
                return False
            scroll_pos = self.scroll_x
        elif axis == "y":
            if not self.do_scroll_y:
                return False
            scroll_pos = self.scroll_y
        else:
            return False

        # At boundary if within threshold of min or max
        return scroll_pos <= _BOUNDARY_THRESHOLD or scroll_pos >= (
                1.0 - _BOUNDARY_THRESHOLD
        )

    def _is_scrolling_beyond_boundary(self, axis, touch):
        # Check if scroll gesture is trying to move beyond the current boundary.
        #
        # Args:
        #     axis: 'x' or 'y' - the axis to check
        #     touch: The touch event
        #
        # Returns:
        #     bool: True if at boundary AND trying to scroll beyond it
        if axis == "x":
            if not self.do_scroll_x:
                return False
            scroll_pos = self.scroll_x
            # Check scroll direction from touch movement
            dx = touch.dx if hasattr(touch, "dx") else (touch.x - touch.px)

            # At left boundary (scroll_x ~= 0.0) trying to scroll further left
            if scroll_pos <= _BOUNDARY_THRESHOLD and dx > 0:
                return True
            # At right boundary (scroll_x ~= 1.0) trying to scroll further right
            if scroll_pos >= (1.0 - _BOUNDARY_THRESHOLD) and dx < 0:
                return True

        elif axis == "y":
            if not self.do_scroll_y:
                return False
            scroll_pos = self.scroll_y
            # Check scroll direction from touch movement
            dy = touch.dy if hasattr(touch, "dy") else (touch.y - touch.py)

            # At top boundary (scroll_y ~= 0.0) trying to scroll further up
            if scroll_pos <= _BOUNDARY_THRESHOLD and dy > 0:
                return True
            # At bottom boundary (scroll_y ~= 1.0) trying to scroll further down
            if scroll_pos >= (1.0 - _BOUNDARY_THRESHOLD) and dy < 0:
                return True

        return False

    def _find_parallel_ancestor(self, touch, axis):
        # Find nearest ancestor in hierarchy that can scroll on the given axis.
        #
        # Skips orthogonal intermediates to enable non-adjacent parallel
        # delegation. Used: V->H->V boundary delegation.
        #
        # CRITICAL: Respects delegate_to_outer property. If an intermediate
        # ScrollView has delegate_to_outer=False, we stop searching there
        # (acting as a delegation barrier).
        #
        # Args:
        #     touch: The touch event
        #     axis: 'x' or 'y' - the axis to search for
        #
        # Returns:
        #     tuple: (ancestor_sv, ancestor_index) if found,
        #            (None, None) if not found
        #
        # Example:
        #     V->H->V hierarchy: Inner V at boundary, searching for 'y'
        #     - Skips Middle H (can't scroll Y)
        #     - Returns Outer V (can scroll Y)
        #
        #     BUT if Outer V has delegate_to_outer=False:
        #     - Returns (None, None) - can't delegate past the barrier
        hierarchy, my_index, _ = self._get_nested_data(touch)
        if not hierarchy:
            return None, None

        # Walk up hierarchy looking for ancestor that can scroll on this axis
        for i in range(my_index - 1, -1, -1):
            ancestor = hierarchy.scrollviews[i]

            # CRITICAL: Check if this ancestor allows delegation through it
            # If delegate_to_outer=False, it acts as a barrier
            #  - stop searching here
            if not ancestor.delegate_to_outer:
                return None, None

            # Check if this ancestor can handle the axis we need
            if axis == "x" and ancestor.do_scroll_x:
                return ancestor, i
            if axis == "y" and ancestor.do_scroll_y:
                return ancestor, i

        return None, None

    def _handle_focus_behavior(self, touch, uid_key):
        # Handle focus behavior after scroll finalization.
        #
        # If the touch caused scrolling (can_defocus=False), add it to the
        # ignored list so focused widgets don't get defocused by this touch.
        #
        # Args:
        #     touch: The touch event
        #     uid_key: The unique key for this ScrollView's touch data

        if uid_key in touch.ud and not touch.ud[uid_key].get(
                "can_defocus", True
        ):
            FocusBehavior.ignored_touch.append(touch)

    def _touch_in_handle(self, pos, size, touch):
        # check if the touch is in the handle of the scrollview
        # touching the handle allows the user to drag the scrollview
        # clicking in the bar, and not the handle, jumps to that position
        # in the scrollview
        x, y = pos
        width, height = size
        return x <= touch.x <= x + width and y <= touch.y <= y + height

    def _check_scroll_bounds(self, touch):
        # Check if touch is within scrollable bounds and set in_bar flags.
        vp = self._viewport
        if not vp:
            return False, False

        # Calculate scrollable dimensions
        width_scrollable = (
                                   self.always_overscroll and self.do_scroll_x
                           ) or vp.width > self.width
        height_scrollable = (
                                    self.always_overscroll and self.do_scroll_y
                            ) or vp.height > self.height

        # Calculate distance from touch to scroll bar edges
        d = {
            "bottom": touch.y - self.y - self.bar_margin,
            "top": self.top - touch.y - self.bar_margin,
            "left": touch.x - self.x - self.bar_margin,
            "right": self.right - touch.x - self.bar_margin,
        }

        # Check if touch is in horizontal or vertical scroll bars
        scroll_bar = "bars" in self.scroll_type
        in_bar_x = (
                scroll_bar
                and width_scrollable
                and (0 <= d[self.bar_pos_x] <= self.bar_width)
        )
        in_bar_y = (
                scroll_bar
                and height_scrollable
                and (0 <= d[self.bar_pos_y] <= self.bar_width)
        )

        return in_bar_x, in_bar_y

    def _handle_mouse_wheel_scroll(self, btn, in_bar_x, in_bar_y):
        # Handle mouse wheel scrolling - WEB-STYLE (no delegation).
        # Wheel scrolls ONLY this ScrollView if it can handle the direction.
        # If it can't, returns False to let parent widgets try.
        m = self.scroll_wheel_distance

        # WEB-STYLE BEHAVIOR:
        # Mouse wheel scrolls the innermost ScrollView under cursor that can
        # handle the direction. No automatic delegation through hierarchy - user
        # must move mouse to scroll a different element. This matches standard
        # web browser UX.

        if btn in self._MOUSE_WHEEL_HORIZONTAL:
            # Horizontal wheel: only handle if we can scroll horizontally
            if not (
                    self.do_scroll_x
                    and (
                            (self.always_overscroll and self.do_scroll_x)
                            or (self._viewport and
                                self._viewport.width > self.width)
                    )
            ):
                return False  # Can't scroll horizontally, pass to parent
        elif btn in self._MOUSE_WHEEL_VERTICAL:
            # Vertical wheel: only handle if we can scroll vertically
            if not (
                    self.do_scroll_y
                    and (
                            (self.always_overscroll and self.do_scroll_y)
                            or (self._viewport and
                                self._viewport.height > self.height)
                    )
            ):
                return False  # Can't scroll vertically, pass to parent

        # Select appropriate scroll effect
        e = self._select_scroll_effect_for_wheel(btn, in_bar_x, in_bar_y)
        if not e:
            return False

        # Dispatch on_scroll_start for mouse wheel scrolling
        self.dispatch("on_scroll_start")
        self._apply_wheel_scroll(e, btn, m)
        e.trigger_velocity_update()
        return True

    def _select_scroll_effect_for_wheel(self, btn, in_bar_x, in_bar_y):
        # Select the appropriate scroll effect for mouse wheel scrolling.
        vp = self._viewport
        if not vp:
            return None

        width_scrollable = (
                                   self.always_overscroll and self.do_scroll_x
                           ) or vp.width > self.width
        height_scrollable = (
                                    self.always_overscroll and self.do_scroll_y
                            ) or vp.height > self.height

        if (
                self.effect_x
                and self.do_scroll_y
                and height_scrollable
                and btn in self._MOUSE_WHEEL_VERTICAL
        ):
            return self.effect_x if in_bar_x else self.effect_y
        elif (
                self.effect_y
                and self.do_scroll_x
                and width_scrollable
                and btn in self._MOUSE_WHEEL_HORIZONTAL
        ):
            return self.effect_y if in_bar_y else self.effect_x
        return None

    def _apply_wheel_scroll(self, effect, btn, distance):
        # Apply wheel scroll movement to the selected effect.
        self._update_effect_bounds()

        if btn in self._MOUSE_WHEEL_DECREASE:
            if self.smooth_scroll_end:
                effect.velocity -= distance * self.smooth_scroll_end
            else:
                if self.always_overscroll:
                    effect.value = effect.value - distance
                else:
                    effect.value = max(effect.value - distance, effect.max)
                effect.velocity = 0
        elif btn in self._MOUSE_WHEEL_INCREASE:
            if self.smooth_scroll_end:
                effect.velocity += distance * self.smooth_scroll_end
            else:
                if self.always_overscroll:
                    effect.value = effect.value + distance
                else:
                    effect.value = min(effect.value + distance, effect.min)
                effect.velocity = 0

    def _handle_scrollbar_jump(self, touch, in_bar_x, in_bar_y):
        # Handle scrollbar position jump when clicking in bar but not handle.
        ud = touch.ud
        if in_bar_y and not self._touch_in_handle(
                self._handle_y_pos, self._handle_y_size, touch
        ):
            self.scroll_y = (touch.y - self.y) / self.height
        elif in_bar_x and not self._touch_in_handle(
                self._handle_x_pos, self._handle_x_size, touch
        ):
            self.scroll_x = (touch.x - self.x) / self.width

        e = self.effect_y if in_bar_y else self.effect_x
        if e:
            self._update_effect_bounds()
            e.velocity = 0
            e.overscroll = 0
            e.trigger_velocity_update()

    def _initialize_scroll_effects(self, touch, in_bar):
        # Initialize scroll effects for both axes if enabled.
        if self.do_scroll_x and self.effect_x and not in_bar:
            self._update_effect_bounds()
            self._effect_x_start_width = self.width
            self.effect_x.start(touch.x)

        if self.do_scroll_y and self.effect_y and not in_bar:
            self._update_effect_bounds()
            self._effect_y_start_height = self.height
            self.effect_y.start(touch.y)

    def _should_delegate_orthogonal(self, touch, parent_sv):
        # Check if touch movement is orthogonal to scroll direction.
        #
        # Only called for orthogonal configurations
        # (classification already verified).
        # Delegates when movement is in a direction child can't handle
        # but parent can.
        #
        # Args:
        #     touch: The touch event
        #     parent_sv: The parent ScrollView in the hierarchy
        #
        # Returns:
        #     bool: True if should delegate to parent
        abs_dx = abs(touch.dx)
        abs_dy = abs(touch.dy)

        # Only delegate if movement is SIGNIFICANTLY orthogonal
        # (2x threshold to avoid noise)
        # AND parent scrollview CAN scroll in that direction

        # Horizontal movement that child can't handle, but parent can
        if (
                abs_dx > abs_dy * 2
                and not self.do_scroll_x
                and parent_sv.do_scroll_x
        ):
            return True

        # Vertical movement that child can't handle, but parent can
        if (
                abs_dy > abs_dx * 2
                and not self.do_scroll_y
                and parent_sv.do_scroll_y
        ):
            return True

        return False

    def _should_delegate_mixed(self, touch, parent_sv, axis_config):
        # Check if touch should be delegated in mixed nested configurations.
        #
        # Only called for mixed configurations (classification already verified)
        # Handles parent-exclusive and child-exclusive axes.
        # Shared axes use the same boundary logic as parallel cases.
        #
        # Args:
        #     touch: The touch event
        #     parent_sv: The parent ScrollView in the hierarchy
        #     axis_config: Dictionary with axis configuration
        #
        # Returns:
        #     bool: True if should delegate to parent
        # Calculate total movement since touch_down
        total_dx = touch.x - touch.ox
        total_dy = touch.y - touch.oy
        abs_dx = abs(total_dx)
        abs_dy = abs(total_dy)

        # Need minimum movement to determine direction
        if abs_dx < self.scroll_distance and abs_dy < self.scroll_distance:
            return False

        # Determine dominant drag direction
        is_horizontal_dominant = abs_dx > abs_dy
        is_vertical_dominant = abs_dy > abs_dx

        # Check parent-exclusive axes (immediate delegation)
        outer_exclusive = axis_config.get("outer_exclusive", [])
        if is_horizontal_dominant and "x" in outer_exclusive:
            return True
        if is_vertical_dominant and "y" in outer_exclusive:
            return True

        # Check child-exclusive axes (no delegation, child continues)
        inner_exclusive = axis_config.get("inner_exclusive", [])
        if is_horizontal_dominant and "x" in inner_exclusive:
            return False
        if is_vertical_dominant and "y" in inner_exclusive:
            return False

        # Shared axes: use parallel boundary delegation logic
        # Call _should_delegate_parallel for shared axes
        # (same behavior as parallel cases)
        return self._should_delegate_parallel(touch, parent_sv)

    def _should_delegate_parallel(self, touch, parent_sv):
        # Check if scroll should lock at boundary for parallel scrolling.
        #
        # Only called for parallel configurations
        # (classification already verified).
        # Also used for SHARED AXES in MIXED cases.
        #
        # Implements web-style boundary locking based on delegation_mode:
        # Returns True if child scrollview should stop scrolling (locked state).
        # Does NOT cause delegation to parent - that only happens on NEW touch.
        #
        # Args:
        #     touch: The touch event
        #     parent_sv: The parent ScrollView in the hierarchy
        #
        # Returns:
        #     bool: True if should lock (stop scrolling but don't delegate)
        # NOTE: Cross-axis delegation (e.g., X gesture on Y-only ScrollView) is
        # handled earlier in _check_nested_delegation before dispatching to this
        # method. This method only handles boundary delegation for axes this
        # ScrollView CAN scroll.

        # Check parallel_delegation logic
        if not parent_sv.parallel_delegation:
            return False

        # Get per-ScrollView delegation mode (arbitrary depth support)
        sv_uid = self._get_uid()
        delegation_modes = touch.ud["nested"].get("delegation_modes", {})

        # For arbitrary depth: use per-ScrollView mode
        # (default UNLOCKED if not set)
        if delegation_modes:
            # We have per-ScrollView modes (arbitrary depth)
            # - use ours or default to UNLOCKED
            delegation_mode = delegation_modes.get(
                sv_uid, DelegationMode.UNLOCKED
            )
        else:
            # No per-ScrollView modes (2-level legacy) - use global mode
            delegation_mode = touch.ud["nested"].get(
                "delegation_mode", DelegationMode.UNLOCKED
            )

        # If not in delegation mode, never lock
        if delegation_mode == DelegationMode.UNLOCKED:
            return False

        # If already locked, keep it locked (child doesn't scroll,
        # stays locked for this gesture)
        if delegation_mode == DelegationMode.LOCKED:
            return True

        # delegation_mode == START_AT_BOUNDARY
        # Web-style: Started at boundary, now check movement direction
        primary_axis = self._get_primary_scroll_axis(touch)

        if primary_axis == "x" and self.do_scroll_x:  # Horizontal scrolling
            at_boundary = self._is_at_scroll_boundary("x")
            scrolling_beyond = self._is_scrolling_beyond_boundary("x", touch)

            # Check if we've moved away from the boundary into content
            if not at_boundary:
                # Moved away from boundary into content -
                # UNLOCK for this gesture
                sv_uid = self._get_uid()
                if "delegation_modes" in touch.ud["nested"]:
                    touch.ud["nested"]["delegation_modes"][
                        sv_uid
                    ] = DelegationMode.UNLOCKED
                touch.ud["nested"]["delegation_mode"] = DelegationMode.UNLOCKED
                return False

            # Still at boundary - check if trying to scroll beyond
            if scrolling_beyond:
                # Trying to overscroll - DELEGATE to parent (chain delegation)
                return True  # Delegate to parent

        elif primary_axis == "y" and self.do_scroll_y:  # Vertical scrolling
            at_boundary = self._is_at_scroll_boundary("y")
            scrolling_beyond = self._is_scrolling_beyond_boundary("y", touch)

            # Check if we've moved away from the boundary into content
            if not at_boundary:
                # Moved away from boundary into content, UNLOCK for this gesture
                sv_uid = self._get_uid()
                if "delegation_modes" in touch.ud["nested"]:
                    touch.ud["nested"]["delegation_modes"][
                        sv_uid
                    ] = DelegationMode.UNLOCKED
                touch.ud["nested"]["delegation_mode"] = DelegationMode.UNLOCKED
                return False

            # Still at boundary - check if trying to scroll beyond
            if scrolling_beyond:
                # Trying to overscroll - DELEGATE to parent (chain delegation)
                return True  # Delegate to parent

        return False

    def _process_scroll_axis_x(self, touch, not_in_bar):
        # Process X-axis scroll movement.
        if (
                touch.ud["sv.handled"]["x"]
                or not self.do_scroll_x
                or not self.effect_x
        ):
            return False

        width = self.width
        if touch.ud["in_bar_x"]:
            if self.hbar[1] != 1:
                dx = touch.dx / float(width - width * self.hbar[1])
                self.scroll_x = min(max(self.scroll_x + dx, 0.0), 1.0)
                self._trigger_update_from_scroll()
        elif not_in_bar:
            self.effect_x.update(touch.x)

        touch.ud["sv.handled"]["x"] = True
        touch.ud["sv.can_defocus"] = False
        return True

    def _process_scroll_axis_y(self, touch, not_in_bar):
        # Process Y-axis scroll movement.
        if (
                touch.ud["sv.handled"]["y"]
                or not self.do_scroll_y
                or not self.effect_y
        ):
            return False

        height = self.height
        if touch.ud["in_bar_y"] and self.vbar[1] != 1.0:
            dy = touch.dy / float(height - height * self.vbar[1])
            self.scroll_y = min(max(self.scroll_y + dy, 0.0), 1.0)
            self._trigger_update_from_scroll()
        elif not_in_bar:
            self.effect_y.update(touch.y)
            self._trigger_update_from_scroll()

        touch.ud["sv.handled"]["y"] = True
        touch.ud["sv.can_defocus"] = False
        return True

    def _stop_scroll_effects(self, touch, not_in_bar):
        if self.do_scroll_x and self.effect_x and not_in_bar:
            self.effect_x.stop(touch.x)

        if self.do_scroll_y and self.effect_y and not_in_bar:
            self.effect_y.stop(touch.y)

    def _finalize_scroll_for_cascade(self, touch):
        # Finalize scroll when cascading to parent,
        # without interfering with touch_up.
        #
        # This stops effects and schedules on_scroll_stop, but doesn't handle
        # click passthrough or other finalization that might interfere with
        # the normal on_touch_up flow to child widgets (like buttons).
        #
        # Called during on_touch_move when delegating from child to parent.
        # Clear our active touch reference (so we can accept new touches)
        self._touch = None

        # Get scroll state
        uid = self._get_uid()
        if uid not in touch.ud:
            return  # Never initialized, nothing to finalize

        ud = touch.ud[uid]

        # Safeguard: Check if already finalized
        if ud.get("_finalized_for_cascade"):
            return
        ud["_finalized_for_cascade"] = True

        # Stop scroll effects (prevent stuck scroll)
        not_in_bar = not touch.ud.get("in_bar_x", False) and not touch.ud.get(
            "in_bar_y", False
        )
        self._stop_scroll_effects(touch, not_in_bar)

        # Schedule velocity check for on_scroll_stop event
        if ud["mode"] == ScrollMode.SCROLL or ud.get("scroll_action"):
            if self._velocity_check_ev:
                self._velocity_check_ev.cancel()
            self._velocity_check_ev = Clock.schedule_interval(
                self._check_velocity_for_stop, 1 / 60.0
            )

        # CRITICAL: Remove our uid from touch.ud so on_touch_up will delegate
        # to children. This ensures buttons and other child widgets receive
        # their on_touch_up events even after we've cascaded scroll
        # handling to a parent
        del touch.ud[uid]

        # Clean up svavoid flag (but KEEP claimed_by_child flag -
        # it's needed for on_touch_up!)
        svavoid_key = self._get_uid("svavoid")
        if svavoid_key in touch.ud:
            del touch.ud[svavoid_key]

        # Update effect bounds
        ev = self._update_effect_bounds_ev
        if ev is None:
            ev = self._update_effect_bounds_ev = Clock.create_trigger(
                self._update_effect_bounds
            )
        ev()

        # CRITICAL: Trigger bar fade animation since _scroll_finalize
        # won't be called (our uid was deleted above,
        # so _scroll_finalize will early-return)
        # This schedules the 0.5s timer to fade bar from active to
        # inactive color
        self._trigger_update_from_scroll()

        # NOTE: We do NOT handle click passthrough here because the actual
        # on_touch_up will come later and needs to reach child widgets

    #
    # TOUCH USER DATA (touch.ud) KEY DOCUMENTATION
    # ============================================
    # This section documents all touch.ud keys used across ScrollView.
    #
    # KEY NAMING CONVENTIONS:
    # ----------------------
    #
    # PER-INSTANCE 'sv.' NAMESPACE:
    # -----------------------------
    # ScrollView uses 'sv.' prefixed keys via _get_uid() to create
    # instance-specific keys like 'sv.123', where 123 is the widget's
    # unique ID. Each ScrollView only checks its own keys - they do NOT
    # share or coordinate via these keys.
    #
    # Per-ScrollView Instance Keys:
    # - sv.<uid>: Primary state dict for this ScrollView instance
    #   Contains:
    #     {
    #       'mode': ScrollMode,   # State: UNKNOWN (detecting intent)
    #                            #   -> SCROLL (confirmed)
    #       'dx': float,         # accumulated absolute X movement
    #                            #   for detection
    #       'dy': float,         # accumulated absolute Y movement
    #                            #   for detection
    #       'scroll_action': bool,  # True if touch started in scrollbar
    #                            # (skips on_scroll_start dispatch)
    #       'frames': int,       # Clock.frames at touch start (timing)
    #       'can_defocus': bool, # Whether this touch can defocus
    #                            # focused widgets
    #     }
    #
    # - svavoid.<uid>: Flag indicating this ScrollView should avoid
    #   handling this touch
    #   Set when: Mouse wheel events are handled, or touch doesn't
    #   collide
    #   Purpose: Prevents double-processing of already-handled touches
    #
    #   Note: Each widget (ScrollView, DragBehavior) has its own
    #   UID-namespaced svavoid key. Widgets do NOT coordinate via svavoid
    #   - each checks only its own key.
    #
    # Cross-ScrollView Shared Keys:
    # - sv.handled: dict {'x': bool, 'y': bool}
    #   Purpose: Tracks which axes have been processed by a ScrollView
    #   Lifecycle: Set at start of on_touch_move, updated during scroll
    #   processing
    #
    # - sv.claimed_by_child: bool
    #   Set when: _change_touch_mode delegates touch to children and
    #   child grabs (timeout expired)
    #   Purpose: Signals a child widget (button, etc.) has claimed this
    #   touch. Prevents ANY ScrollView from processing scroll gestures.
    #   ScrollView becomes transparent, calling super() to propagate
    #   touch properly.
    #   Used in: _scroll_initialize, on_touch_move, on_touch_up
    #   Lifecycle: Set in _change_touch_mode when child grabs, cleared
    #   in on_touch_up
    #
    # - sv.can_defocus: bool
    #   Purpose: Controls whether FocusBehavior should defocus on this
    #   touch
    #   Set to False when: Touch results in actual scrolling
    #   Used in: on_touch_up to prevent defocus after scroll gestures
    #
    # NESTED SCROLLVIEW NAMESPACE
    # (Arbitrary Depth Support):
    # -------------------------------------------------------
    # - nested: dict - Nested ScrollView coordination state for
    #   arbitrary depth hierarchies
    #   Contains:
    #     {
    #       'hierarchy': ScrollViewHierarchy,    # Chain of nested
    #                                 # ScrollViews (2+ levels)
    #       'current_index': int,     # Index of ScrollView currently
    #                                 # handling touch
    #       'parallel_ancestor_index': int (optional),  # For
    #                                 # non-adjacent delegation
    #     }
    #   Purpose: Coordinates touches across multiple levels of nested
    #   ScrollViews
    #   Lifecycle: Built in outer's on_touch_down, updated during
    #   cascade in on_touch_move
    #
    # - sv_hierarchy_handled: bool
    #   Global flag indicating hierarchy coordination is complete
    #   Set when: Outer ScrollView completes on_touch_up coordination
    #   (line 2623)
    #   Purpose: Prevents multiple hierarchies from interfering with
    #   each other. This occurs in non-adjacent delegation when
    #   skip-level cascade creates a shallower hierarchy (e.g.,
    #   3-level becomes 2-level)
    #   Used in: on_touch_up to make all ScrollViews transparent after
    #   coordination done
    #   Lifecycle: Set once by first hierarchy to complete, checked by
    #   all ScrollViews
    #
    # GLOBAL SCROLLBAR FLAGS
    # (No Namespacing Required):
    # --------------------------------------------------
    # - in_bar_x: bool - Touch started on horizontal scroll bar
    # - in_bar_y: bool - Touch started on vertical scroll bar
    #   Purpose: Differentiates bar dragging from content scrolling
    #   Affects: Touch routing, effect handling, movement calculations,
    #   delegation
    #   Rationale: Scroll bars are positioned at widget edges and cannot
    #   overlap, so multiple ScrollViews can safely share these global
    #   flags

    # =========================================================================
    # MAIN TOUCH HANDLING METHODS (in lifecycle order)
    # =========================================================================

    def on_touch_down(self, touch):
        # SCROLLVIEW TOUCH HANDLING WITH AUTO-NESTED DETECTION
        # =====================================================
        # This method automatically detects nested ScrollView configurations and
        # sets up coordination.

        if not self.collide_point(*touch.pos):
            return False

        # Check if we already have an active nested ScrollView touch
        # This prevents multiple ScrollViews from scrolling simultaneously
        if self._nested_sv_active_touch is not None:
            touch.ud[self._get_uid("svavoid")] = True
            return False

        # NESTED DETECTION via touch event flow:
        # Parent widgets receive touches BEFORE children in Kivy.
        # - If 'nested' NOT in touch.ud: We're the FIRST ScrollView to see
        #   this touch (either outer or standalone - check for children below)
        # - If 'nested' IN touch.ud: We're an INNER ScrollView
        #   (parent already set up coordination - process as inner)

        # Check if touch is on OUR scrollbar -
        # if so, handle it directly (don't look for children)
        # This ensures outer scrollbar works even when there are inner SVs
        in_bar_x, in_bar_y = self._check_scroll_bounds(touch)
        if in_bar_x or in_bar_y:
            # Touch is on our scrollbar - handle it directly
            if self._scroll_initialize(touch):
                touch.grab(self)
                return True
            return False

        # We might be the outer ScrollView - check for child at touch position
        # Build full hierarchy (supports arbitrary depth nesting)
        hierarchy = self._build_hierarchy_recursive(touch)

        is_wheel = "button" in touch.profile and touch.button.startswith(
            "scroll"
        )

        if hierarchy:
            # We're the OUTER ScrollView with nested children
            # hierarchy.depth >= 2 (self + at least one child)

            # For backward compatibility with 2-level code, extract outer/inner
            outer_sv = hierarchy.outer
            inner_sv = hierarchy.inner  # Innermost (deepest) ScrollView

            # Get config for the LAST relationship
            # (inner with its immediate parent)
            config_type = hierarchy.get_classification(hierarchy.depth - 1)
            axis_config = hierarchy.get_axis_config(hierarchy.depth - 1)

            # Set up nested coordination with hierarchy
            touch.ud["nested"] = {
                "hierarchy": hierarchy,
                "current_index": hierarchy.touched_index,  # Start at innermost
                "config_type": config_type,
                # Classification of inner with its parent
                "delegation_mode": DelegationMode.UNLOCKED,
                # Will be set in _scroll_initialize
            }

            # Store axis_config for mixed configurations
            if axis_config:
                touch.ud["nested"]["axis_config"] = axis_config

            # WEB-STYLE WHEEL BEHAVIOR: Wheel scrolls ONLY innermost ScrollView
            # under cursor
            # No delegation through hierarchy - matches standard web browser UX
            if is_wheel:
                # Try only the innermost ScrollView
                if inner_sv._scroll_initialize(touch):
                    return True
                # Innermost couldn't handle it - don't try outer levels
                # This prevents scroll hijacking when inner reaches boundary
                return False

            # Non-wheel touch: Initialize scrolling on the innermost child
            # (handles coordinate transformation)
            result = self._initialize_nested_inner(touch, inner_sv)

            # After initialization, setup delegation modes for ALL ScrollViews
            # in hierarchy
            # (The innermost already had its mode set by
            # _setup_boundary_delegation in _scroll_initialize)
            # Now check the other levels in the hierarchy
            if result and "nested" in touch.ud:
                for i in range(
                        1, hierarchy.depth - 1
                ):  # Skip outer (0) and innermost (already done)
                    child_sv = hierarchy.scrollviews[i]
                    parent_sv = hierarchy.scrollviews[i - 1]

                    # Only check if parent has parallel_delegation enabled
                    if parent_sv.parallel_delegation:
                        # Check if child is at boundary in parallel directions
                        at_boundary_x = (
                                child_sv.do_scroll_x
                                and parent_sv.do_scroll_x
                                and child_sv._is_at_scroll_boundary("x")
                        )
                        at_boundary_y = (
                                child_sv.do_scroll_y
                                and parent_sv.do_scroll_y
                                and child_sv._is_at_scroll_boundary("y")
                        )

                        if at_boundary_x or at_boundary_y:
                            child_uid = child_sv._get_uid()
                            if "delegation_modes" not in touch.ud["nested"]:
                                touch.ud["nested"]["delegation_modes"] = {}
                            touch.ud["nested"]["delegation_modes"][
                                child_uid
                            ] = DelegationMode.START_AT_BOUNDARY

            return result

        # We're STANDALONE - no parent, no child ScrollView found
        if self._scroll_initialize(touch):
            # Only grab if we actually set up scroll state
            uid = self._get_uid()
            if uid in touch.ud:
                # We set up scroll state -
                # claim this touch to ensure only one active touch
                self._nested_sv_active_touch = touch
                touch.grab(self)
            return True
        return False

    def _scroll_initialize(self, touch):
        # This is the first phase of the scroll gesture, call from on_touch_down
        # it is used to determine if the scrollview should handle the touch
        # and to initialize the scroll effects
        if "nested" in touch.ud and "hierarchy" in touch.ud["nested"]:
            is_inner = touch.ud["nested"]["hierarchy"].inner == self

        # Check if this touch was claimed by a child widget (e.g., button)
        # If so, don't initialize scrolling
        if touch.ud.get("sv.claimed_by_child", False):
            return False

        # Skip collision check if we're the inner in a nested setup and parent
        # already validated (parent called us directly after finding us
        # with _find_child_scrollview_at_touch)
        skip_collision = (
                "nested" in touch.ud
                and "hierarchy" in touch.ud["nested"]
                and touch.ud["nested"]["hierarchy"].inner == self
        )

        if not skip_collision and not self.collide_point(*touch.pos):
            touch.ud[self._get_uid("svavoid")] = True
            return False

        if self.disabled:
            return True

        if self._touch:
            # Already handling a touch - reject this one to enforce single-touch
            # EXCEPT for mouse wheel events which are independent
            is_wheel = "button" in touch.profile and touch.button.startswith(
                "scroll"
            )
            if not is_wheel:
                # Check if stored touch is stale (completed but not cleaned up)
                # This happens when a touch completes via hierarchy handling but
                # this ScrollView wasn't the one that called _scroll_finalize
                # This is defensive. All _touch are cleared in scroll_finalize
                touch_is_stale = (
                        'sv_hierarchy_handled' in self._touch.ud  # Touch completed
                        and not any(
                    ref() is self for ref in (self._touch.grab_list or [])
                )  # We're not in grab list
                )

                if touch_is_stale:
                    # Clear the stale touch reference
                    self._touch = None
                    # Fall through to process the new touch
                else:
                    # Touch is still active - reject new touch
                    return False
            # For wheel events, continue even if we have an active touch

        if not (self.do_scroll_x or self.do_scroll_y):
            # Scrolling is disabled for both axes
            # Re-dispatch to child content so non-scroll interactions
            # (e.g., buttons) still work
            return self._simulate_touch_down(touch)

        # Handle mouse scrolling, only if the viewport size is bigger than the
        # scrollview size, and if the user allowed to do it
        vp = self._viewport
        if not vp:
            return True
        scroll_type = self.scroll_type
        ud = touch.ud

        # Check if touch is in scroll bars and set in_bar flags
        in_bar_x, in_bar_y = self._check_scroll_bounds(touch)
        in_bar = in_bar_x or in_bar_y
        ud["in_bar_x"] = in_bar_x
        ud["in_bar_y"] = in_bar_y

        if "button" in touch.profile and touch.button.startswith("scroll"):
            if self._handle_mouse_wheel_scroll(
                    touch.button, in_bar_x, in_bar_y
            ):
                touch.ud[self._get_uid("svavoid")] = True
                # Start velocity check for scroll stop after mouse wheel
                if self._velocity_check_ev:
                    self._velocity_check_ev.cancel()
                self._velocity_check_ev = Clock.schedule_interval(
                    self._check_velocity_for_stop, 1 / 60.0
                )
                return True
            return False

        if scroll_type == ["bars"] and not in_bar:
            return self._simulate_touch_down(touch)

        if in_bar:
            self._handle_scrollbar_jump(touch, in_bar_x, in_bar_y)
            # Dispatch on_scroll_start for scrollbar interactions
            self.dispatch("on_scroll_start")

        # No mouse scrolling, the user is going to drag the scrollview with
        # this touch.
        self._touch = touch
        # Set the touch state for this touch
        uid = self._get_uid()
        ud[uid] = {
            "mode": ScrollMode.UNKNOWN,
            "dx": 0,
            "dy": 0,
            "scroll_action": in_bar,
            "frames": Clock.frames,
            "can_defocus": True,  # Default: allow defocus unless scrolling
        }

        # Initialize scroll effects for content scrolling
        self._initialize_scroll_effects(touch, in_bar)

        # Configure boundary delegation for nested parallel scrolling
        self._setup_boundary_delegation(touch, in_bar)

        if not in_bar:
            Clock.schedule_once(
                self._change_touch_mode, self.scroll_timeout / 1000.0
            )
        return True

    def on_touch_move(self, touch):
        # SCROLLVIEW TOUCH HANDLING WITH ARBITRARY DEPTH HIERARCHY
        # =========================================================
        # Handles both standalone and nested ScrollView configurations.
        # For nested setups (2+ levels), uses hierarchy and current_index to
        # route touches to the correct ScrollView in the chain.

        # NESTED COORDINATION: Check if we have hierarchy data
        nested_data = touch.ud.get("nested")
        if nested_data and "hierarchy" in nested_data:
            hierarchy = nested_data["hierarchy"]
            current_index = nested_data["current_index"]

            # Only the OUTER ScrollView coordinates the hierarchy
            if hierarchy.outer is not self:
                return True  # Not our job to coordinate

            # We're the outer - we coordinate regardless of grab state
            # The hierarchy structure itself determines our role, not the grab

            # Get the ScrollView that should handle this touch
            current_sv = hierarchy.scrollviews[current_index]

            # Check if child widget claimed the touch - propagate to children
            if touch.ud.get("sv.claimed_by_child", False):
                return super(ScrollView, self).on_touch_move(touch)

            # Route to current handler
            if current_sv is self:
                # We (outer) are handling - process normally
                touch.ud["sv.handled"] = {"x": False, "y": False}
                return self._scroll_update(touch)
            else:
                # Another ScrollView in hierarchy is handling
                # Transform and delegate to it
                # Loop to handle cascading delegation up the chain
                while True:
                    current_sv = hierarchy.scrollviews[current_index]

                    touch.ud["sv.handled"] = {"x": False, "y": False}
                    touch.push()
                    touch.apply_transform_2d(current_sv.parent.to_widget)
                    result = current_sv._scroll_update(touch)
                    touch.pop()

                    # If current ScrollView accepted, we're done
                    if result:
                        return True

                    # Current ScrollView rejected - cascade up the chain
                    # The _should_delegate_* methods already handle boundary
                    # logic and return True/False.  If they return
                    # True (delegate), we should cascade regardless of mode
                    if current_index > 0:
                        # Move up to parent in chain
                        child_sv = current_sv

                        # Check if we should skip to a non-adjacent
                        # parallel ancestor
                        if "parallel_ancestor_index" in nested_data:
                            # Non-adjacent parallel delegation
                            # (e.g., V->H->V, skip H, go to outer V)
                            new_index = nested_data["parallel_ancestor_index"]
                            del nested_data[
                                "parallel_ancestor_index"
                            ]  # One-time use

                            # Finalize any intermediate ScrollViews that we're
                            # skipping over
                            # This ensures their touch state is cleaned up even
                            # though they never handled this touch
                            for skip_idx in range(
                                    current_index - 1, new_index, -1
                            ):
                                skipped_sv = hierarchy.scrollviews[skip_idx]
                                skipped_uid = skipped_sv._get_uid()
                                if skipped_uid in touch.ud:
                                    # This intermediate ScrollView has touch
                                    # data - clean it up
                                    touch.push()
                                    touch.apply_transform_2d(
                                        skipped_sv.parent.to_widget
                                    )
                                    skipped_sv._finalize_scroll_for_cascade(
                                        touch
                                    )
                                    touch.pop()

                            current_index = new_index
                        else:
                            # Standard delegation to immediate parent
                            current_index -= 1

                        nested_data["current_index"] = current_index
                        parent_sv = hierarchy.scrollviews[current_index]

                        # Initialize parent's scroll state if not already set up
                        parent_uid = parent_sv._get_uid()
                        if parent_uid not in touch.ud:
                            # Set to UNKNOWN so parent can detect scroll
                            # intent on next move
                            touch.ud[parent_uid] = {
                                "mode": ScrollMode.UNKNOWN,
                                "dx": 0,
                                "dy": 0,
                                "scroll_action": False,
                                "frames": 0,
                                "can_defocus": False,
                            }
                            # Transform touch to parent's space before
                            # initializing effects
                            touch.push()
                            touch.apply_transform_2d(parent_sv.parent.to_widget)
                            parent_sv._initialize_scroll_effects(
                                touch, in_bar=False
                            )
                            touch.pop()

                            parent_sv._touch = touch
                            parent_sv.dispatch("on_scroll_start")

                            # CRITICAL: Finalize child's scroll when cascading
                            # This stops effects AND schedules
                            # on_scroll_stop event
                            # But doesn't interfere with normal
                            # on_touch_up to buttons/widgets
                            touch.push()
                            touch.apply_transform_2d(child_sv.parent.to_widget)
                            child_sv._finalize_scroll_for_cascade(touch)
                            touch.pop()

                            # Extra safety: If child had _touch set but
                            # no scroll state, clear it to prevent
                            # blocking future touches
                            if child_sv._touch is touch:
                                child_sv._touch = None

                            # Parent just initialized - return True and let next
                            # touch_move handle it
                            # This prevents immediate cascading
                            # in the same event
                            return True

                        # Parent already initialized
                        continue
                    else:
                        # At outer level, and it rejected -
                        # shouldn't happen but return False
                        return False

        # STANDALONE: Standard single-touch processing
        # Only process our designated touch
        if self._touch is not touch:
            return self._delegate_to_children(touch, "on_touch_move")

        if touch.grab_current is not self:
            return True

        # Verify we have established scroll state for this touch
        if not any(
                isinstance(key, str) and key.startswith("sv.") for key in
                touch.ud
        ):
            return self._delegate_to_children(touch, "on_touch_move")

        # Process the scroll movement
        touch.ud["sv.handled"] = {"x": False, "y": False}
        return self._scroll_update(touch)

    def _scroll_update(self, touch):
        # Second phase of scroll gesture -
        # updates scroll effects during movement.
        #
        # Handles mode detection (unknown -> scroll), nested delegation checks,
        # and axis-specific scroll processing.

        # Early rejection checks
        if self._get_uid("svavoid") in touch.ud:
            return False
        if touch.ud.get("sv.claimed_by_child", False):
            # Child widget claimed touch - propagate through widget tree
            return super(ScrollView, self).on_touch_move(touch)

        # Allow this touch to defocus focused widgets (default behavior)
        touch.ud["sv.can_defocus"] = True

        # Verify we have scroll state for this touch
        uid = self._get_uid()
        if uid not in touch.ud:
            self._touch = False
            return self._scroll_initialize(touch)

        # Detect scroll intent (unknown -> scroll mode transition)
        ud = touch.ud[uid]

        if ud["mode"] == ScrollMode.UNKNOWN:
            if not self._detect_scroll_intent(touch, ud):
                return False

        # Process active scrolling
        if ud["mode"] == ScrollMode.SCROLL:
            not_in_bar = not touch.ud["in_bar_x"] and not touch.ud["in_bar_y"]

            # Check if inner should delegate to outer
            if self._check_nested_delegation(touch, not_in_bar):
                return (
                    False  # Delegate to outer (on_touch_move will switch mode)
                )

            # Process scroll movement for each axis
            self._process_scroll_axis_x(touch, not_in_bar)
            self._process_scroll_axis_y(touch, not_in_bar)
        return True

    def on_touch_up(self, touch):
        # SCROLLVIEW TOUCH HANDLING WITH ARBITRARY DEPTH HIERARCHY
        # ========================================================
        # Handles touch release for both standalone and nested
        # configurations. For nested setups (2+ levels), uses
        # current_index to finalize the correct ScrollView in the
        # chain.
        #
        # CRITICAL: Unschedule the timeout callback to prevent a race
        # condition. If the timeout fires during on_touch_up
        # processing, child widgets can grab the touch too late and
        # never receive on_touch_up (stuck button bug)
        if self._touch is touch:
            Clock.unschedule(self._change_touch_mode)

        # FAST PATH: If ANY nested hierarchy already completed on_touch_up,
        # skip processing. This prevents duplicate processing when
        # non-adjacent delegation creates multiple hierarchies for the
        # same touch (e.g., a 3-level cascade becomes a 2-level cascade).
        # The first hierarchy to complete sets this flag; all others
        # become transparent.
        if "sv_hierarchy_handled" in touch.ud:
            return False

        # NESTED COORDINATION: Check if we have hierarchy data
        nested_data = touch.ud.get("nested")
        if nested_data and "hierarchy" in nested_data:
            hierarchy = nested_data["hierarchy"]
            current_index = nested_data["current_index"]

            # Only the OUTER ScrollView coordinates
            if hierarchy.outer is not self:
                # Intermediate ScrollView - be transparent
                # Outer ScrollView will do the cleanup
                return False

            # Get the ScrollView that was handling this touch
            current_sv = hierarchy.scrollviews[current_index]

            # Check if current handler has scroll state
            current_uid = current_sv._get_uid()
            has_state = current_uid in touch.ud

            # Finalize the current handler
            if current_sv is self:
                # We (outer) were handling - finalize normally
                self._scroll_finalize(touch)
                self._handle_focus_behavior(touch, self._get_uid())
            else:
                # Another ScrollView in hierarchy was handling
                # Transform and finalize it
                current_uid = current_sv._get_uid()
                if current_uid in touch.ud:
                    touch.push()
                    touch.apply_transform_2d(current_sv.parent.to_widget)
                    current_sv._scroll_finalize(touch)
                    touch.pop()
                    self._handle_focus_behavior(touch, current_uid)

            # Clear the nested ScrollView active touch (outer only)
            if self._nested_sv_active_touch is touch:
                self._nested_sv_active_touch = None

            # Release grab
            if touch.grab_current is self:
                touch.ungrab(self)

            # Mark that ScrollView hierarchy handling is complete
            touch.ud["sv_hierarchy_handled"] = True

            # Proactively clear _touch for ALL ScrollViews in hierarchy
            # This prevents stale touch references when intermediate ScrollViews
            # had _touch set but didn't call _scroll_finalize themselves
            for sv in hierarchy.scrollviews:
                if sv._touch is touch:
                    sv._touch = None

            # CRITICAL: Check if a child widget (button) claimed this touch
            # We check AFTER cleanup so hierarchy state is properly finalized
            claimed_by_child = touch.ud.get("sv.claimed_by_child", False)

            # If a child claimed the touch, propagate through widget tree by
            # calling super()
            # This ensures intermediate parent widgets receive on_touch_up
            # events
            # Kivy's grab mechanism will also dispatch to grabbed widgets
            # automatically
            if claimed_by_child:
                return super(ScrollView, self).on_touch_up(touch)

            # No child claimed - ScrollView handled the gesture
            # Return False to allow other widgets to process if needed
            return False

        # STANDALONE: Handle touch release
        uid_key = self._get_uid()

        # Touch was handled by this ScrollView
        if uid_key in touch.ud:
            self._scroll_finalize(touch)

            # Clear the nested ScrollView active touch (standalone case)
            if self._nested_sv_active_touch is touch:
                self._nested_sv_active_touch = None

            # Release grab if we still have it (handlers may have released it)
            gl = touch.grab_list or []
            if any(w() is self for w in gl):
                touch.ungrab(self)

            self._handle_focus_behavior(touch, uid_key)

            return True

        # Touch not handled by us - delegate to children
        uid = self._get_uid("svavoid")
        if self._touch is not touch and uid not in touch.ud:
            return self._delegate_to_children(touch, "on_touch_up")

        # Final fallback: finalize and ungrab
        if self._scroll_finalize(touch):
            touch.ungrab(self)
            self._handle_focus_behavior(touch, uid_key)

            return True

    def _scroll_finalize(self, touch):
        # SCROLL COMPLETION AND FINAL CLEANUP, called from on_touch_up
        # This method handles the end of scroll gestures and performs cleanup.

        self._touch = None  # Clear our active touch reference

        # Early exit if this ScrollView never handled this touch:
        # Case 1: svavoid is set - we explicitly avoided this touch
        # (e.g., outside bounds, wheel handled)
        # Case 2: UID not in touch.ud - we never initialized scroll state
        # (touch went to child widget)
        if (
                self._get_uid("svavoid") in touch.ud
                or self._get_uid() not in touch.ud
        ):
            return False

        uid = self._get_uid()
        ud = touch.ud[uid]

        # Determine if this was a scroll bar interaction
        not_in_bar = not touch.ud["in_bar_x"] and not touch.ud["in_bar_y"]
        # Stop scroll effects if they were active (not for bar interactions)
        self._stop_scroll_effects(touch, not_in_bar)

        # Start checking for velocity-based stop if this was a scroll
        # this is used to dispatch the on_scroll_stop event
        if ud["mode"] == ScrollMode.SCROLL or ud["scroll_action"]:
            if self._velocity_check_ev:
                self._velocity_check_ev.cancel()
            self._velocity_check_ev = Clock.schedule_interval(
                self._check_velocity_for_stop, 1 / 60.0
            )

        # CLICK PASSTHROUGH LOGIC
        # If the gesture never transitioned from UNKNOWN to SCROLL mode,
        # it means the user made a tap/click rather than a scroll gesture.
        # We need to simulate the click for child widgets to handle.
        if ud["mode"] == ScrollMode.UNKNOWN:
            # Only simulate click if no scroll action occurred
            # (e.g., no scroll bar interaction or dragging)
            if not ud["scroll_action"]:
                self._simulate_touch_down(
                    touch
                )  # Let children handle the "click"
            # Schedule delayed touch up to complete the click simulation
            Clock.schedule_once(partial(self._do_touch_up, touch), 0.2)

        # Update effect bounds after scroll completion
        ev = self._update_effect_bounds_ev
        if ev is None:
            ev = self._update_effect_bounds_ev = Clock.create_trigger(
                self._update_effect_bounds
            )
        ev()

        # Always accept mouse wheel events
        if "button" in touch.profile and touch.button.startswith("scroll"):
            return True

        # Return whether we had any involvement with this touch
        return self._get_uid() in touch.ud

    def scroll_to(self, widget, padding=10, animate=True):
        """Scrolls the viewport to ensure that the given widget is visible,
        optionally with padding and animation. If animate is True (the
        default), then the default animation parameters will be used.
        Otherwise, it should be a dict containing arguments to pass to
        :class:`~kivy.animation.Animation` constructor.

        .. versionadded:: 1.9.1
        """
        if not self.parent:
            return

        # if _viewport is layout and has pending operation, reschedule
        if hasattr(self._viewport, "do_layout"):
            if self._viewport._trigger_layout.is_triggered:
                Clock.schedule_once(
                    lambda *dt: self.scroll_to(widget, padding, animate)
                )
                return

        if isinstance(padding, (int, float)):
            padding = (padding, padding)

        pos = self.parent.to_widget(*widget.to_window(*widget.pos))
        cor = self.parent.to_widget(*widget.to_window(widget.right, widget.top))

        dx = dy = 0

        if pos[1] < self.y:
            dy = self.y - pos[1] + dp(padding[1])
        elif cor[1] > self.top:
            dy = self.top - cor[1] - dp(padding[1])

        if pos[0] < self.x:
            dx = self.x - pos[0] + dp(padding[0])
        elif cor[0] > self.right:
            dx = self.right - cor[0] - dp(padding[0])

        dsx, dsy = self.convert_distance_to_scroll(dx, dy)
        sxp = min(1, max(0, self.scroll_x - dsx))
        syp = min(1, max(0, self.scroll_y - dsy))

        # Stop any existing motion before starting new animation
        if self.effect_x:
            self.effect_x.halt()
        if self.effect_y:
            self.effect_y.halt()

        if animate:
            if animate is True:
                animate = {"d": 0.2, "t": "out_quad"}
            Animation.stop_all(self, "scroll_x", "scroll_y")
            Animation(scroll_x=sxp, scroll_y=syp, **animate).start(self)
        else:
            self.scroll_x = sxp
            self.scroll_y = syp

    def convert_distance_to_scroll(self, dx, dy):
        """Convert a distance in pixels to a scroll distance, depending on the
        content size and the scrollview size.

        The result will be a tuple of scroll distance that can be added to
        :data:`scroll_x` and :data:`scroll_y`
        """
        if not self._viewport:
            return 0, 0
        vp = self._viewport
        if vp.width > self.width:
            sw = vp.width - self.width
            sx = dx / float(sw)
        else:
            sx = 0
        if vp.height > self.height:
            sh = vp.height - self.height
            sy = dy / float(sh)
        else:
            sy = 1
        return sx, sy

    def update_from_scroll(self, *largs):
        """Force the reposition of the content, according to current value of
        :attr:`scroll_x` and :attr:`scroll_y`.

        This method is automatically called when one of the :attr:`scroll_x`,
        :attr:`scroll_y`, :attr:`pos` or :attr:`size` properties change, or
        if the size of the content changes.
        """
        if not self._viewport:
            self.g_translate.xy = self.pos
            return
        vp = self._viewport

        # update from size_hint
        if vp.size_hint_x is not None:
            w = vp.size_hint_x * self.width
            if vp.size_hint_min_x is not None:
                w = max(w, vp.size_hint_min_x)
            if vp.size_hint_max_x is not None:
                w = min(w, vp.size_hint_max_x)
            vp.width = w

        if vp.size_hint_y is not None:
            h = vp.size_hint_y * self.height
            if vp.size_hint_min_y is not None:
                h = max(h, vp.size_hint_min_y)
            if vp.size_hint_max_y is not None:
                h = min(h, vp.size_hint_max_y)
            vp.height = h

        if vp.width > self.width or self.always_overscroll:
            sw = vp.width - self.width
            x = self.x - self.scroll_x * sw
        else:
            x = self.x

        if vp.height > self.height or self.always_overscroll:
            sh = vp.height - self.height
            y = self.y - self.scroll_y * sh
        else:
            y = self.top - vp.height

        # from 1.8.0, we now use a matrix by default, instead of moving the
        # widget position behind. We set it here, but it will be a no-op most
        # of the time.
        vp.pos = 0, 0
        self.g_translate.xy = x, y

        # New in 1.2.0, show bar when scrolling happens and (changed in 1.9.0)
        # fade to bar_inactive_color when no scroll is happening.
        ev = self._bind_inactive_bar_color_ev
        if ev is None:
            ev = self._bind_inactive_bar_color_ev = Clock.create_trigger(
                self._bind_inactive_bar_color, 0.5
            )
        self.funbind("bar_inactive_color", self._change_bar_color)
        Animation.stop_all(self, "_bar_color")
        self.fbind("bar_color", self._change_bar_color)
        self._bar_color = self.bar_color
        ev()

    def _bind_inactive_bar_color(self, *args):
        self.funbind("bar_color", self._change_bar_color)
        self.fbind("bar_inactive_color", self._change_bar_color)
        Animation(
            _bar_color=self.bar_inactive_color, d=0.5, t="out_quart"
        ).start(self)

    def _change_bar_color(self, inst, value):
        self._bar_color = value

    def add_widget(self, widget, *args, **kwargs):
        if self._viewport:
            raise Exception("ScrollView accept only one widget")
        canvas = self.canvas
        self.canvas = self.canvas_viewport
        super(ScrollView, self).add_widget(widget, *args, **kwargs)
        self.canvas = canvas
        self._viewport = widget
        widget.bind(
            size=self._trigger_update_from_scroll,
            size_hint_min=self._trigger_update_from_scroll,
        )
        self._trigger_update_from_scroll()

    def remove_widget(self, widget, *args, **kwargs):
        canvas = self.canvas
        self.canvas = self.canvas_viewport
        super(ScrollView, self).remove_widget(widget, *args, **kwargs)
        self.canvas = canvas
        if widget is self._viewport:
            self._viewport = None

    def _on_scroll_pos_changed(self, instance, value):
        # Called when scroll_x or scroll_y changes.
        # Dispatches on_scroll_move event to notify listeners of
        # actual scroll position changes.
        self.dispatch("on_scroll_move")

    def _check_position_stable(self, dt):
        # Check if scroll position has stabilized. Used to dispatch the
        # on_scroll_stop event.
        current_pos = (self.scroll_x, self.scroll_y)

        if self._last_scroll_pos is None:
            self._last_scroll_pos = current_pos
            self._stable_frames = 0
            return True

        # Check if position changed
        pos_changed = not (
                isclose(current_pos[0], self._last_scroll_pos[0])
                and isclose(current_pos[1], self._last_scroll_pos[1])
        )
        if not pos_changed:
            # Position hasn't changed - increment stable counter
            self._stable_frames += 1

            # Require 3 consecutive stable frames before dispatching stop
            if self._stable_frames >= 3:
                self.dispatch("on_scroll_stop")
                # Clean up
                if self._position_check_ev:
                    self._position_check_ev.cancel()
                self._position_check_ev = None
                self._last_scroll_pos = None
                self._stable_frames = 0
                return False
        else:
            # Position still changing - reset counter
            self._last_scroll_pos = current_pos
            self._stable_frames = 0

        return True

    def _check_velocity_for_stop(self, dt):
        # Used to dispatch the on_scroll_stop event.
        # Checks if velocity is zero. After detecting zero velocity,
        # we verify the position has stabilized before dispatching.

        # Get current velocities
        vel_x = self.effect_x.velocity if self.effect_x else 0
        vel_y = self.effect_y.velocity if self.effect_y else 0

        # Use small threshold for velocity check
        if isclose(vel_x, 0.0) and isclose(vel_y, 0.0):
            # Velocity is zero - now check position stability
            if self._velocity_check_ev:
                self._velocity_check_ev.cancel()
            self._velocity_check_ev = None

            # Start position stability check
            self._last_scroll_pos = None
            self._stable_frames = 0
            if self._position_check_ev:
                self._position_check_ev.cancel()
            self._position_check_ev = Clock.schedule_interval(
                self._check_position_stable, 0
            )
            return False

        return True

    def _get_uid(self, prefix="sv"):
        # UNIQUE IDENTIFIER GENERATOR FOR TOUCH.UD KEYS
        # ==============================================
        # Generates unique keys for touch.ud (user data) dictionary based on
        # this ScrollView's unique ID.
        #
        # USAGE PATTERNS:
        # - _get_uid() -> 'sv.123' (primary state key)
        # - _get_uid('svavoid') -> 'svavoid.123' (avoid processing flag)
        #
        # This ensures each ScrollView instance has its own namespace in
        # touch.ud, preventing conflicts in nested scenarios.
        return "{0}.{1}".format(prefix, self.uid)

    def _get_debug_name(self):
        # Helper method for debug output - identifies ScrollView by scroll axes
        axes = []
        if self.do_scroll_x:
            axes.append("X")
        if self.do_scroll_y:
            axes.append("Y")
        axis_str = "+".join(axes) if axes else "NONE"
        return f"SV[{axis_str}:{self.uid}]"

    def _change_touch_mode(self, *largs):
        # SCROLL TIMEOUT HANDLER - GESTURE DETECTION TIMEOUT
        # ==================================================
        # This method is called when the scroll_timeout expires without the
        # touch traveling the minimum scroll_distance. It transitions from
        # scroll detection mode to normal widget interaction mode by handing-off
        # the touch to child widgets.
        if not self._touch:
            return

        uid = self._get_uid()
        touch = self._touch
        if uid not in touch.ud:
            self._touch = False
            return

        ud = touch.ud[uid]
        # Only proceed if we're still in gesture detection mode
        if ud["mode"] != ScrollMode.UNKNOWN or ud["scroll_action"]:
            return

        # SLOW DEVICE PROTECTION:
        # On very slow devices, we need at least 3 frames to accumulate
        # velocity data. Otherwise, scroll effects might not work properly.
        # This addresses issues #1464 and #1499 for low-performance devices.
        if self.slow_device_support:
            diff_frames = Clock.frames - ud["frames"]
            if diff_frames < 3:
                Clock.schedule_once(self._change_touch_mode, 0)
                return

        # CLEANUP AND HANDOFF:
        # Cancel any scroll effects that may have started
        if self.do_scroll_x and self.effect_x:
            self.effect_x.cancel()
        if self.do_scroll_y and self.effect_y:
            self.effect_y.cancel()

        # Store hierarchy info
        has_hierarchy = (
                "nested" in touch.ud and "hierarchy" in touch.ud["nested"]
        )
        if has_hierarchy:
            hierarchy = touch.ud["nested"]["hierarchy"]

        # Cancel any scroll effects that may have started
        if self.do_scroll_x and self.effect_x:
            self.effect_x.cancel()
        if self.do_scroll_y and self.effect_y:
            self.effect_y.cancel()

        touch.ungrab(self)
        self._touch = None

        # CONTROLLED HANDOFF TO CHILD WIDGETS:
        # Transform touch coordinates and re-dispatch to children
        # This allows buttons, sliders, etc. to handle the touch normally
        # NOTE: Do NOT schedule _do_touch_up here, this is a live touch handoff,
        # not a synthetic click. The user is still holding their finger down.
        touch.push()
        touch.apply_transform_2d(self.to_widget)
        touch.apply_transform_2d(self.to_parent)

        child_grabbed = self._simulate_touch_down(touch)

        touch.pop()

        if child_grabbed:
            # A child widget grabbed the touch - hand it off completely
            uid = self._get_uid()
            if uid in touch.ud:
                del touch.ud[uid]

            # Set flag to prevent re-initialization, this touch belongs to child
            touch.ud["sv.claimed_by_child"] = True

            # Clear the nested ScrollView active touch since we're handing off
            if has_hierarchy:
                if hierarchy.scrollviews[0]._nested_sv_active_touch is touch:
                    hierarchy.scrollviews[0]._nested_sv_active_touch = None
            else:
                # Standalone case: clear our own active touch
                if self._nested_sv_active_touch is touch:
                    self._nested_sv_active_touch = None
        else:
            # No child grabbed it (e.g., user is on empty space) -
            # transition to SCROLL mode so the user can begin scrolling without
            # restarting the gesture
            uid = self._get_uid()
            if uid in touch.ud:
                touch.ud[uid]["mode"] = ScrollMode.SCROLL
                # Dispatch on_scroll_start since we're now ready to scroll
                self.dispatch("on_scroll_start")
                # Re-grab since we ungrabbed above
                touch.grab(self)
                self._touch = touch

    def _do_touch_up(self, touch, *largs):
        # Complete touch lifecycle by sending touch_up to all widgets that
        # grabbed this touch.
        # Ensures proper cleanup for buttons/widgets that were touched
        # during scroll gestures touch is in window coords
        self._delegate_touch_up_to_children_widget_coords(touch)
        # don't forget about grab event!
        for x in touch.grab_list[:]:
            touch.grab_list.remove(x)
            x = x()
            if not x:
                continue
            touch.grab_current = x
            # touch is in window coords
            self._delegate_touch_up_to_children_widget_coords(touch)
        touch.grab_current = None

    def on_scroll_start(self):
        """Event fired when a scroll gesture starts.

        This event is dispatched when scrolling begins, regardless of the input
        method (touch, mouse wheel, or programmatic). It fires once per scroll
        gesture when the ScrollView determines that scrolling should commence.

        For touch/content scrolling, this fires after the touch has moved beyond
        the scroll_distance threshold. For scrollbar interactions, it fires when
        the scrollbar is initially grabbed. For mouse wheel scrolling, it fires
        on the first scroll wheel event.

        .. versionchanged:: NEXT_VERSION
            Removed touch parameter. Use on_touch_down/move/up for
            touch-specific handling.
        """
        pass

    def on_scroll_move(self):
        """Event fired when the scroll position changes.

        This event is dispatched whenever the scroll_x or scroll_y properties
        change during an active scroll gesture. It provides a unified way to
        track scrolling regardless of input method.
        (touch, mouse wheel, scrollbar, or programmatic
        scroll_x/scroll_y changes).

        This event fires continuously during scrolling and is useful for
        implementing scroll-based animations, progress indicators, or parallax
        effects.

        .. versionchanged:: NEXT_VERSION
            Removed touch parameter. Use on_touch_down/move/up for touch-specific
            handling. Now fires for all scroll_x/scroll_y changes including
            programmatic updates.
        """
        pass

    def on_scroll_stop(self):
        """Event fired when scrolling motion stops.

        This event is dispatched when the scrolling motion has completely
        stopped.  Fires when both velocity reaches zero and scroll position
        stabilizes for 3 consecutive frames.

        This event is useful for triggering actions after scrolling completes,
        such as loading more content, snapping to grid positions, or updating
        UI state.

        .. versionchanged:: NEXT_VERSION
            Removed touch parameter. Use on_touch_down/move/up for
            touch-specific handling.
        """
        pass


if __name__ == "__main__":
    from kivy.app import App

    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.button import Button


    class ScrollViewApp(App):

        def build(self):
            layout1 = GridLayout(cols=4, spacing=10, size_hint=(None, None))
            layout1.bind(
                minimum_height=layout1.setter("height"),
                minimum_width=layout1.setter("width"),
            )
            for i in range(40):
                btn = Button(
                    text=str(i), size_hint=(None, None), size=(200, 100)
                )
                layout1.add_widget(btn)
            scrollview1 = ScrollView(bar_width="2dp", smooth_scroll_end=10)
            scrollview1.add_widget(layout1)

            layout2 = GridLayout(cols=4, spacing=10, size_hint=(None, None))
            layout2.bind(
                minimum_height=layout2.setter("height"),
                minimum_width=layout2.setter("width"),
            )
            for i in range(40):
                btn = Button(
                    text=str(i), size_hint=(None, None), size=(200, 100)
                )
                layout2.add_widget(btn)
            scrollview2 = ScrollView(
                scroll_type=["bars"], bar_width="9dp", scroll_wheel_distance=100
            )
            scrollview2.add_widget(layout2)

            root = GridLayout(cols=2)
            root.add_widget(scrollview1)
            root.add_widget(scrollview2)
            return root


    ScrollViewApp().run()
