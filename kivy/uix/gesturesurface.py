'''
Gesture Surface
===============

.. versionadded::
    1.9.0

.. warning::

    This is experimental and subject to change as long as this warning notice
    is present.

See :file:`kivy/examples/demo/multistroke/main.py` for a complete application
example.
'''
__all__ = ('GestureSurface', 'GestureContainer')

from random import random
from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.vector import Vector
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Line, Rectangle
from kivy.properties import (NumericProperty, BooleanProperty,
                             DictProperty, ListProperty)
from colorsys import hsv_to_rgb

# Clock undershoot margin, FIXME: this is probably too high?
UNDERSHOOT_MARGIN = 0.1


class GestureContainer(EventDispatcher):
    '''Container object that stores information about a gesture. It has
    various properties that are updated by `GestureSurface` as drawing
    progresses.

    :Arguments:
        `touch`
            Touch object (as received by on_touch_down) used to initialize
            the gesture container. Required.

    :Properties:
        `active`
            Set to False once the gesture is complete (meets
            `max_stroke` setting or `GestureSurface.temporal_window`)

            :attr:`active` is a
            :class:`~kivy.properties.BooleanProperty`

        `active_strokes`
            Number of strokes currently active in the gesture, ie
            concurrent touches associated with this gesture.

            :attr:`active_strokes` is a
            :class:`~kivy.properties.NumericProperty`

        `max_strokes`
            Max number of strokes allowed in the gesture. This
            is set by `GestureSurface.max_strokes` but can
            be overridden for example from `on_gesture_start`.

            :attr:`max_strokes` is a
            :class:`~kivy.properties.NumericProperty`

        `was_merged`
            Indicates that this gesture has been merged with another
            gesture and should be considered discarded.

            :attr:`was_merged` is a
            :class:`~kivy.properties.BooleanProperty`

        `bbox`
            Dictionary with keys minx, miny, maxx, maxy. Represents the size
            of the gesture bounding box.

            :attr:`bbox` is a
            :class:`~kivy.properties.DictProperty`

        `width`
            Represents the width of the gesture.

            :attr:`width` is a
            :class:`~kivy.properties.NumericProperty`

        `height`
            Represents the height of the gesture.

            :attr:`height` is a
            :class:`~kivy.properties.NumericProperty`
    '''
    active = BooleanProperty(True)
    active_strokes = NumericProperty(0)
    max_strokes = NumericProperty(0)
    was_merged = BooleanProperty(False)
    bbox = DictProperty({'minx': float('inf'), 'miny': float('inf'),
                         'maxx': float('-inf'), 'maxy': float('-inf')})
    width = NumericProperty(0)
    height = NumericProperty(0)

    def __init__(self, touch, **kwargs):
        # The color is applied to all canvas items of this gesture
        self.color = kwargs.pop('color', [1., 1., 1.])

        super(GestureContainer, self).__init__(**kwargs)

        # This is the touch.uid of the oldest touch represented
        self.id = str(touch.uid)

        # Store various timestamps for decision making
        self._create_time = Clock.get_time()
        self._update_time = None
        self._cleanup_time = None
        self._cache_time = 0

        # We can cache the candidate here to save zip()/Vector instantiation
        self._vectors = None

        # Key is touch.uid; value is a kivy.graphics.Line(); it's used even
        # if line_width is 0 (i.e. not actually drawn anywhere)
        self._strokes = {}

        # Make sure the bbox is up to date with the first touch position
        self.update_bbox(touch)

    def get_vectors(self, **kwargs):
        '''Return strokes in a format that is acceptable for
        `kivy.multistroke.Recognizer` as a gesture candidate or template. The
        result is cached automatically; the cache is invalidated at the start
        and end of a stroke and if `update_bbox` is called. If you are going
        to analyze a gesture mid-stroke, you may need to set the `no_cache`
        argument to True.'''
        if self._cache_time == self._update_time and \
                not kwargs.get('no_cache'):
            return self._vectors

        vecs = []
        append = vecs.append
        for tuid, l in self._strokes.items():
            lpts = l.points
            append([Vector(*pts) for pts in zip(lpts[::2], lpts[1::2])])

        self._vectors = vecs
        self._cache_time = self._update_time
        return vecs

    def handles(self, touch):
        '''Returns True if this container handles the given touch'''
        if not self.active:
            return False
        return str(touch.uid) in self._strokes

    def accept_stroke(self, count=1):
        '''Returns True if this container can accept `count` new strokes'''
        if not self.max_strokes:
            return True
        return len(self._strokes) + count <= self.max_strokes

    def update_bbox(self, touch):
        '''Update gesture bbox from a touch coordinate'''
        x, y = touch.x, touch.y
        bb = self.bbox
        if x < bb['minx']:
            bb['minx'] = x
        if y < bb['miny']:
            bb['miny'] = y
        if x > bb['maxx']:
            bb['maxx'] = x
        if y > bb['maxy']:
            bb['maxy'] = y
        self.width = bb['maxx'] - bb['minx']
        self.height = bb['maxy'] - bb['miny']
        self._update_time = Clock.get_time()

    def add_stroke(self, touch, line):
        '''Associate a list of points with a touch.uid; the line itself is
        created by the caller, but subsequent move/up events look it
        up via us. This is done to avoid problems during merge.'''
        self._update_time = Clock.get_time()
        self._strokes[str(touch.uid)] = line
        self.active_strokes += 1

    def complete_stroke(self):
        '''Called on touch up events to keep track of how many strokes
        are active in the gesture (we only want to dispatch event when
        the *last* stroke in the gesture is released)'''
        self._update_time = Clock.get_time()
        self.active_strokes -= 1

    def single_points_test(self):
        '''Returns True if the gesture consists only of single-point strokes,
        we must discard it in this case, or an exception will be raised'''
        for tuid, l in self._strokes.items():
            if len(l.points) > 2:
                return False
        return True


class GestureSurface(FloatLayout):
    '''Simple gesture surface to track/draw touch movements. Typically used
    to gather user input suitable for :class:`kivy.multistroke.Recognizer`.

    :Properties:
        `temporal_window`
            Time to wait from the last touch_up event before attempting
            to recognize the gesture. If you set this to 0, the
            `on_gesture_complete` event is not fired unless the
            :attr:`max_strokes` condition is met.

            :attr:`temporal_window` is a
            :class:`~kivy.properties.NumericProperty` and defaults to 2.0

        `max_strokes`
            Max number of strokes in a single gesture; if this is reached,
            recognition will start immediately on the final touch_up event.
            If this is set to 0, the `on_gesture_complete` event is not
            fired unless the :attr:`temporal_window` expires.

            :attr:`max_strokes` is a
            :class:`~kivy.properties.NumericProperty` and defaults to 2.0

        `bbox_margin`
            Bounding box margin for detecting gesture collisions, in
            pixels.

            :attr:`bbox_margin` is a
            :class:`~kivy.properties.NumericProperty` and defaults to 30

        `draw_timeout`
            Number of seconds to keep lines/bbox on canvas after the
            `on_gesture_complete` event is fired. If this is set to 0,
            gestures are immediately removed from the surface when
            complete.

            :attr:`draw_timeout` is a
            :class:`~kivy.properties.NumericProperty` and defaults to 3.0

        `color`
            Color used to draw the gesture, in RGB. This option does not
            have an effect if :attr:`use_random_color` is True.

            :attr:`draw_timeout` is a
            :class:`~kivy.properties.ListProperty` and defaults to
            [1, 1, 1] (white)

        `use_random_color`
            Set to True to pick a random color for each gesture, if you do
            this then `color` is ignored. Defaults to False.

            :attr:`use_random_color` is a
            :class:`~kivy.properties.BooleanProperty` and defaults to False

        `line_width`
            Line width used for tracing touches on the surface. Set to 0
            if you only want to detect gestures without drawing anything.
            If you use 1.0, OpenGL GL_LINE is used for drawing; values > 1
            will use an internal drawing method based on triangles (less
            efficient), see :mod:`kivy.graphics`.

            :attr:`line_width` is a
            :class:`~kivy.properties.NumericProperty` and defaults to 2

        `draw_bbox`
            Set to True if you want to draw bounding box behind gestures.
            This only works if `line_width` >= 1. Default is False.

            :attr:`draw_bbox` is a
            :class:`~kivy.properties.BooleanProperty` and defaults to True

        `bbox_alpha`
            Opacity for bounding box if `draw_bbox` is True. Default 0.1

            :attr:`bbox_alpha` is a
            :class:`~kivy.properties.NumericProperty` and defaults to 0.1

    :Events:
        `on_gesture_start` :class:`GestureContainer`
            Fired when a new gesture is initiated on the surface, i.e. the
            first on_touch_down that does not collide with an existing
            gesture on the surface.

        `on_gesture_extend` :class:`GestureContainer`
            Fired when a touch_down event occurs within an existing gesture.

        `on_gesture_merge` :class:`GestureContainer`, :class:`GestureContainer`
            Fired when two gestures collide and get merged to one gesture.
            The first argument is the gesture that has been merged (no longer
            valid); the second is the combined (resulting) gesture.

        `on_gesture_complete` :class:`GestureContainer`
            Fired when a set of strokes is considered a complete gesture,
            this happens when `temporal_window` expires or `max_strokes`
            is reached. Typically you will bind to this event and use
            the provided `GestureContainer` get_vectors() method to
            match against your gesture database.

        `on_gesture_cleanup` :class:`GestureContainer`
            Fired `draw_timeout` seconds after `on_gesture_complete`,
            The gesture will be removed from the canvas (if line_width > 0 or
            draw_bbox is True) and the internal gesture list before this.

        `on_gesture_discard` :class:`GestureContainer`
            Fired when a gesture does not meet the minimum size requirements
            for recognition (width/height < 5, or consists only of single-
            point strokes).
    '''

    temporal_window = NumericProperty(2.0)
    draw_timeout = NumericProperty(3.0)
    max_strokes = NumericProperty(4)
    bbox_margin = NumericProperty(30)

    line_width = NumericProperty(2)
    color = ListProperty([1., 1., 1.])
    use_random_color = BooleanProperty(False)
    draw_bbox = BooleanProperty(False)
    bbox_alpha = NumericProperty(0.1)

    def __init__(self, **kwargs):
        super(GestureSurface, self).__init__(**kwargs)
        # A list of GestureContainer objects (all gestures on the surface)
        self._gestures = []
        self.register_event_type('on_gesture_start')
        self.register_event_type('on_gesture_extend')
        self.register_event_type('on_gesture_merge')
        self.register_event_type('on_gesture_complete')
        self.register_event_type('on_gesture_cleanup')
        self.register_event_type('on_gesture_discard')

# -----------------------------------------------------------------------------
# Touch Events
# -----------------------------------------------------------------------------
    def on_touch_down(self, touch):
        '''When a new touch is registered, the first thing we do is to test if
        it collides with the bounding box of another known gesture. If so, it
        is assumed to be part of that gesture.
        '''
        # If the touch originates outside the surface, ignore it.
        if not self.collide_point(touch.x, touch.y):
            return

        touch.grab(self)

        # Add the stroke to existing gesture, or make a new one
        g = self.find_colliding_gesture(touch)
        new = False
        if g is None:
            g = self.init_gesture(touch)
            new = True

        # We now belong to a gesture (new or old); start a new stroke.
        self.init_stroke(g, touch)

        if new:
            self.dispatch('on_gesture_start', g, touch)
        else:
            self.dispatch('on_gesture_extend', g, touch)

        return True

    def on_touch_move(self, touch):
        '''When a touch moves, we add a point to the line on the canvas so the
        path is updated. We must also check if the new point collides with the
        bounding box of another gesture - if so, they should be merged.'''
        if touch.grab_current is not self:
            return
        if not self.collide_point(touch.x, touch.y):
            return

        # Retrieve the GestureContainer object that handles this touch, and
        # test for colliding gestures. If found, merge them to one.
        g = self.get_gesture(touch)
        collision = self.find_colliding_gesture(touch)
        if collision is not None and g.accept_stroke(len(collision._strokes)):
            merge = self.merge_gestures(g, collision)
            if g.was_merged:
                self.dispatch('on_gesture_merge', g, collision)
            else:
                self.dispatch('on_gesture_merge', collision, g)
            g = merge
        else:
            g.update_bbox(touch)

        # Add the new point to gesture stroke list and update the canvas line
        g._strokes[str(touch.uid)].points += (touch.x, touch.y)

        # Draw the gesture bounding box; if it is a single press that
        # does not trigger a move event, we would miss it otherwise.
        if self.draw_bbox:
            self._update_canvas_bbox(g)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return
        touch.ungrab(self)

        g = self.get_gesture(touch)
        g.complete_stroke()

        # If this stroke hit the maximum limit, dispatch immediately
        if not g.accept_stroke():
            self._complete_dispatcher(0)

        # dispatch later only if we have a window
        elif self.temporal_window > 0:
            Clock.schedule_once(self._complete_dispatcher,
                                    self.temporal_window)

# -----------------------------------------------------------------------------
# Gesture related methods
# -----------------------------------------------------------------------------
    def init_gesture(self, touch):
        '''Create a new gesture from touch, i.e. it's the first on
        surface, or was not close enough to any existing gesture (yet)'''
        col = self.color
        if self.use_random_color:
            col = hsv_to_rgb(random(), 1., 1.)

        g = GestureContainer(touch, max_strokes=self.max_strokes, color=col)

        # Create the bounding box Rectangle for the gesture
        if self.draw_bbox:
            bb = g.bbox
            with self.canvas:
                Color(col[0], col[1], col[2], self.bbox_alpha, mode='rgba',
                      group=g.id)

                g._bbrect = Rectangle(
                    group=g.id,
                    pos=(bb['minx'], bb['miny']),
                    size=(bb['maxx'] - bb['minx'],
                          bb['maxy'] - bb['miny']))

        self._gestures.append(g)
        return g

    def init_stroke(self, g, touch):
        points = [touch.x, touch.y]
        col = g.color

        new_line = Line(
            points=points,
            width=self.line_width,
            group=g.id)
        g._strokes[str(touch.uid)] = new_line

        if self.line_width:
            canvas_add = self.canvas.add
            canvas_add(Color(col[0], col[1], col[2], mode='rgb', group=g.id))
            canvas_add(new_line)

        # Update the bbox in case; this will normally be done in on_touch_move,
        # but we want to update it also for a single press, force that here:
        g.update_bbox(touch)
        if self.draw_bbox:
            self._update_canvas_bbox(g)

        # Register the stroke in GestureContainer so we can look it up later
        g.add_stroke(touch, new_line)

    def get_gesture(self, touch):
        '''Returns GestureContainer associated with given touch'''
        for g in self._gestures:
            if g.active and g.handles(touch):
                return g
        raise Exception('get_gesture() failed to identify ' + str(touch.uid))

    def find_colliding_gesture(self, touch):
        '''Checks if a touch x/y collides with the bounding box of an existing
        gesture. If so, return it (otherwise returns None)
        '''
        touch_x, touch_y = touch.pos
        for g in self._gestures:
            if g.active and not g.handles(touch) and g.accept_stroke():
                bb = g.bbox
                margin = self.bbox_margin
                minx = bb['minx'] - margin
                miny = bb['miny'] - margin
                maxx = bb['maxx'] + margin
                maxy = bb['maxy'] + margin
                if minx <= touch_x <= maxx and miny <= touch_y <= maxy:
                    return g
        return None

    def merge_gestures(self, g, other):
        '''Merges two gestures together, the oldest one is retained and the
        newer one gets the `GestureContainer.was_merged` flag raised.'''
        # Swap order depending on gesture age (the merged gesture gets
        # the color from the oldest one of the two).
        swap = other._create_time < g._create_time
        a = swap and other or g
        b = swap and g or other

        # Apply the outer limits of bbox to the merged gesture
        abbox = a.bbox
        bbbox = b.bbox
        if bbbox['minx'] < abbox['minx']:
            abbox['minx'] = bbbox['minx']
        if bbbox['miny'] < abbox['miny']:
            abbox['miny'] = bbbox['miny']
        if bbbox['maxx'] > abbox['maxx']:
            abbox['maxx'] = bbbox['maxx']
        if bbbox['maxy'] > abbox['maxy']:
            abbox['maxy'] = bbbox['maxy']

        # Now transfer the coordinates from old to new gesture;
        # FIXME: This can probably be copied more efficiently?
        astrokes = a._strokes
        lw = self.line_width
        a_id = a.id
        col = a.color

        self.canvas.remove_group(b.id)
        canv_add = self.canvas.add
        for uid, old in b._strokes.items():
            # FIXME: Can't figure out how to change group= for existing Line()
            new_line = Line(
                points=old.points,
                width=old.width,
                group=a_id)
            astrokes[uid] = new_line
            if lw:
                canv_add(Color(col[0], col[1], col[2], mode='rgb', group=a_id))
                canv_add(new_line)

        b.active = False
        b.was_merged = True
        a.active_strokes += b.active_strokes
        a._update_time = Clock.get_time()
        return a

    def _update_canvas_bbox(self, g):
        # If draw_bbox is changed while two gestures are active,
        # we might not have a bbrect member
        if not hasattr(g, '_bbrect'):
            return

        bb = g.bbox
        g._bbrect.pos = (bb['minx'], bb['miny'])
        g._bbrect.size = (bb['maxx'] - bb['minx'],
                          bb['maxy'] - bb['miny'])

# -----------------------------------------------------------------------------
# Timeout callbacks
# -----------------------------------------------------------------------------
    def _complete_dispatcher(self, dt):
        '''This method is scheduled on all touch up events. It will dispatch
        the `on_gesture_complete` event for all completed gestures, and remove
        merged gestures from the internal gesture list.'''
        need_cleanup = False
        gest = self._gestures
        timeout = self.draw_timeout
        twin = self.temporal_window
        get_time = Clock.get_time

        for idx, g in enumerate(gest):
            # Gesture is part of another gesture, just delete it
            if g.was_merged:
                del gest[idx]
                continue

            # Not active == already handled, or has active strokes (it cannot
            # possibly be complete). Proceed to next gesture on surface.
            if not g.active or g.active_strokes != 0:
                continue

            t1 = g._update_time + twin
            t2 = get_time() + UNDERSHOOT_MARGIN

            # max_strokes reached, or temporal window has expired. The gesture
            # is complete; need to dispatch _complete or _discard event.
            if not g.accept_stroke() or t1 <= t2:
                discard = False
                if g.width < 5 and g.height < 5:
                    discard = True
                elif g.single_points_test():
                    discard = True

                need_cleanup = True
                g.active = False
                g._cleanup_time = get_time() + timeout

                if discard:
                    self.dispatch('on_gesture_discard', g)
                else:
                    self.dispatch('on_gesture_complete', g)

        if need_cleanup:
            Clock.schedule_once(self._cleanup, timeout)

    def _cleanup(self, dt):
        '''This method is scheduled from _complete_dispatcher to clean up the
        canvas and internal gesture list after a gesture is completed.'''
        m = UNDERSHOOT_MARGIN
        rg = self.canvas.remove_group
        gestures = self._gestures
        for idx, g in enumerate(gestures):
            if g._cleanup_time is None:
                continue
            if g._cleanup_time <= Clock.get_time() + m:
                rg(g.id)
                del gestures[idx]
                self.dispatch('on_gesture_cleanup', g)

    def on_gesture_start(self, *l):
        pass

    def on_gesture_extend(self, *l):
        pass

    def on_gesture_merge(self, *l):
        pass

    def on_gesture_complete(self, *l):
        pass

    def on_gesture_discard(self, *l):
        pass

    def on_gesture_cleanup(self, *l):
        pass
