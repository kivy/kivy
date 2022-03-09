'''
.. _motionevent:

Motion Event
============

The :class:`MotionEvent` is the base class used for events provided by
pointing devices (touch and non-touch). This class defines all the properties
and methods needed to handle 2D and 3D movements but has many more
capabilities.

Usually you would never need to create the :class:`MotionEvent` yourself as
this is the role of the :mod:`~kivy.input.providers`.

Flow of the motion events
-------------------------

1. The :class:`MotionEvent` 's are gathered from input providers by
   :class:`~kivy.base.EventLoopBase`.
2. Post processing is performed by registered processors
   :mod:`~kivy.input.postproc`.
3. :class:`~kivy.base.EventLoopBase` dispatches all motion events using
   `on_motion` event to all registered listeners including the
   :class:`~kivy.core.window.WindowBase`.
4. Once received in :meth:`~kivy.core.window.WindowBase.on_motion` events
   (touch or non-touch) are all registered managers. If a touch event is not
   handled by at least one manager, then it is dispatched through
   :meth:`~kivy.core.window.WindowBase.on_touch_down`,
   :meth:`~kivy.core.window.WindowBase.on_touch_move` and
   :meth:`~kivy.core.window.WindowBase.on_touch_up`.
5. Widgets receive events in :meth:`~kivy.uix.widget.Widget.on_motion` method
   (if passed by a manager) or on `on_touch_xxx` methods.

Motion events and event managers
--------------------------------

A motion event is a touch event if its :attr:`MotionEvent.is_touch` is set to
`True`. Beside `is_touch` attribute, :attr:`MotionEvent.type_id` can be used to
check for event's general type. Currently two types are dispatched by
input providers: "touch" and "hover".

Event managers can be used to dispatch any motion event throughout the widget
tree and a manager uses `type_id` to specify which event types it want to
receive. See :mod:`~kivy.eventmanager` to learn how to define and register
an event manager.

A manager can also assign a new `type_id` to
:attr:`MotionEvent.type_id` before dispatching it to the widgets. This useful
when dispatching a specific event::

    class MouseTouchManager(EventManagerBase):

        type_ids = ('touch',)

        def dispatch(self, etype, me):
            accepted = False
            if me.device == 'mouse':
                me.push() # Save current type_id and other values
                me.type_id = 'mouse_touch'
                self.window.transform_motion_event_2d(me)
                # Dispatch mouse touch event to widgets which registered
                # to receive 'mouse_touch'
                for widget in self.window.children[:]:
                    if widget.dispatch('on_motion', etype, me):
                        accepted = True
                        break
                me.pop() # Restore
            return accepted

Listening to a motion event
---------------------------

If you want to receive all motion events, touch or not, you can bind the
MotionEvent from the :class:`~kivy.core.window.Window` to your own callback::

    def on_motion(self, etype, me):
        # will receive all motion events.
        pass

    Window.bind(on_motion=on_motion)

You can also listen to changes of the mouse position by watching
:attr:`~kivy.core.window.WindowBase.mouse_pos`.

Profiles
--------

The :class:`MotionEvent` stores device specific information in various
properties listed in the :attr:`~MotionEvent.profile`.
For example, you can receive a MotionEvent that has an angle, a fiducial
ID, or even a shape. You can check the :attr:`~MotionEvent.profile`
attribute to see what is currently supported by the MotionEvent provider.

This is a short list of the profile values supported by default. Please check
the :attr:`MotionEvent.profile` property to see what profile values are
available.

============== ================================================================
Profile value   Description
-------------- ----------------------------------------------------------------
angle          2D angle. Accessed via the `a` property.
button         Mouse button ('left', 'right', 'middle', 'scrollup' or
               'scrolldown'). Accessed via the `button` property.
markerid       Marker or Fiducial ID. Accessed via the `fid` property.
pos            2D position. Accessed via the `x`, `y` or `pos` properties.
pos3d          3D position. Accessed via the `x`, `y` or `z` properties.
pressure       Pressure of the contact. Accessed via the `pressure` property.
shape          Contact shape. Accessed via the `shape` property .
============== ================================================================

If you want to know whether the current :class:`MotionEvent` has an angle::

    def on_touch_move(self, touch):
        if 'angle' in touch.profile:
            print('The touch angle is', touch.a)

If you want to select only the fiducials::

    def on_touch_move(self, touch):
        if 'markerid' not in touch.profile:
            return

'''

__all__ = ('MotionEvent', )

import weakref
from inspect import isroutine
from copy import copy
from time import time

from kivy.eventmanager import MODE_DEFAULT_DISPATCH
from kivy.vector import Vector


class EnhancedDictionary(dict):

    def __getattr__(self, attr):
        try:
            return self.__getitem__(attr)
        except KeyError:
            return super(EnhancedDictionary, self).__getattr__(attr)

    def __setattr__(self, attr, value):
        self.__setitem__(attr, value)


class MotionEventMetaclass(type):

    def __new__(mcs, name, bases, attrs):
        __attrs__ = []
        for base in bases:
            if hasattr(base, '__attrs__'):
                __attrs__.extend(base.__attrs__)
        if '__attrs__' in attrs:
            __attrs__.extend(attrs['__attrs__'])
        attrs['__attrs__'] = tuple(__attrs__)
        return super(MotionEventMetaclass, mcs).__new__(mcs, name,
                                                        bases, attrs)


MotionEventBase = MotionEventMetaclass('MotionEvent', (object, ), {})


class MotionEvent(MotionEventBase):
    '''Abstract class that represents an input event.

    :Parameters:
        `id`: str
            unique ID of the MotionEvent
        `args`: list
            list of parameters, passed to the depack() function
    '''

    __uniq_id = 0
    __attrs__ = \
        ('device', 'push_attrs', 'push_attrs_stack',
         'is_touch', 'type_id', 'id', 'dispatch_mode', 'shape', 'profile',
         # current position, in 0-1 range
         'sx', 'sy', 'sz',
         # first position set, in 0-1 range
         'osx', 'osy', 'osz',
         # last position set, in 0-1 range
         'psx', 'psy', 'psz',
         # delta from the last position and current one, in 0-1 range
         'dsx', 'dsy', 'dsz',
         # current position, in screen range
         'x', 'y', 'z',
         # first position set, in screen range
         'ox', 'oy', 'oz',
         # last position set, in 0-1 range
         'px', 'py', 'pz',
         # delta from the last position and current one, in screen range
         'dx', 'dy', 'dz',
         'time_start',
         'is_double_tap', 'double_tap_time',
         'is_triple_tap', 'triple_tap_time',
         'ud')

    def __init__(self, device, id, args, is_touch=False, type_id=None):
        if self.__class__ == MotionEvent:
            raise NotImplementedError('class MotionEvent is abstract')
        MotionEvent.__uniq_id += 1

        #: True if the MotionEvent is a touch.
        self.is_touch = is_touch

        #: (Experimental) String to identify event type.
        #:
        #: .. versionadded:: 2.1.0
        self.type_id = type_id

        #: (Experimental) Used by a event manager or a widget to assign
        #: the dispatching mode. Defaults to
        #: :const:`~kivy.eventmanager.MODE_DEFAULT_DISPATCH`. See
        #: :mod:`~kivy.eventmanager` for available modes.
        #:
        #: .. versionadded:: 2.1.0
        self.dispatch_mode = MODE_DEFAULT_DISPATCH

        #: Attributes to push by default, when we use :meth:`push` : x, y, z,
        #: dx, dy, dz, ox, oy, oz, px, py, pz.
        self.push_attrs_stack = []
        self.push_attrs = ('x', 'y', 'z', 'dx', 'dy', 'dz', 'ox', 'oy', 'oz',
                           'px', 'py', 'pz', 'pos', 'type_id', 'dispatch_mode')

        #: Uniq ID of the event. You can safely use this property, it will be
        #: never the same across all existing events.
        self.uid = MotionEvent.__uniq_id

        #: Device used for creating this event.
        self.device = device

        # For grab
        self.grab_list = []
        self.grab_exclusive_class = None
        self.grab_state = False

        #: Used to determine which widget the event is being dispatched to.
        #: Check the :meth:`grab` function for more information.
        self.grab_current = None

        #: Currently pressed button.
        self.button = None

        #: Profiles currently used in the event.
        self.profile = []

        #: Id of the event, not unique. This is generally the Id set by the
        #: input provider, like ID in TUIO. If you have multiple TUIO sources,
        #: then same id can be used. Prefer to use :attr:`uid` attribute
        #: instead.
        self.id = id

        #: Shape of the touch event, subclass of
        #: :class:`~kivy.input.shape.Shape`.
        #: By default, the property is set to None.
        self.shape = None

        #: X position, in 0-1 range.
        self.sx = 0.0
        #: Y position, in 0-1 range.
        self.sy = 0.0
        #: Z position, in 0-1 range.
        self.sz = 0.0
        #: Origin X position, in 0-1 range.
        self.osx = None
        #: Origin Y position, in 0-1 range.
        self.osy = None
        #: Origin Z position, in 0-1 range.
        self.osz = None
        #: Previous X position, in 0-1 range.
        self.psx = None
        #: Previous Y position, in 0-1 range.
        self.psy = None
        #: Previous Z position, in 0-1 range.
        self.psz = None
        #: Delta between self.sx and self.psx, in 0-1 range.
        self.dsx = None
        #: Delta between self.sy and self.psy, in 0-1 range.
        self.dsy = None
        #: Delta between self.sz and self.psz, in 0-1 range.
        self.dsz = None
        #: X position, in window range.
        self.x = 0.0
        #: Y position, in window range.
        self.y = 0.0
        #: Z position, in window range.
        self.z = 0.0
        #: Origin X position, in window range.
        self.ox = None
        #: Origin Y position, in window range.
        self.oy = None
        #: Origin Z position, in window range.
        self.oz = None
        #: Previous X position, in window range.
        self.px = None
        #: Previous Y position, in window range.
        self.py = None
        #: Previous Z position, in window range.
        self.pz = None
        #: Delta between self.x and self.px, in window range.
        self.dx = None
        #: Delta between self.y and self.py, in window range.
        self.dy = None
        #: Delta between self.z and self.pz, in window range.
        self.dz = None
        #: Position (X, Y), in window range.
        self.pos = (0.0, 0.0)

        #: Initial time of the event creation.
        self.time_start = time()

        #: Time of the last update.
        self.time_update = self.time_start

        #: Time of the end event (last event usage).
        self.time_end = -1

        #: Indicate if the touch event is a double tap or not.
        self.is_double_tap = False

        #: Indicate if the touch event is a triple tap or not.
        #:
        #: .. versionadded:: 1.7.0
        self.is_triple_tap = False

        #: If the touch is a :attr:`is_double_tap`, this is the time
        #: between the previous tap and the current touch.
        self.double_tap_time = 0

        #: If the touch is a :attr:`is_triple_tap`, this is the time
        #: between the first tap and the current touch.
        #:
        #: .. versionadded:: 1.7.0
        self.triple_tap_time = 0

        #: User data dictionary. Use this dictionary to save your own data on
        #: the event.
        self.ud = EnhancedDictionary()

        #: If set to `True` (default) keeps first previous position
        #: (X, Y, Z in 0-1 range) and ignore all other until
        #: :meth:`MotionEvent.dispatch_done` is called from the `EventLoop`.
        #:
        #: This attribute is needed because event provider can make many calls
        #: to :meth:`MotionEvent.move`, but for all those calls event is
        #: dispatched to the listeners only once. Assigning `False` will keep
        #: latest previous position. See :meth:`MotionEvent.move`.
        #:
        #: .. versionadded:: 2.1.0
        self.sync_with_dispatch = True

        #: Keep first previous position if :attr:`sync_with_dispatch` is
        #: `True`.
        self._keep_prev_pos = True

        #: Flag that first dispatch of this event is done.
        self._first_dispatch_done = False

        self.depack(args)

    def depack(self, args):
        '''Depack `args` into attributes of the class'''
        if self.osx is None \
                or self.sync_with_dispatch and not self._first_dispatch_done:
            # Sync origin/previous/current positions until the first
            # dispatch (etype == 'begin') is done.
            self.osx = self.psx = self.sx
            self.osy = self.psy = self.sy
            self.osz = self.psz = self.sz
        # update the delta
        self.dsx = self.sx - self.psx
        self.dsy = self.sy - self.psy
        self.dsz = self.sz - self.psz

    def grab(self, class_instance, exclusive=False):
        '''Grab this motion event.

        If this event is a touch you can grab it if you want to receive
        subsequent :meth:`~kivy.uix.widget.Widget.on_touch_move` and
        :meth:`~kivy.uix.widget.Widget.on_touch_up` events, even if the touch
        is not dispatched by the parent:

        .. code-block:: python

            def on_touch_down(self, touch):
                touch.grab(self)

            def on_touch_move(self, touch):
                if touch.grab_current is self:
                    # I received my grabbed touch
                else:
                    # it's a normal touch

            def on_touch_up(self, touch):
                if touch.grab_current is self:
                    # I receive my grabbed touch, I must ungrab it!
                    touch.ungrab(self)
                else:
                    # it's a normal touch
                    pass

        .. versionchanged:: 2.1.0
            Allowed grab for non-touch events.
        '''
        if self.grab_exclusive_class is not None:
            raise Exception('Event is exclusive and cannot be grabbed')
        class_instance = weakref.ref(class_instance.__self__)
        if exclusive:
            self.grab_exclusive_class = class_instance
        self.grab_list.append(class_instance)

    def ungrab(self, class_instance):
        '''Ungrab a previously grabbed motion event.
        '''
        class_instance = weakref.ref(class_instance.__self__)
        if self.grab_exclusive_class == class_instance:
            self.grab_exclusive_class = None
        if class_instance in self.grab_list:
            self.grab_list.remove(class_instance)

    def dispatch_done(self):
        '''Notify that dispatch to the listeners is done.

        Called by the :meth:`EventLoopBase.post_dispatch_input`.

        .. versionadded:: 2.1.0
        '''
        self._keep_prev_pos = True
        self._first_dispatch_done = True

    def move(self, args):
        '''Move to another position.
        '''
        if self.sync_with_dispatch:
            if self._keep_prev_pos:
                self.psx, self.psy, self.psz = self.sx, self.sy, self.sz
                self._keep_prev_pos = False
        else:
            self.psx, self.psy, self.psz = self.sx, self.sy, self.sz
        self.time_update = time()
        self.depack(args)

    def scale_for_screen(self, w, h, p=None, rotation=0,
                         smode='None', kheight=0):
        '''Scale position for the screen.

        .. versionchanged:: 2.1.0
            Max value for `x`, `y` and `z` is changed respectively to `w` - 1,
            `h` - 1 and `p` - 1.
        '''
        x_max, y_max = max(0, w - 1), max(0, h - 1)
        absolute = self.to_absolute_pos
        self.x, self.y = absolute(self.sx, self.sy, x_max, y_max, rotation)
        self.ox, self.oy = absolute(self.osx, self.osy, x_max, y_max, rotation)
        self.px, self.py = absolute(self.psx, self.psy, x_max, y_max, rotation)
        z_max = 0 if p is None else max(0, p - 1)
        self.z = self.sz * z_max
        self.oz = self.osz * z_max
        self.pz = self.psz * z_max
        if smode:
            # Adjust y for keyboard height
            if smode == 'pan' or smode == 'below_target':
                self.y -= kheight
                self.oy -= kheight
                self.py -= kheight
            elif smode == 'scale':
                offset = kheight * (self.y - h) / (h - kheight)
                self.y += offset
                self.oy += offset
                self.py += offset
        # Update delta values
        self.dx = self.x - self.px
        self.dy = self.y - self.py
        self.dz = self.z - self.pz
        # Cache position
        self.pos = self.x, self.y

    def to_absolute_pos(self, nx, ny, x_max, y_max, rotation):
        '''Transforms normalized (0-1) coordinates `nx` and `ny` to absolute
        coordinates using `x_max`, `y_max` and `rotation`.

        :raises:
            `ValueError`: If `rotation` is not one of: 0, 90, 180 or 270

        .. versionadded:: 2.1.0
        '''
        if rotation == 0:
            return nx * x_max, ny * y_max
        elif rotation == 90:
            return ny * y_max, (1 - nx) * x_max
        elif rotation == 180:
            return (1 - nx) * x_max, (1 - ny) * y_max
        elif rotation == 270:
            return (1 - ny) * y_max, nx * x_max
        raise ValueError('Invalid rotation %s, '
                         'valid values are 0, 90, 180 or 270' % rotation)

    def push(self, attrs=None):
        '''Push attribute values in `attrs` onto the stack.
        '''
        if attrs is None:
            attrs = self.push_attrs
        values = [getattr(self, x) for x in attrs]
        self.push_attrs_stack.append((attrs, values))

    def pop(self):
        '''Pop attributes values from the stack.
        '''
        attrs, values = self.push_attrs_stack.pop()
        for i in range(len(attrs)):
            setattr(self, attrs[i], values[i])

    def apply_transform_2d(self, transform):
        '''Apply a transformation on x, y, z, px, py, pz,
        ox, oy, oz, dx, dy, dz.
        '''
        self.x, self.y = self.pos = transform(self.x, self.y)
        self.px, self.py = transform(self.px, self.py)
        self.ox, self.oy = transform(self.ox, self.oy)
        self.dx = self.x - self.px
        self.dy = self.y - self.py

    def copy_to(self, to):
        '''Copy some attribute to another motion event object.'''
        for attr in self.__attrs__:
            to.__setattr__(attr, copy(self.__getattribute__(attr)))

    def distance(self, other_touch):
        '''Return the distance between the two events.
        '''
        return Vector(self.pos).distance(other_touch.pos)

    def update_time_end(self):
        self.time_end = time()

    # facilities
    @property
    def dpos(self):
        '''Return delta between last position and current position, in the
        screen coordinate system (self.dx, self.dy).'''
        return self.dx, self.dy

    @property
    def opos(self):
        '''Return the initial position of the motion event in the screen
        coordinate system (self.ox, self.oy).'''
        return self.ox, self.oy

    @property
    def ppos(self):
        '''Return the previous position of the motion event in the screen
        coordinate system (self.px, self.py).'''
        return self.px, self.py

    @property
    def spos(self):
        '''Return the position in the 0-1 coordinate system (self.sx, self.sy).
        '''
        return self.sx, self.sy

    def __str__(self):
        basename = str(self.__class__)
        classname = basename.split('.')[-1].replace('>', '').replace('\'', '')
        return '<%s spos=%s pos=%s>' % (classname, self.spos, self.pos)

    def __repr__(self):
        out = []
        for x in dir(self):
            v = getattr(self, x)
            if x[0] == '_':
                continue
            if isroutine(v):
                continue
            out.append('%s="%s"' % (x, v))
        return '<%s %s>' % (
            self.__class__.__name__,
            ' '.join(out))

    @property
    def is_mouse_scrolling(self, *args):
        '''Returns True if the touch event is a mousewheel scrolling

        .. versionadded:: 1.6.0
        '''
        return 'button' in self.profile and 'scroll' in self.button
