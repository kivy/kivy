'''
Widget: base widget of Kivy. 

TODO: write how the base class are working
+ add example about how to create your own widget
+ add example about how to bind from properties
+ do we need to use WeakMethod for properties ?
'''

__all__ = ('Widget', )

from kivy.weakmethod import WeakMethod
from kivy.c_ext.event import EventDispatcher
from kivy.c_ext.properties import *

class Widget(EventDispatcher):
    '''
    Widget is the very basic class for implementing any Kivy Widget.
    '''

    # UID counter
    __widget_uid = 0

    def __new__(cls, *largs, **kwargs):
        self = super(Widget, cls).__new__(cls)

        # XXX for the moment, we need to create a uniq id for properties.
        # Properties need a identifier to the class instance. hash() and id()
        # are longer than using a custom __uid. I hope we can figure out a way
        # of doing that without require any python code. :)
        Widget.__widget_uid += 1
        self.__dict__['__uid'] = Widget.__widget_uid

        # First loop, link all the properties storage to our instance
        attrs = cls.__dict__
        for k, attr in attrs.iteritems():
            if isinstance(attr, Property):
                attr.link(self, k)

        # Second loop, resolve all the reference
        for k, attr in attrs.iteritems():
            if isinstance(attr, Property):
                attr.link_deps(self, k)

        # Then, return the class instance
        return self

    def __del__(self):
        # The thing here, since the storage of the property is inside the
        # Property class, we must remove ourself from the storage of each
        # Property. The usage is faster, the creation / deletion is longer.
        attrs = self.__class__.__dict__
        for k, attr in attrs.iteritems():
            if isinstance(attr, Property):
                attr.unlink(self)

    def bind(self, **kwargs):
        '''Bind properties or event to handler

        Usage ::
            def my_x_callback(obj, value):
                print 'on object', obj', 'x changed to', value
            def my_width_callback(obj, value):
                print 'on object', obj, 'width changed to', value
            self.bind(x=my_x_callback, width=my_width_callback)
        '''
        super(Widget, self).bind(**kwargs)
        for key, value in kwargs.iteritems():
            if key.startswith('on_'):
                continue
            self.__class__.__dict__[key].bind(self, value)

    def unbind(self, **kwargs):
        '''Unbind properties or event from handler

        Same usage as bind().
        '''
        super(Widget, self).unbind(**kwargs)
        for key, value in kwargs.iteritems():
            if key.startswith('on_'):
                continue

            self.__class__.__dict__[key].unbind(self, value)

    def setter(self, name):
        '''Return the setter of a property. Useful if you want to directly bind
        a property to another. For example ::

            self.bind(right=nextchild.setter('x'))
        '''
        return self.__class__.__dict__[name].__set__

    def getter(self, name):
        '''Return the getter of a property.
        '''
        return self.__class__.__dict__[name].__get__


    #
    # Properties
    #

    #: X position of the widget
    x = NumericProperty(0)

    #: Y position of the widget
    y = NumericProperty(0)

    #: Width of the widget
    width = NumericProperty(100)

    #: Height of the widget
    height = NumericProperty(100)

    #: Position of the widget (x, y)
    pos = ReferenceListProperty(x, y)

    #: Size of the widget (width, height)
    size = ReferenceListProperty(width, height)

    def get_right(self):
        return self.x + self.width
    def set_right(self, value):
        self.x = value - self.width

    #: Right position of the widget (x + width)
    right = AliasProperty(get_right, set_right, bind=(x, width))

    def get_top(self):
        return self.y + self.height
    def set_top(self, value):
        self.y = value - self.height

    #: Top position of the widget (y + height)
    top = AliasProperty(get_top, set_top, bind=(y, height))

    def get_center(self):
        return [self.x + self.width / 2.,
                self.y + self.height / 2.]
    def set_center(self, value):
        self.x = value[0] - self.width / 2.
        self.y = value[1] - self.height / 2.

    #: Center position of the widget (x + width / 2, y + height / 2)
    center = AliasProperty(get_center, set_center, bind=(x, y, width, height))

    #: Class of the widget, used for style
    cls = ListProperty([])

    #: User id of the widget
    id = StringProperty(None, allownone=True)
