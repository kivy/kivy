'''
Widget class
============

TODO: write how the base class are working

* add example about how to create your own widget
* add example about how to bind from properties
* do we need to use WeakMethod for properties ?
'''

__all__ = ('Widget', 'WidgetException')

from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, StringProperty, \
        AliasProperty, ReferenceListProperty, Property, ObjectProperty, \
        ListProperty
from kivy.graphics import Canvas
from kivy.base import EventLoop
from kivy.lang import Builder

Widget_forbidden_properties = ('touch_down', 'touch_move', 'touch_up')


class WidgetException(Exception):
    '''Fired when the widget got an exception
    '''
    pass


class Widget(EventDispatcher):
    '''
    Widget is the very basic class for implementing any Kivy Widget.

    :Events:
        `on_touch_down`:
            Fired when a new touch appear
        `on_touch_move`:
            Fired when an existing touch is moved
        `on_touch_down`:
            Fired when an existing touch disapear
    '''

    # UID counter
    __widget_uid = 0

    def __new__(__cls__, *largs, **kwargs):
        self = super(Widget, __cls__).__new__(__cls__)

        # XXX for the moment, we need to create a uniq id for properties.
        # Properties need a identifier to the class instance. hash() and id()
        # are longer than using a custom __uid. I hope we can figure out a way
        # of doing that without require any python code. :)
        Widget.__widget_uid += 1
        self.__dict__['__uid'] = Widget.__widget_uid

        # First loop, link all the properties storage to our instance
        attrs_found = {}
        attrs = dir(__cls__)
        for k in attrs:
            attr = getattr(__cls__, k)
            if isinstance(attr, Property):
                if k in Widget_forbidden_properties:
                    raise Exception(
                        'The property <%s> have a forbidden name' % k)
                attr.link(self, k)
                attrs_found[k] = attr

        # Second loop, resolve all the reference
        for k in attrs:
            attr = getattr(__cls__, k)
            if isinstance(attr, Property):
                attr.link_deps(self, k)

        self.__properties = attrs_found

        # Then, return the class instance
        return self

    def __del__(self):
        # The thing here, since the storage of the property is inside the
        # Property class, we must remove ourself from the storage of each
        # Property. The usage is faster, the creation / deletion is longer.
        for attr in self.__properties.itervalues():
            attr.unlink(self)

    def __init__(self, **kwargs):
        super(Widget, self).__init__()

        # Register touch events
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

        # Create the default canvas
        self.canvas = Canvas()

        # Apply the existing arguments to our widget
        for key, value in kwargs.iteritems():
            if hasattr(self, key):
                setattr(self, key, value)

        # Apply all the styles
        if '__no_builder' not in kwargs:
            Builder.apply(self)

    def create_property(self, name):
        '''Create a new property at runtime.

        .. warning::

            This function is designed for the Kivy language, don't use it in
            your code. You should declare the property in your class instead of
            using this method.

        :Parameters:
            `name`: string
                Name of the property

        The class of the property cannot be specified, it will be always an
        :class:`~kivy.properties.ObjectProperty` class. The default value of the
        property will be None, until you set a new value.

        >>> mywidget = Widget()
        >>> mywidget.create_property('custom')
        >>> mywidget.custom = True
        >>> print mywidget.custom
        True
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
        '''Check if a point (x, y) is inside the widget bounding box.

        :Parameters:
            `x`: numeric
                X position of the point
            `y`: numeric
                Y position of the point

        :Returns:
            bool, True if the point is inside the bounding box

        >>> Widget(pos=(10, 10), size=(50, 50)).collide_point(40, 40)
        True
        '''
        return self.x <= x <= self.right and self.y <= y <= self.top


    #
    # Default event handlers
    #
    def on_touch_down(self, touch):
        '''Receive a touch down event

        :Parameters:
            `touch`: :class:`~kivy.input.motionevent.MotionEvent` class
                Touch received

        :Returns:
            bool. If True, the dispatching will stop.
        '''
        for child in self.children[:]:
            if child.dispatch('on_touch_down', touch):
                return True

    def on_touch_move(self, touch):
        '''Receive a touch move event.

        See :func:`on_touch_down` for more information
        '''
        for child in self.children[:]:
            if child.dispatch('on_touch_move', touch):
                return True

    def on_touch_up(self, touch):
        '''Receive a touch up event.

        See :func:`on_touch_down` for more information
        '''
        for child in self.children[:]:
            if child.dispatch('on_touch_up', touch):
                return True


    #
    # Events
    #
    def bind(self, **kwargs):
        '''Bind properties or event to handler.

        Example of usage::

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

        See :func:`bind()` for more information.
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

        :Parameters:
            `widget`: :class:`Widget`
                Widget to add in our children list.

        >>> root = Widget()
        >>> root.add_widget(Button())
        >>> slider = Slider()
        >>> root.add_widget(slider)
        '''
        if not isinstance(widget, Widget):
            raise WidgetException(
                'add_widget() can be used only with Widget classes.')
        widget.parent = self
        self.children = [widget] + self.children
        self.canvas.add(widget.canvas)

    def remove_widget(self, widget):
        '''Remove a widget from the children of current widget

        :Parameters:
            `widget`: :class:`Widget`
                Widget to add in our children list.

        >>> root = Widget()
        >>> button = Button()
        >>> root.add_widget(button)
        >>> root.remove_widget(button)
        '''
        if widget not in self.children:
            return
        self.children.remove(widget)
        self.children = self.children[:]
        self.canvas.remove(widget.canvas)
        widget.parent = None

    def clear_widgets(self):
        '''Remove all widgets added to the widget.
        '''
        remove_widget = self.remove_widget
        for child in self.children[:]:
            remove_widget(child)

    def get_root_window(self):
        '''Return the root window

        :Returns:
            Instance of the root window. Can be
            :class:`~kivy.core.window.WindowBase` or
            :class:`Widget`
        '''
        if self.parent:
            return self.parent.get_root_window()

    def get_parent_window(self):
        '''Return the parent window

        :Returns:
            Instance of the root window. Can be
            :class:`~kivy.core.window.WindowBase` or
            :class:`Widget`
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
        a property to another.

        For example, if you want to position one widget next to you ::

            self.bind(right=nextchild.setter('x'))
        '''
        return self.__properties[name].__set__

    def getter(self, name):
        '''Return the getter of a property.
        '''
        return self.__properties[name].__get__

    x = NumericProperty(0)
    '''X position of the widget.

    :data:`x` is a :class:`~kivy.properties.NumericProperty`, default to 0.
    '''

    y = NumericProperty(0)
    '''Y position of the widget.

    :data:`y` is a :class:`~kivy.properties.NumericProperty`, default to 0.
    '''

    width = NumericProperty(100)
    '''Width of the widget.

    :data:`width` is a :class:`~kivy.properties.NumericProperty`, default
    to 100.
    '''

    height = NumericProperty(100)
    '''Height of the widget.

    :data:`height` is a :class:`~kivy.properties.NumericProperty`, default
    to 100.
    '''

    pos = ReferenceListProperty(x, y)
    '''Position of the widget.

    :data:`pos` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:data:`x`, :data:`y`) properties.
    '''

    size = ReferenceListProperty(width, height)
    '''Size of the widget.

    :data:`size` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:data:`width`, :data:`height`) properties.
    '''

    def get_right(self):
        return self.x + self.width

    def set_right(self, value):
        self.x = value - self.width

    right = AliasProperty(get_right, set_right, bind=('x', 'width'))
    '''Right position of the widget

    :data:`right` is a :class:`~kivy.properties.AliasProperty` of
    (:data:`x` + :data:`width`)
    '''

    def get_top(self):
        return self.y + self.height

    def set_top(self, value):
        self.y = value - self.height

    top = AliasProperty(get_top, set_top, bind=('y', 'height'))
    '''Top position of the widget

    :data:`top` is a :class:`~kivy.properties.AliasProperty` of
    (:data:`y` + :data:`height`)
    '''

    def get_center_x(self):
        return self.x + self.width / 2.

    def set_center_x(self, value):
        self.x = value - self.width / 2.
    center_x = AliasProperty(get_center_x, set_center_x, bind=('x', 'width'))
    '''X center position of the widget

    :data:`center_x` is a :class:`~kivy.properties.AliasProperty` of
    (:data:`x` + :data:`width` / 2.)
    '''

    def get_center_y(self):
        return self.y + self.height / 2.

    def set_center_y(self, value):
        self.y = value - self.height / 2.
    center_y = AliasProperty(get_center_y, set_center_y, bind=('y', 'height'))
    '''Y center position of the widget

    :data:`center_y` is a :class:`~kivy.properties.AliasProperty` of
    (:data:`y` + :data:`height` / 2.)
    '''

    center = ReferenceListProperty(center_x, center_y)
    '''Center position of the widget

    :data:`center` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:data:`center_x`, :data:`center_y`)
    '''

    cls = ListProperty([])
    '''Class of the widget, used for styling.
    '''

    id = StringProperty(None, allownone=True)
    '''Uniq identifier of the widget in the tree.

    :data:`id` is a :class:`~kivy.properties.StringProperty`, default to None.

    .. warning::

        If the :data:`id` is already used in the tree, an exception will
        occur.
    '''

    children = ListProperty([])
    '''Children list

    :data:`children` is a :class:`~kivy.properties.ListProperty` instance,
    default to an empty list.

    Use :func:`add_widget` and :func:`remove_widget` for manipulate children
    list. Don't manipulate children list directly until you know what you are
    doing.
    '''

    parent = ObjectProperty(None, allownone=True)
    '''Parent of the widget

    :data:`parent` is a :class:`~kivy.properties.ObjectProperty` instance,
    default to None.

    The parent of a widget is set when the widget is added to another one, and
    unset when the widget is removed from his parent.
    '''

    size_hint_x = NumericProperty(1, allownone=True)
    '''X size hint. It represent how much space the widget should use in the X
    axis from his parent. Only :class:`~kivy.uix.layout.Layout` and
    :class:`~kivy.core.window.Window` are using the hint.

    Value is in percent, 1. will mean the full size of his parent, aka 100%. 0.5
    will represent 50%.

    :data:`size_hint_x` is a :class:`~kivy.properties.NumericProperty`, default
    to 1.
    '''

    size_hint_y = NumericProperty(1, allownone=True)
    '''Y size hint.

    :data:`size_hint_y` is a :class:`~kivy.properties.NumericProperty`, default
    to 1.

    See :data:`size_hint_x` for more information
    '''

    size_hint = ReferenceListProperty(size_hint_x, size_hint_y)
    '''Size hint.

    :data:`size_hint` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:data:`size_hint_x`, :data:`size_hint_y`)

    See :data:`size_hint_x` for more information
    '''

    canvas = None
    '''Canvas of the widget.

    The canvas is a graphics object that contain all the drawing instruction.
    Check :class:`~kivy.graphics.Canvas` for more information about usage.
    '''

