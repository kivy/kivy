#!/usr/bin/env python
from random import random
from collections import deque
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Line, Rectangle
from kivy.properties import ObjectProperty
from kivy.multistroke import Recognizer, GPoint

__all__ = ('TouchAnalyzer', 'GContainer')

# Number of seconds from touch up event until a new touch is considered
# unrelated (ie analysis will start)
TEMPORAL_WINDOW = 1.85

# Result disappears from screen after n seconds
RESULT_TIMEOUT = 3.5

# Maximum number of strokes per gesture (0 = disabled)
MAX_STROKES = 4

# We add this amounnt of pixels to a gesture's bounding box to detect
# collisions (in both directions)
FUZZY_BBOX = 35


class GContainer(object):
    '''A simple Gesture Container that is used to store data about one of the
    tracked gestures.'''
    def __init__(self, touch, max_strokes=0):
        # This is the touch.uid of the oldest touch represented
        self.id = str(touch.uid)

        # When analysis is started, the gesture is deactivated
        self.active = True

        # We need to track active strokes to make sure we don't analyze
        # a gesture when a stroke is still active.
        self.active_strokes = 0

        # This option forces the gesture to be dispatched if it reaches
        # this number of strokes; it will not allow merging with another
        # gesture if the total stroke length is exceeded.
        self.max_strokes = max_strokes

        # When a gesture is merged (so it disappears), this flag is raised
        # so we can clean it up later.
        self.merged = False

        # Raised if the gesture is too small to be matched; so it's not
        # appended to history after cleanup
        self.discard = False

        # Store various timestamps for decision making
        self.created = Clock.get_time()
        self.last_update = None
        self.result_time = None

        # Before we push the item to history, we tag it with the corresponding
        # GestureSearch object
        self.recognize_result = None

        # The color is applied to all canvas items of this gesture
        self.color = random()

        # Key is touch.uid; value is the canvas Line item.
        self.strokes = {}

        # Holds Canvas instructions
        self.bbrect = None
        self.result_lbl = None

        # Actual bounding box data, updated for every touch move
        self.bbox = {'minx': float('inf'),  'miny': float('inf'),
                     'maxx': float('-inf'), 'maxy': float('-inf')}

        # Computed on bbox update
        self.width = 0
        self.height = 0

        # Make sure the bbox is up to date with the first touch position
        self.update_bbox(touch)

    def handles(self, touch):
        if not self.active:
            return False
        return str(touch.uid) in self.strokes

    def accept_stroke(self, count=1):
        if not self.max_strokes:
            return True
        return len(self.strokes) + count <= self.max_strokes

    def update_bbox(self, touch):
        '''Update gesture bbox from a touch coordinate'''
        if touch.x < self.bbox['minx']:
            self.bbox['minx'] = touch.x
        if touch.y < self.bbox['miny']:
            self.bbox['miny'] = touch.y
        if touch.x > self.bbox['maxx']:
            self.bbox['maxx'] = touch.x
        if touch.y > self.bbox['maxy']:
            self.bbox['maxy'] = touch.y
        self.width = self.bbox['maxx'] - self.bbox['minx']
        self.height = self.bbox['maxy'] - self.bbox['miny']
        self.last_update = Clock.get_time()

    def add_stroke(self, touch, line):
        '''Associate a canvas Line with a touch.uid; the line itself is
        created by the caller, but subsequent move/up events look it
        up via us. This is done to avoid problems during merge.'''
        self.last_update = Clock.get_time()
        self.strokes[str(touch.uid)] = line
        self.active_strokes += 1

    def complete_stroke(self):
        '''Called on touch up events to keep track of how many strokes
        are actie in the gesture. (we only want to dispatch event when
        the *last* stroke is released'''
        self.last_update = Clock.get_time()
        self.active_strokes -= 1

    def merge_with(self, other, canvas):
        # Swap order depending on gesture age (the merged gesture gets
        # the color from the oldest one of the two).
        swap = other.created < self.created
        a = swap and other or self
        b = swap and self  or other

        # Apply the outer limits of bbox to the merged gesture
        if b.bbox['minx'] < a.bbox['minx']:
            a.bbox['minx'] = b.bbox['minx']
        if b.bbox['miny'] < a.bbox['miny']:
            a.bbox['miny'] = b.bbox['miny']
        if b.bbox['maxx'] > a.bbox['maxx']:
            a.bbox['maxx'] = b.bbox['maxx']
        if b.bbox['maxy'] > a.bbox['maxy']:
            a.bbox['maxy'] = b.bbox['maxy']

        # Now transfer the actual line from old to new gesture;
        # FIXME: I couldn't figure out how to actually change the group/color
        # of the old instructions, so this was the easiest hack..
        for uid, old_line in b.strokes.items():
            with canvas:
                Color(a.color, 1, 1, mode='hsv', group=a.id)
                a.strokes[uid] = Line(points=old_line.points, group=a.id)

        b.active = False
        b.merged = True
        canvas.remove_group(b.id)

        a.active_strokes += b.active_strokes
        a.last_updated = Clock.get_time()
        return a

    def collide_point(self, x, y):
        '''Check if point collides with gesture; add some fuzzyness to merge
        stroke when they get in close proximity.'''
        minx = self.bbox['minx'] - FUZZY_BBOX
        miny = self.bbox['miny'] - FUZZY_BBOX
        maxx = self.bbox['maxx'] + FUZZY_BBOX
        maxy = self.bbox['maxy'] + FUZZY_BBOX
        return minx <= x <= maxx and miny <= y <= maxy


# Could not figure out how to do this with canvas Line instructions stored in
# touch.ud, so I moved them all out instead of a hybrid approach.

class TouchAnalyzer(FloatLayout):
    '''$N is a template-based gesture recognizer; there are a lot of problems
    that it does not solve. This class illustrates how the `on_touch` events
    can be used in combination with Recognizer. The basic job is to determine
    what strokes belong in what gesture, and then dispatch for template
    matching.'''

    gdb = ObjectProperty(Recognizer())

    def __init__(self, **kwargs):
        super(TouchAnalyzer, self).__init__(**kwargs)

        # A list of GContainer objects; ie all the gestures on the surface.
        self._gestures = []

        # When we don't need the gesture anymore (ie finished analyzing and
        # reporting the result), it is moved to history storage. This is a
        # deque() object so we can .popleft() items in history order.
        self._history = deque()

        # Dispatched when a set of strokes is considered a complete gesture,
        # we will start Recognizer.recognize() from the default handler.
        self.register_event_type('on_gesture_detect')

        # Dispatched when the call to recognize() has completed, ie finished
        # analyzing the gesture. We will show the result label from here.
        self.register_event_type('on_gesture_recognize')

        # Dispatched if a gesture is detected, but too small to be considered
        # worthy of template matching (ie w<5 and h<5)
        self.register_event_type('on_gesture_discard')

        # Dispatched when a gesture is moved to history
        self.register_event_type('on_gesture_purge')

        super(TouchAnalyzer, self).__init__(**kwargs)

# -----------------------------------------------------------------------------
# Touch Event handlers
# -----------------------------------------------------------------------------
    def on_touch_down(self, touch):
        '''When a new touch is registered, the first thing we do is to test if
        it collides with the bounding box of another known gesture. If so, it
        is assumed to be part of that gesture.
        '''
        # If the touch originates outside the analyzer, ignore it.
        if not self.collide_point(touch.x, touch.y):
            return

        # OLD - we now use touch.grab(self)
        ## Raise a flag so move/up events know they should track the touch
        #touch.ud['is_gesture'] = True
        touch.grab(self)

        # Add the stroke to existing gesture, or make a new one
        g = self.find_colliding_gesture(touch)
        if g is None:
            g = self._init_gesture(touch)

        # We now belong to a gesture (new or old); start a new stroke.
        self._init_stroke(g, touch)

        return True

    def on_touch_move(self, touch):
        '''When a touch moves, we add a point to the line on the canvas so the
        path is updated. We must also check if the new point collides with the
        bouonding box of another gesture - if so, they should be merged.'''
        if touch.grab_current is not self:
            return
        if not self.collide_point(touch.y, touch.y):
            return

        # Retrieve the GContainer object that handles this touch, and test for
        # colliding gestures. If found, merge them to one.
        g = self.get_gesture(touch)
        collision = self.find_colliding_gesture(touch)
        if collision is not None and g.accept_stroke(len(collision.strokes)):
            g = g.merge_with(collision, self.canvas)
        else:
            g.update_bbox(touch)

        # Add a point to the Line with the new coordinates
        g.strokes[str(touch.uid)].points += [touch.x, touch.y]

        # Force drawing the gesture bounding box; if it is a single press that
        # does not trigger a move event, we would miss it otherwise.
        self._update_canvas_bbox(g)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return
        touch.ungrab(self)

        g = self.get_gesture(touch)
        g.complete_stroke()

        # If released within the widget, add a dot to represent end of stroke
        if self.collide_point(touch.x, touch.y):
            with self.canvas:
                Color(g.color, 1, 1, mode='hsv', group=g.id)
                Rectangle(
                    source='particle.png', pos=(touch.x - 5, touch.y - 5),
                    size=(10, 10), group=g.id)

        # If this stroke hit the maximum limit, dispatch immediately
        if not g.accept_stroke():
            self._dispatcher(0)

        # dispatch later only if we have a window
        elif TEMPORAL_WINDOW > 0:
            Clock.schedule_once(self._dispatcher, TEMPORAL_WINDOW)

# -----------------------------------------------------------------------------
# Gesture Event handlers
# -----------------------------------------------------------------------------
    def on_gesture_detect(self, g):
        # Too small, discard it
        if g.width < 5 and g.height < 5:
            self.dispatch('on_gesture_discard', g)
            return

        # Convert the data to acceptable input for recognize, ie a list of
        # GPoint objects with the coordinates from on_touch_* events.
        cand = []
        for tuid, l in g.strokes.items():
            cand.append([GPoint(*pts) for pts in \
                zip(l.points[::2], l.points[1::2])])

        # Create a callback that dispatches the event when the actual search
        # is completed (depends on # of gestures in gdb, among other things)
        def _recognize_complete(result):
            self.dispatch('on_gesture_recognize', g, result)

        import cProfile
        print cProfile.runctx('self.gdb.recognize(cand);Clock.tick()',
                                  globals(), locals())
        res = self.gdb.recognize(cand)
        res.bind(on_complete=_recognize_complete)

    def on_gesture_recognize(self, g, result):
        g.recognize_result = result
        best = result.best
        if best['name'] is not None:
            txt = "Name: %s\nScore: %f\nDistance: %f" % (
                best['name'], best['score'], best['dist'])
        else:
            txt = 'No match'

        g.result_lbl = Label(text=txt, size_hint=(None, None),
            center=(g.bbox['minx'], g.bbox['miny']))
        self.add_widget(g.result_lbl)
        g.result_time = Clock.get_time()
        Clock.schedule_once(self._cleanup, RESULT_TIMEOUT)

    def on_gesture_discard(self, g):
        g.result_lbl = Label(text='Not enough input', size_hint=(None, None),
            center=(g.bbox['minx'], g.bbox['miny']))
        self.add_widget(g.result_lbl)
        g.discard = True
        g.result_time = Clock.get_time()
        Clock.schedule_once(self._cleanup, RESULT_TIMEOUT)

    def on_gesture_purge(self, *l):
        pass

# -----------------------------------------------------------------------------
# Other methods
# -----------------------------------------------------------------------------
    def get_gesture(self, touch):
        for g in self._gestures:
            if g.active and g.handles(touch):
                return g
        raise Exception('get_gesture() failed to identify ' + str(touch.uid))

    def find_colliding_gesture(self, touch):
        '''Checks if a touch x/y collides with the (fuzzy) bounding box of
        another gesture. If so, return it's id (otherwise return touch id)
        '''
        for g in self._gestures:
            if g.active and not g.handles(touch) and g.accept_stroke():
                if g.collide_point(touch.x, touch.y) or not TEMPORAL_WINDOW:
                    return g
        return None

# -----------------------------------------------------------------------------
# Other methods
# -----------------------------------------------------------------------------
    def _update_canvas_bbox(self, g):
        g.bbrect.pos = (g.bbox['minx'], g.bbox['miny'])
        g.bbrect.size = (g.bbox['maxx'] - g.bbox['minx'],
                         g.bbox['maxy'] - g.bbox['miny'])

    def _init_gesture(self, touch):
        '''Create a new gesture from touch, ie it's the first on
        surface, or was not close enough to any existing gesture (yet)'''
        g = GContainer(touch, max_strokes=MAX_STROKES)

        # Create the bounding box Rectangle for the gesture
        bb = g.bbox
        with self.canvas:
            Color(g.color, 1, 1, .045, mode='hsv', group=g.id)
            g.bbrect = Rectangle(
              group=g.id,
              pos=(g.bbox['minx'], g.bbox['miny']),
              size=(g.bbox['maxx'] - g.bbox['minx'],
                    g.bbox['maxy'] - g.bbox['miny'])
            )

        self._gestures.append(g)
        return g

    def _init_stroke(self, g, touch):
        with self.canvas:
            Color(g.color, 1, 1, mode='hsv', group=g.id)
            Rectangle(source='particle.png', pos=(touch.x - 5, touch.y - 5),
                size=(10, 10), group=g.id)
            l = Line(points=(touch.x, touch.y), group=g.id)

        # Update the bbox in case; this will normally be done in on_touch_move,
        # but we want to update it also for a single press, force that here:
        g.update_bbox(touch)
        self._update_canvas_bbox(g)

        # Now register the Line in GContainer so we can look it up later
        g.add_stroke(touch, l)

# -----------------------------------------------------------------------------
# Timeout callbacks
# -----------------------------------------------------------------------------
    def _dispatcher(self, dt):
        '''This method is scheduled on all touch up events. It will not
        always do work; for example if the gesture was merged with another
        one before the timeout occurs. In any case, there will always be a
        final touch, and event is dispatched.'''
        for id, g in enumerate(self._gestures):
            if g.active and g.active_strokes == 0 and \
               (g.last_update + TEMPORAL_WINDOW <= Clock.get_time() or
                not g.accept_stroke()):
                g.active = False
                self.dispatch('on_gesture_detect', g)

            elif g.merged:
                # Do some cleanup while we're here
                del self._gestures[id]

    def _cleanup(self, dt):
        '''This method is scheduled from on_gesture_recognize, it's job is
        to clean up the line/bbox on the canvas, remove the result label
        and move the gesture to history.'''
        for idx, g in enumerate(self._gestures):
            if g.result_time and \
               g.result_time + RESULT_TIMEOUT < Clock.get_time():
                del self._gestures[idx]
                self.canvas.remove_group(g.id)
                if g.result_lbl is not None:
                    self.remove_widget(g.result_lbl)
                if not g.discard:
                    self._history.append(g)
                    self.dispatch('on_gesture_purge')
