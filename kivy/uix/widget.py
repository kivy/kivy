'''
Widget class
============

The :class:`Widget` class is the base class required to create a Widget.
Our widget class is designed with a couple of principles in mind:

    Event Driven
        The widget interaction is build on top of events that occur.
        If a property changes, the widget can do something. If nothing changes
        in the widget, nothing will be done. That's the main goal of the
        :class:`~kivy.properties.Property` class.

    Separate the widget and its graphical representation
        Widgets don't have a `draw()` method. This is done on purpose: The idea
        is to allow you to create your own graphical representation outside the
        widget class.
        Obviously you can still use all the available properties to do that, so
        that your representation properly reflects the widget's current state.
        Every widget has its own :class:`~kivy.graphics.Canvas` that you can use
        to draw. This separation allows Kivy to run your application in a very
        efficient manner.

    Bounding Box / Collision
        Often you want to know if a certain point is within the bounds of your
        widget. An example would be a button widget where you want to only
        trigger an action when the button itself is actually touched.
        For this, you can use the :func:`Widget.collide_point` method, which
        will return True if the point you pass it is inside the axis-aligned
        bounding box defined by the widgets position and size.
        If a simple AABB is not sufficient, you can override the method to
        perform the collision checks with more complex shapes (e.g. a polygon).
        You can also check if a widget collides with another widget with
        :func:`Widget.collide_widget`.

Using Properties
----------------

When you read the documentation, all properties are described in the format::

    <name> is a <property class>, defaults to <default value>

For example::

    :data:`Widget.pos` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:data:`Widget.x`, :data:`Widget.y`) properties.

If you want to be notified when the pos attribute changes (i.e. when the
widget moves), you can bind your own function (callback) like this::

    def callback_pos(instance, value):
        print 'The widget', instance, 'moved to', value

    wid = Widget()
    wid.bind(pos=callback_pos)

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
    '''Widget class. See module documentation for more information.

    :Events:
        `on_touch_down`:
            Fired when a new touch appear
        `on_touch_move`:
            Fired when an existing touch is moved
        `on_touch_up`:
            Fired when an existing touch disappears
    '''

    # UID counter
    __widget_uid = 0
    __cache_properties = {}

    def __new__(__cls__, *largs, **kwargs):
        self = super(Widget, __cls__).__new__(__cls__)

        # XXX for the moment, we need to create a uniq id for properties.
        # Properties need a identifier to the class instance. hash() and id()
        # are longer than using a custom __uid. I hope we can figure out a way
        # of doing that without require any python code. :)
        Widget.__widget_uid += 1
        self.__dict__['__uid'] = Widget.__widget_uid
        self.__dict__['__storage'] = {}

        cp = Widget.__cache_properties
        if __cls__ not in cp:
            attrs_found = cp[__cls__] = {}
            attrs = dir(__cls__)
            for k in attrs:
                attr = getattr(__cls__, k)
                if isinstance(attr, Property):
                    if k in Widget_forbidden_properties:
                        raise Exception(
                            'The property <%s> have a forbidden name' % k)
                    attrs_found[k] = attr
        else:
            attrs_found = cp[__cls__]

        # First loop, link all the properties storage to our instance
        for k, attr in attrs_found.iteritems():
            attr.link(self, k)

        # Second loop, resolve all the reference
        for k, attr in attrs_found.iteritems():
            attr.link_deps(self, k)

        self.__properties = attrs_found

        # Then, return the class instance
        return self

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

        # Create the default canvas if not exist
        if self.canvas is None:
            self.canvas = Canvas()

        # Apply the existing arguments to our widget
        for key, value in kwargs.iteritems():
            if key in properties:
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

        The class of the property cannot be specified, it will always be an
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
        setattr(self.__class__, name, prop)


    #
    # Collision
    #
    def collide_point(self, x, y):
        '''Check if a point (x, y) is inside the widget's axis aligned bounding
        box.

        :Parameters:
            `x`: numeric
                X position of the point (in window coordinates)
            `y`: numeric
                Y position of the point (in window coordinates)

        :Returns:
            bool, True if the point is inside the bounding box.

        >>> Widget(pos=(10, 10), size=(50, 50)).collide_point(40, 40)
        True
        '''
        return self.x <= x <= self.right and self.y <= y <= self.top

    def collide_widget(self, wid):
        '''Check if the other widget collides with this widget.
        Performs an axis-aligned bounding box intersection test by default.

        :Parameters:
            `wid`: :class:`Widget` class
                Widget to collide with.

        :Returns:
            bool, True if the other widget collides with this widget.

        >>> wid = Widget(size=(50, 50))
        >>> wid2 = Widget(size=(50, 50), pos=(25, 25))
        >>> wid.collide_widget(wid2)
        True
        >>> wid2.pos = (55, 55)
        >>> wid.collide_widget(wid2)
        False
        '''
        if self.right < wid.x:
            return False
        if self.x > wid.right:
            return False
        if self.top < wid.y:
            return False
        if self.y > wid.top:
            return False
        return True


    #
    # Default event handlers
    #
    def on_touch_down(self, touch):
        '''Receive a touch down event.

        :Parameters:
            `touch`: :class:`~kivy.input.motionevent.MotionEvent` class
                Touch received

        :Returns:
            bool. If True, the dispatching of the touch will stop.
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
        '''Bind properties or events to a handler.

        Example usage::

            def my_x_callback(obj, value):
                print 'on object', obj, 'x changed to', value
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
        '''Unbind properties or events from their handler.

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
    def add_widget(self, widget, index=0):
        '''Add a new widget as a child of this widget.

        :Parameters:
            `widget`: :class:`Widget`
                Widget to add to our list of children.
            `index`: int, default to 0
                *(this attribute have been added in 1.0.5)*
                Index to insert the widget in the list

        >>> root = Widget()
        >>> root.add_widget(Button())
        >>> slider = Slider()
        >>> root.add_widget(slider)
        '''
        if not isinstance(widget, Widget):
            raise WidgetException(
                'add_widget() can be used only with Widget classes.')
        widget.parent = self
        if index == 0 or len(self.children) == 0:
            self.children.insert(0, widget)
            self.canvas.add(widget.canvas)
        else:
            canvas = self.canvas
            children = self.children
            if index >= len(children):
                index = len(children)
                next_index = 0
            else:
                next_child = children[index]
                next_index = canvas.indexof(next_child.canvas)
                if next_index == -1:
                    next_index = canvas.length()
                else:
                    next_index += 1

            children.insert(index, widget)
            canvas.insert(next_index, widget.canvas)

    def remove_widget(self, widget):
        '''Remove a widget from the children of this widget.

        :Parameters:
            `widget`: :class:`Widget`
                Widget to remove from our children list.

        >>> root = Widget()
        >>> button = Button()
        >>> root.add_widget(button)
        >>> root.remove_widget(button)
        '''
        if widget not in self.children:
            return
        self.children.remove(widget)
        self.canvas.remove(widget.canvas)
        widget.parent = None

    def clear_widgets(self):
        '''Remove all widgets added to this widget.
        '''
        remove_widget = self.remove_widget
        for child in self.children[:]:
            remove_widget(child)

    def get_root_window(self):
        '''Return the root window.

        :Returns:
            Instance of the root window. Can be
            :class:`~kivy.core.window.WindowBase` or
            :class:`Widget`
        '''
        if self.parent:
            return self.parent.get_root_window()

    def get_parent_window(self):
        '''Return the parent window.

        :Returns:
            Instance of the parent window. Can be
            :class:`~kivy.core.window.WindowBase` or
            :class:`Widget`
        '''
        if self.parent:
            return self.parent.get_parent_window()

    def to_widget(self, x, y, relative=False):
        '''Convert the given coordinate from window to local widget
        coordinates.
        '''
        if self.parent:
            x, y = self.parent.to_widget(x, y)
        return self.to_local(x, y, relative=relative)

    def to_window(self, x, y, initial=True, relative=False):
        '''Transform local coordinates to window coordinates.'''
        if not initial:
            x, y = self.to_parent(x, y, relative=relative)
        if self.parent:
            return self.parent.to_window(x, y, initial=False, relative=relative)
        return (x, y)

    def to_parent(self, x, y, relative=False):
        '''Transform local coordinates to parent coordinates.

        :Parameters:
            `relative`: bool, default to False
                Change to True if you want to translate relative positions from
                widget to its parent.
        '''
        if relative:
            return (x + self.x, y + self.y)
        return (x, y)

    def to_local(self, x, y, relative=False):
        '''Transform parent coordinates to local coordinates.

        :Parameters:
            `relative`: bool, default to False
                Change to True if you want to translate coordinates to
                relative widget coordinates.
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

    def get_uid(self):
        return self.__dict__['__uid']
    uid = AliasProperty(get_uid, None)
    '''Unique identifier of the widget in the whole Kivy instance.

    .. versionadded:: 1.0.7

    :data:`uid` is a :class:`~kivy.properties.AliasProperty`, read-only.
    '''

    id = StringProperty(None, allownone=True)
    '''Unique identifier of the widget in the tree.

    :data:`id` is a :class:`~kivy.properties.StringProperty`, default to None.

    .. warning::

        If the :data:`id` is already used in the tree, an exception will
        be raised.
    '''

    children = ListProperty([])
    '''List of children of this widget

    :data:`children` is a :class:`~kivy.properties.ListProperty` instance,
    default to an empty list.

    Use :func:`add_widget` and :func:`remove_widget` for manipulate children
    list. Don't manipulate children list directly until you know what you are
    doing.
    '''

    parent = ObjectProperty(None, allownone=True)
    '''Parent of this widget

    :data:`parent` is a :class:`~kivy.properties.ObjectProperty` instance,
    default to None.

    The parent of a widget is set when the widget is added to another one, and
    unset when the widget is removed from his parent.
    '''

    size_hint_x = NumericProperty(1, allownone=True)
    '''X size hint. It represents how much space the widget should use in the
    direction of the X axis, relative to its parent's width.
    Only :class:`~kivy.uix.layout.Layout` and
    :class:`~kivy.core.window.Window` make use of the hint.

    The value is in percent as a float from 0. to 1., where 1. means the full
    size of his parent, i.e. 100%. 0.5 represents 50%.

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

    pos_hint = ObjectProperty({})
    '''Position hint. This property allows you to set the position of the widget
    inside its parent layout, in percent (similar to size_hint).

    For example, if you want to set the top of the widget to be at 90% height of
    its parent layout, you can write:

        widget = Widget(pos_hint={'top': 0.9})

    The keys 'x', 'right', 'center_x', will use the parent width.
    The keys 'y', 'top', 'center_y', will use the parent height.

    Check :doc:`api-kivy.uix.floatlayout` for further reference.

    Position hint is only used in :class:`~kivy.uix.floatlayout.FloatLayout` and
    :class:`~kivy.core.window.Window`.

    :data:`pos_hint` is a :class:`~kivy.properties.ObjectProperty` containing a
    dict.
    '''

    canvas = None
    '''Canvas of the widget.

    The canvas is a graphics object that contains all the drawing instructions
    for the graphical representation of the widget.
    Check :class:`~kivy.graphics.Canvas` for more information about the usage.
    '''
