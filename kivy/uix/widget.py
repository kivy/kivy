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
from kivy.graphics import Canvas
from kivy.base import EventLoop
from kivy.uxl import Uxl

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
        attrs = dir(cls)
        for k in attrs:
            attr = getattr(cls, k)
            if isinstance(attr, Property):
                attr.link(self, k)

        # Second loop, resolve all the reference
        for k in attrs:
            attr = getattr(cls, k)
            if isinstance(attr, Property):
                attr.link_deps(self, k)

        # Then, return the class instance
        return self

    def __del__(self):
        # The thing here, since the storage of the property is inside the
        # Property class, we must remove ourself from the storage of each
        # Property. The usage is faster, the creation / deletion is longer.
        cls = self.__class__
        attrs = dir(cls)
        for k in attrs:
            attr = getattr(cls, k)
            if isinstance(attr, Property):
                attr.unlink(self)

    def __init__(self, **kwargs):
        super(Widget, self).__init__()
        self.register_event_type('on_touch_down')
        self.register_event_type('on_touch_move')
        self.register_event_type('on_touch_up')
        self.register_event_type('on_draw')

        EventLoop.ensure_window()
        self.canvas = Canvas()

        # Apply all the styles
        Uxl.apply(self)




    #
    # Collision
    #

    def collide_point(self, x, y):
        return self.x <= x <= self.right and self.y <= y <= self.top


    #
    # Default event handlers
    #

    def on_draw(self):
        '''Dispatch the on_draw even in every child
        '''
        self.draw()
        for child in self.children:
            child.dispatch('on_draw')

    def on_touch_down(self, touch):
        '''Send the touch down event in every child
        Return true if one child use it
        '''
        for child in reversed(self.children[:]):
            if child.dispatch('on_touch_down', touch):
                return True

    def on_touch_move(self, touch):
        '''Send the touch move event in every child
        Return true if one child use it
        '''
        for child in reversed(self.children[:]):
            if child.dispatch('on_touch_move', touch):
                return True

    def on_touch_up(self, touch):
        '''Send the touch down event in every child
        Return true if one child use it
        '''
        for child in reversed(self.children[:]):
            if child.dispatch('on_touch_up', touch):
                return True


    #
    # Drawing
    #
    def draw(self):
        '''Draw the widget
        '''
        self.canvas.draw()


    #
    # Events
    #

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
            getattr(self.__class__, key).bind(self, value)

    def unbind(self, **kwargs):
        '''Unbind properties or event from handler

        Same usage as bind().
        '''
        super(Widget, self).unbind(**kwargs)
        for key, value in kwargs.iteritems():
            if key.startswith('on_'):
                continue
            getattr(self.__class__, key).unbind(self, value)


    #
    # Tree management
    #

    def add_widget(self, widget):
        '''Add a new widget as a child of current widget
        '''
        widget.parent = self
        self.children = [widget] + self.children

    def remove_widget(self, widget):
        '''Remove a widget from the childs of current widget
        '''
        if widget in self.children:
            self.children = self.children.remove(widget)
            widget.parent = None

    def get_root_window(self):
        '''Return the root window
        '''
        if self.parent:
            return self.parent.get_root_window()

    def get_parent_window(self):
        '''Return the parent window
        '''
        if self.parent:
            return self.parent.get_parent_window()


    #
    # Properties
    #

    def setter(self, name):
        '''Return the setter of a property. Useful if you want to directly bind
        a property to another. For example ::

            self.bind(right=nextchild.setter('x'))
        '''
        return getattr(self.__class__, name).__set__

    def getter(self, name):
        '''Return the getter of a property.
        '''
        return getattr(self.__class__, name).__get__

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

    #: Children list
    children = ListProperty([])

    #: Parent
    parent = ObjectProperty(None)

    #: Size hint X
    size_hint_x = NumericProperty(1, allownone=True)

    #: Size hint Y
    size_hint_y = NumericProperty(1, allownone=True)

    #: Size hint
    size_hint = ReferenceListProperty(size_hint_x, size_hint_y)

    #: Canvas
    canvas = None

