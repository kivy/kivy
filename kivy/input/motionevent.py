'''
.. _motionevent:

Motion Event
============

The :class:`MotionEvent` is the base class used for events provided by
pointing devices (touch and non-touch). This class defines all the properties
and methods needed to handle 2D and 3D movements but has many more
capabilities.

.. note::

    You never create the :class:`MotionEvent` yourself: this is the role of the
    :mod:`~kivy.input.providers`.

Motion Event and Touch
----------------------

We differentiate between a Motion Event and Touch event. A Touch event is a
:class:`MotionEvent` with the `pos` profile. Only these events are dispatched
throughout the widget tree.

1. The :class:`MotionEvent` 's are gathered from input providers.
2. All the :class:`MotionEvent` 's are dispatched from
    :meth:`~kivy.core.window.WindowBase.on_motion`.
3. If a :class:`MotionEvent` has a `pos` profile, we dispatch it through
    :meth:`~kivy.core.window.WindowBase.on_touch_down`,
    :meth:`~kivy.core.window.WindowBase.on_touch_move` and
    :meth:`~kivy.core.window.WindowBase.on_touch_up`.

Listening to a Motion Event
---------------------------

If you want to receive all MotionEvents, Touch or not, you can bind the
MotionEvent from the :class:`~kivy.core.window.Window` to your own callback::

    def on_motion(self, etype, motionevent):
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
    '''Abstract class that represents an input event (touch or non-touch).

    :Parameters:
        `id`: str
            unique ID of the MotionEvent
        `args`: list
            list of parameters, passed to the depack() function
    '''

    __uniq_id = 0
    __attrs__ = \
        ('device', 'push_attrs', 'push_attrs_stack',
         'is_touch', 'id', 'shape', 'profile',
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

    def __init__(self, device, id, args):
        if self.__class__ == MotionEvent:
            raise NotImplementedError('class MotionEvent is abstract')
        MotionEvent.__uniq_id += 1

        #: True if the Motion Event is a Touch. Can be also verified is
        #: `pos` is :attr:`profile`.
        self.is_touch = False

        #: Attributes to push by default, when we use :meth:`push` : x, y, z,
        #: dx, dy, dz, ox, oy, oz, px, py, pz.
        self.push_attrs_stack = []
        self.push_attrs = ('x', 'y', 'z', 'dx', 'dy', 'dz', 'ox', 'oy', 'oz',
                           'px', 'py', 'pz', 'pos')

        #: Uniq ID of the touch. You can safely use this property, it will be
        #: never the same accross all existing touches.
        self.uid = MotionEvent.__uniq_id

        #: Device used for creating this touch
        self.device = device

        # For grab
        self.grab_list = []
        self.grab_exclusive_class = None
        self.grab_state = False

        #: Used to determine which widget the touch is being dispatched to.
        #: Check the :meth:`grab` function for more information.
        self.grab_current = None

        #: Profiles currently used in the touch
        self.profile = []

        #: Id of the touch, not uniq. This is generally the Id set by the input
        #: provider, like ID in TUIO. If you have multiple TUIO source,
        #: the same id can be used. Prefer to use :attr:`uid` attribute
        #: instead.
        self.id = id

        #: Shape of the touch, subclass of
        #: :class:`~kivy.input.shape.Shape`.
        #: By default, the property is set to None
        self.shape = None

        #: X position, in 0-1 range
        self.sx = 0.0
        #: Y position, in 0-1 range
        self.sy = 0.0
        #: Z position, in 0-1 range
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
        #: X position, in window range
        self.x = 0.0
        #: Y position, in window range
        self.y = 0.0
        #: Z position, in window range
        self.z = 0.0
        #: Origin X position, in window range
        self.ox = None
        #: Origin Y position, in window range
        self.oy = None
        #: Origin Z position, in window range
        self.oz = None
        #: Previous X position, in window range
        self.px = None
        #: Previous Y position, in window range
        self.py = None
        #: Previous Z position, in window range
        self.pz = None
        #: Delta between self.x and self.px, in window range
        self.dx = None
        #: Delta between self.y and self.py, in window range
        self.dy = None
        #: Delta between self.z and self.pz, in window range
        self.dz = None
        #: Position (X, Y), in window range
        self.pos = (0.0, 0.0)

        #: Initial time of the touch creation
        self.time_start = time()

        #: Time of the last update
        self.time_update = self.time_start

        #: Time of the end event (last touch usage)
        self.time_end = -1

        #: Indicate if the touch is a double tap or not
        self.is_double_tap = False

        #: Indicate if the touch is a triple tap or not
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
        #: the touch.
        self.ud = EnhancedDictionary()

        self.depack(args)

    def depack(self, args):
        '''Depack `args` into attributes of the class'''
        # set initial position and last position
        if self.osx is None:
            self.psx = self.osx = self.sx
            self.psy = self.osy = self.sy
            self.psz = self.osz = self.sz
        # update the delta
        self.dsx = self.sx - self.psx
        self.dsy = self.sy - self.psy
        self.dsz = self.sz - self.psz

    def grab(self, class_instance, exclusive=False):
        '''Grab this motion event. You can grab a touch if you want
        to receive subsequent :meth:`~kivy.uix.widget.Widget.on_touch_move`
        and :meth:`~kivy.uix.widget.Widget.on_touch_up`
        events, even if the touch is not dispatched by the parent:

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
        '''
        if not self.is_touch:
            raise Exception('Grab works only for Touch MotionEvents.')
        if self.grab_exclusive_class is not None:
            raise Exception('Cannot grab the touch, touch is exclusive')
        class_instance = weakref.ref(class_instance.__self__)
        if exclusive:
            self.grab_exclusive_class = class_instance
        self.grab_list.append(class_instance)

    def ungrab(self, class_instance):
        '''Ungrab a previously grabbed touch
        '''
        class_instance = weakref.ref(class_instance.__self__)
        if self.grab_exclusive_class == class_instance:
            self.grab_exclusive_class = None
        if class_instance in self.grab_list:
            self.grab_list.remove(class_instance)

    def move(self, args):
        '''Move the touch to another position
        '''
        self.px = self.x
        self.py = self.y
        self.pz = self.z
        self.psx = self.sx
        self.psy = self.sy
        self.psz = self.sz
        self.time_update = time()
        self.depack(args)

    def scale_for_screen(self, w, h, p=None, rotation=0,
                         smode='None', kheight=0):
        '''Scale position for the screen
        '''
        sx, sy = self.sx, self.sy
        if rotation == 0:
            self.x = sx * float(w)
            self.y = sy * float(h)
        elif rotation == 90:
            sx, sy = sy, 1 - sx
            self.x = sx * float(h)
            self.y = sy * float(w)
        elif rotation == 180:
            sx, sy = 1 - sx, 1 - sy
            self.x = sx * float(w)
            self.y = sy * float(h)
        elif rotation == 270:
            sx, sy = 1 - sy, sx
            self.x = sx * float(h)
            self.y = sy * float(w)

        if p:
            self.z = self.sz * float(p)

        if smode:
            if smode == 'pan':
                self.y -= kheight
            elif smode == 'scale':
                self.y += (kheight * (
                    (self.y - kheight) / (h - kheight))) - kheight

        if self.ox is None:
            self.px = self.ox = self.x
            self.py = self.oy = self.y
            self.pz = self.oz = self.z

        self.dx = self.x - self.px
        self.dy = self.y - self.py
        self.dz = self.z - self.pz

        # cache position
        self.pos = self.x, self.y

    def push(self, attrs=None):
        '''Push attribute values in `attrs` onto the stack
        '''
        if attrs is None:
            attrs = self.push_attrs
        values = [getattr(self, x) for x in attrs]
        self.push_attrs_stack.append((attrs, values))

    def pop(self):
        '''Pop attributes values from the stack
        '''
        attrs, values = self.push_attrs_stack.pop()
        for i in range(len(attrs)):
            setattr(self, attrs[i], values[i])

    def apply_transform_2d(self, transform):
        '''Apply a transformation on x, y, z, px, py, pz,
        ox, oy, oz, dx, dy, dz
        '''
        self.x, self.y = self.pos = transform(self.x, self.y)
        self.px, self.py = transform(self.px, self.py)
        self.ox, self.oy = transform(self.ox, self.oy)
        self.dx = self.x - self.px
        self.dy = self.y - self.py

    def copy_to(self, to):
        '''Copy some attribute to another touch object.'''
        for attr in self.__attrs__:
            to.__setattr__(attr, copy(self.__getattribute__(attr)))

    def distance(self, other_touch):
        '''Return the distance between the current touch and another touch.
        '''
        return Vector(self.pos).distance(other_touch.pos)

    def update_time_end(self):
        self.time_end = time()

    # facilities
    @property
    def dpos(self):
        '''Return delta between last position and current position, in the
        screen coordinate system (self.dx, self.dy)'''
        return self.dx, self.dy

    @property
    def opos(self):
        '''Return the initial position of the touch in the screen
        coordinate system (self.ox, self.oy)'''
        return self.ox, self.oy

    @property
    def ppos(self):
        '''Return the previous position of the touch in the screen
        coordinate system (self.px, self.py)'''
        return self.px, self.py

    @property
    def spos(self):
        '''Return the position in the 0-1 coordinate system
        (self.sx, self.sy)'''
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
        '''Returns True if the touch is a mousewheel scrolling

        .. versionadded:: 1.6.0
        '''
        return 'button' in self.profile and 'scroll' in self.button
