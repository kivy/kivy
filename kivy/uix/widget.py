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
from kivy.lang import Builder

Widget_forbidden_properties = ('touch_down', 'touch_move', 'touch_up')

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
        attrs_found = {}
        attrs = dir(cls)
        for k in attrs:
            attr = getattr(cls, k)
            if isinstance(attr, Property):
                if k in Widget_forbidden_properties:
                    raise Exception(
                        'The property <%s> have a forbidden name' % k)
                attr.link(self, k)
                attrs_found[k] = attr

        # Second loop, resolve all the reference
        for k in attrs:
            attr = getattr(cls, k)
            if isinstance(attr, Property):
                attr.link_deps(self, k)

        self.__properties = attrs_found

        # Then, return the class instance
        return self

    def __del__(self):
        # The thing here, since the storage of the property is inside the
        # Property class, we must remove ourself from the storage of each
        # Property. The usage is faster, the creation / deletion is longer.
        for attr in self._properties.itervalues():
            attr.unlink(self)

    def __init__(self, **kwargs):
        super(Widget, self).__init__()
        self.register_event_type('on_touch_down')
        self.register_event_type('on_touch_move')
        self.register_event_type('on_touch_up')

        # Before doing anything, ensure the windows exist.
        EventLoop.ensure_window()

        # Auto bind on own handler if exist
        properties = self.__properties.keys()
        for func in dir(self):
            if not func.startswith('on_'):
                continue
            name = func[3:]
            if name in properties:
                self.bind(**{name: getattr(self, func)})

        # Apply the existing arguments to our widget
        for key, value in kwargs.iteritems():
            if hasattr(self, key):
                setattr(self, key, value)

        # Create the default canvas
        self.canvas = Canvas()

        # Apply all the styles
        if '__no_builder' not in kwargs:
            print 'APPLY', self
            Builder.apply(self)


    def create_property(self, name):
        '''Create on live a new property. Unfortunatly, you cannot specify
        the type of the property. It will be an ObjectProperty with None value
        by default, until you set a new value.
        '''
        prop = ObjectProperty(None)
        prop.link(self, name)
        prop.link_deps(self, name)
        self.__properties[name] = prop
        setattr(self, name, prop)


    #
    # Collision
    #

    def collide_point(self, x, y):
        return self.x <= x <= self.right and self.y <= y <= self.top


    #
    # Default event handlers
    #

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
            self.__properties[key].bind(self, value)

    def unbind(self, **kwargs):
        '''Unbind properties or event from handler

        Same usage as bind().
        '''
        super(Widget, self).unbind(**kwargs)
        for key, value in kwargs.iteritems():
            if key.startswith('on_'):
                continue
            self.__properties[key].unbind(self, value)


    #
    # Tree management
    #

    def add_widget(self, widget):
        '''Add a new widget as a child of current widget
        '''
        widget.parent = self
        self.children = [widget] + self.children
        self.canvas.add_canvas(widget.canvas)

    def remove_widget(self, widget):
        '''Remove a widget from the childs of current widget
        '''
        if widget not in self.children:
            return
        self.children = self.children.remove(widget)
        self.canvas.remove_canvas(widget.canvas)
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

    def to_widget(self, x, y, relative=False):
        '''Return the coordinate from window to local widget'''
        if self.parent:
            x, y = self.parent.to_widget(x, y)
        return self.to_local(x, y, relative=relative)

    def to_window(self, x, y, initial=True, relative=False):
        '''Transform local coordinate to window coordinate'''
        if not initial:
            x, y = self.to_parent(x, y, relative=relative)
        if self.parent:
            return self.parent.to_window(x, y, initial=False, relative=relative)
        return (x, y)

    def to_parent(self, x, y, relative=False):
        '''Transform local coordinate to parent coordinate

        :Parameters:
            `relative`: bool, default to False
                Change to True is you want to translate relative position from
                widget to his parent.
        '''
        if relative:
            return (x + self.x, y + self.y)
        return (x, y)

    def to_local(self, x, y, relative=False):
        '''Transform parent coordinate to local coordinate

        :Parameters:
            `relative`: bool, default to False
                Change to True is you want to translate a coordinate to a
                relative coordinate from widget.
        '''
        if relative:
            return (x - self.x, y - self.y)
        return (x, y)


    #
    # Properties
    #

    def setter(self, name):
        '''Return the setter of a property. Useful if you want to directly bind
        a property to another. For example ::

            self.bind(right=nextchild.setter('x'))
        '''
        return self.__properties[name].__set__

    def getter(self, name):
        '''Return the getter of a property.
        '''
        return self.__properties[name].__get__

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

    #: X center position
    def get_center_x(self):
        return self.x + self.width / 2.
    def set_center_x(self, value):
        self.x = value - self.width / 2.
    center_x = AliasProperty(get_center_x, set_center_x, bind=(x, width))

    #: Y center position
    def get_center_y(self):
        return self.y + self.height / 2.
    def set_center_y(self, value):
        self.y = value - self.height / 2.
    center_y = AliasProperty(get_center_y, set_center_y, bind=(y, height))

    #: Center position of the widget (x + width / 2, y + height / 2)
    center = ReferenceListProperty(center_x, center_y)

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

