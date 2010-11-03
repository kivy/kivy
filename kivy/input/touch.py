'''
Touch: Base for all touch objects


Every touch in Kivy derives from the abstract Touch class.
A touch can have more or less attributes, depending on the provider.
For example, the TUIO provider can give you a lot of information about the touch,
like position, acceleration, width/height of the shape and so on.
Another provider might just give you x/y coordinates and pressure.

We call these attributes "capabilities". Every touch indicates its
capabilities in its "profile" property.
A profile is just a simple list with strings, containing for example:

    * pos (property x, y)
    * pos3d (property x, y, z)
    * mov (tuio/property X, Y)
    * mov3d (tuio/property X, Y, Z)
    * dim (tuio/property w, h)
    * dim3d (tuio/property w, h, d)
    * markerid (tuio/property i (fid property))
    * sessionid (tuio/property s (id property))
    * angle (tuio/property a)
    * angle3D (tuio/property a, b, c)
    * rotacc (tuio/property A)
    * rotacc3d (tuio/property A, B, C)
    * motacc (tuio/property m)
    * shape (property shape)
    * kinetic
    * ... and others could be added by new classes

If you're only interested in a certain kind of touches, check the profile::

    def on_touch_down(self, touch):
        if 'markerid' not in touch.profile:
            # not a fiducial, not interesting
            return

'''

__all__ = ('Touch', )

import weakref
from inspect import isroutine
from copy import copy
from kivy.utils import SafeList
from kivy.clock import Clock
from kivy.vector import Vector


class TouchMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        __attrs__ = []
        for base in bases:
            if hasattr(base, '__attrs__'):
                __attrs__.extend(base.__attrs__)
        if '__attrs__' in attrs:
            __attrs__.extend(attrs['__attrs__'])
        attrs['__attrs__'] = tuple(__attrs__)
        return super(TouchMetaclass, mcs).__new__(mcs, name, bases, attrs)


class Touch(object):
    '''Abstract class to represent a touch, and support TUIO 1.0 definition.

    :Parameters:
        `id` : str
            uniq ID of the touch
        `args` : list
            list of parameters, passed to depack() function
    '''

    __metaclass__ = TouchMetaclass
    __uniq_id = 0
    __attrs__ = \
        ('device', 'attr',
         'id', 'sx', 'sy', 'sz', 'profile',
         'x', 'y', 'z', 'shape',
         'dxpos', 'dypos', 'dzpos',
         'oxpos', 'oypos', 'ozpos',
         'dsxpos', 'dsypos', 'dszpos',
         'osxpos', 'osypos', 'oszpos',
         'time_start', 'is_double_tap',
         'double_tap_time', 'userdata')

    def __init__(self, device, id, args):
        if self.__class__ == Touch:
            raise NotImplementedError, 'class Touch is abstract'

        # Uniq ID
        Touch.__uniq_id += 1
        self.uid = Touch.__uniq_id
        self.device = device

        # For push/pop
        self.attr = []
        self.default_attrs = (
            'x', 'y', 'z',
            'dxpos', 'dypos', 'dzpos',
            'oxpos', 'oypos', 'ozpos')

        # For grab
        self.grab_list = SafeList()
        self.grab_exclusive_class = None
        self.grab_state = False
        self.grab_current = None

        # TUIO definition
        self.id = id
        self.sx = 0.0
        self.sy = 0.0
        self.sz = 0.0
        self.profile = ('pos', )

        # new parameters
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.shape = None
        self.dxpos = None
        self.dypos = None
        self.dzpos = None
        self.oxpos = None
        self.oypos = None
        self.ozpos = None
        self.dsxpos = None
        self.dsypos = None
        self.dszpos = None
        self.osxpos = None
        self.osypos = None
        self.oszpos = None
        self.time_start = Clock.get_time()
        self.is_double_tap = False
        self.double_tap_time = 0
        self.userdata = {}

        self.depack(args)

    def depack(self, args):
        '''Depack `args` into attributes in class'''
        if self.dsxpos is None:
            self.dsxpos = self.osxpos = self.sx
            self.dsypos = self.osypos = self.sy
            self.dszpos = self.oszpos = self.sz

    def grab(self, class_instance, exclusive=False):
        '''Grab a touch. You can grab a touch if you absolutly want to receive
        on_touch_move() and on_touch_up(), even if the touch is not dispatched
        by your parent ::

            def on_touch_down(self, touch):
                touch.grab(self)

            def on_touch_move(self, touch):
                if touch.grab_current == self:
                    # i receive my grabbed touch
                else:
                    # it's a normal touch

            def on_touch_up(self, touch):
                if touch.grab_current == self:
                    # i receive my grabbed touch, i must ungrab it !
                    touch.ungrab(self)
                else:
                    # it's a normal touch

        '''
        if self.grab_exclusive_class is not None:
            raise Exception('Cannot grab the touch, touch are exclusive')
        class_instance = weakref.ref(class_instance)
        if exclusive:
            self.grab_exclusive_class = class_instance
        self.grab_list.append(class_instance)

    def ungrab(self, class_instance):
        '''Ungrab a previous grabbed touch'''
        class_instance = weakref.ref(class_instance)
        if self.grab_exclusive_class == class_instance:
            self.grab_exclusive_class = None
        if class_instance in self.grab_list:
            self.grab_list.remove(class_instance)

    def move(self, args):
        '''Move the touch to another position.'''
        self.dxpos = self.x
        self.dypos = self.y
        self.dzpos = self.z
        self.dsxpos = self.sx
        self.dsypos = self.sy
        self.dszpos = self.sz
        self.depack(args)

    def scale_for_screen(self, w, h, p=None, rotation=0):
        '''Scale position for the screen'''
        sx, sy = self.sx, self.sy
        if rotation == 0:
            self.x = sx * float(w)
            self.y = sy * float(h)
        elif rotation == 90:
            sx, sy = sy, 1-sx
            self.x = sx * float(h)
            self.y = sy * float(w)
        elif rotation == 180:
            sx, sy = 1-sx, 1-sy
            self.x = sx * float(w)
            self.y = sy * float(h)
        elif rotation == 270:
            sx, sy = 1-sy, sx
            self.x = sx * float(h)
            self.y = sy * float(w)

        if p:
            self.z = self.sz * float(p)
        if self.oxpos is None:
            self.dxpos = self.oxpos = self.x
            self.dypos = self.oypos = self.y
            self.dzpos = self.ozpos = self.z

    def push(self, attrs=None):
        '''Push attributes values in `attrs` in the stack'''
        if attrs is None:
            attrs = self.default_attrs
        values = [getattr(self, x) for x in attrs]
        self.attr.append((attrs, values))

    def pop(self):
        '''Pop attributes values from the stack'''
        attrs, values = self.attr.pop()
        for i in xrange(len(attrs)):
            setattr(self, attrs[i], values[i])

    def apply_transform_2d(self, transform):
        '''Apply a transformation on x, y, dxpos, dypos, oxpos, oypos'''
        self.x, self.y = transform(self.x, self.y)
        self.dxpos, self.dypos = transform(self.dxpos, self.dypos)
        self.oxpos, self.oypos = transform(self.oxpos, self.oypos)

    def copy_to(self, to):
        '''Copy some attribute to another touch object.'''
        for attr in self.__attrs__:
            to.__setattr__(attr, copy(self.__getattribute__(attr)))

    def __str__(self):
        classname = str(self.__class__).split('.')[-1].replace('>', '').replace('\'', '')
        return '<%s spos=%s pos=%s>' % (classname, str(self.spos), str(self.pos))

    def distance(self, other_touch):
        return Vector(self.pos).distance(other_touch.pos)

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
            ' '.join(out)
        )

    # facility
    @property
    def pos(self):
        '''Return position of the touch in the screen coordinate
        system (self.x, self.y)'''
        return self.x, self.y

    @property
    def dpos(self):
        '''Return previous position of the touch in the
        screen coordinate system (self.dxpos, self.dypos)'''
        return self.dxpos, self.dypos

    @property
    def opos(self):
        '''Return the initial position of the touch in the screen
        coordinate system (self.oxpos, self.oypos)'''
        return self.oxpos, self.oypos

    @property
    def spos(self):
        '''Return the position in the 0-1 coordinate system
        (self.sx, self.sy)'''
        return self.sx, self.sy

    # compatibility bridge
    xpos = property(lambda self: self.x)
    ypos = property(lambda self: self.y)
    blobID = property(lambda self: self.id)
