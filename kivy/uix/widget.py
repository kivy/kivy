'''
Widget class
============

The :class:`Widget` class is the base class required to create a Widget.
Our widget class is designed with a couple of principles in mind:

    Event Driven
        The widget interaction is built on top of events that occur.
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
        For this, you can use the :meth:`Widget.collide_point` method, which
        will return True if the point you pass it is inside the axis-aligned
        bounding box defined by the widget's position and size.
        If a simple AABB is not sufficient, you can override the method to
        perform the collision checks with more complex shapes, e.g., a polygon.
        You can also check if a widget collides with another widget with
        :meth:`Widget.collide_widget`.


We also have some defaults that you should be aware of:

* A :class:`Widget` is not a :class:`Layout`: it will not change the position
  nor the size of its children. If you want a better positionning / sizing, use
  a :class:`Layout`.

* The default size is (100, 100), if the parent is not a :class:`Layout`. For
  example, adding a widget inside a :class:`Button`, :class:`Label`, will not
  inherit from the parent size or pos.

* The default size_hint is (1, 1). If the parent is a :class:`Layout`, then the
  widget size will be the parent/layout size.

* :meth:`Widget.on_touch_down`, :meth:`Widget.on_touch_move`,
  :meth:`Widget.on_touch_up` don't do any sort of collisions. If you want to
  know if the touch is inside your widget, use :meth:`Widget.collide_point`.

Using Properties
----------------

When you read the documentation, all properties are described in the format::

    <name> is a <property class>, defaults to <default value>

For example::

    :data:`Widget.pos` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:data:`Widget.x`, :data:`Widget.y`) properties.

If you want to be notified when the pos attribute changes, i.e., when the
widget moves, you can bind your own callback function like this::

    def callback_pos(instance, value):
        print('The widget', instance, 'moved to', value)

    wid = Widget()
    wid.bind(pos=callback_pos)

Read more about the :doc:`/api-kivy.properties`.

'''

__all__ = ('Widget', 'WidgetException')

from kivy.event import EventDispatcher
from kivy.factory import Factory
from kivy.properties import (NumericProperty, StringProperty, AliasProperty,
                             ReferenceListProperty, ObjectProperty,
                             ListProperty, DictProperty, BooleanProperty)
from kivy.graphics import Canvas
from kivy.base import EventLoop
from kivy.lang import Builder
from kivy.context import get_current_context
from weakref import proxy
from functools import partial


# references to all the destructors widgets (partial method with widget uid as
# key.)
_widget_destructors = {}


def _widget_destructor(uid, r):
    # internal method called when a widget is deleted from memory. the only
    # thing we remember about it is its uid. Clear all the associated callback
    # created in kv language.
    del _widget_destructors[uid]
    Builder.unbind_widget(uid)


class WidgetException(Exception):
    '''Fired when the widget gets an exception.
    '''
    pass


class WidgetMetaclass(type):
    '''Metaclass to auto register new widget into :class:`~kivy.factory.Factory`

    .. warning::
        This metaclass is used for Widget. Don't use it directly !
    '''
    def __init__(mcs, name, bases, attrs):
        super(WidgetMetaclass, mcs).__init__(name, bases, attrs)
        Factory.register(name, cls=mcs)


#: Base class used for widget, that inherit from :class:`EventDispatcher`
WidgetBase = WidgetMetaclass('WidgetBase', (EventDispatcher, ), {})


class Widget(WidgetBase):
    '''Widget class. See module documentation for more information.

    :Events:
        `on_touch_down`:
            Fired when a new touch happens
        `on_touch_move`:
            Fired when an existing touch is moved
        `on_touch_up`:
            Fired when an existing touch disappears

    .. versionchanged:: 1.0.9
        Everything related to event properties has been moved to
        :class:`~kivy.event.EventDispatcher`. Event properties can now be used
        in contructing a simple class, without subclassing :class:`Widget`.

    .. versionchanged:: 1.5.0
        Constructor now accept on_* arguments to automatically bind callbacks to
        properties or events, as the Kv language.
    '''

    __metaclass__ = WidgetMetaclass
    __events__ = ('on_touch_down', 'on_touch_move', 'on_touch_up')

    def __init__(self, **kwargs):
        # Before doing anything, ensure the windows exist.
        EventLoop.ensure_window()

        # assign the default context of the widget creation
        if not hasattr(self, '_context'):
            self._context = get_current_context()

        super(Widget, self).__init__(**kwargs)

        # Create the default canvas if not exist
        if self.canvas is None:
            self.canvas = Canvas(opacity=self.opacity)

        # Apply all the styles
        if '__no_builder' not in kwargs:
            #current_root = Builder.idmap.get('root')
            #Builder.idmap['root'] = self
            Builder.apply(self)
            #if current_root is not None:
            #    Builder.idmap['root'] = current_root
            #else:
            #    Builder.idmap.pop('root')

        # Bind all the events
        for argument in kwargs:
            if argument[:3] == 'on_':
                self.bind(**{argument: kwargs[argument]})

    @property
    def proxy_ref(self):
        '''Return a proxy reference to the widget, ie, without taking a
        reference of the widget. See `weakref.proxy
        <http://docs.python.org/2/library/weakref.html?highlight\
        =proxy#weakref.proxy>`_ for more information about it.

        .. versionadded:: 1.7.2
        '''
        if hasattr(self, '_proxy_ref'):
            return self._proxy_ref

        f = partial(_widget_destructor, self.uid)
        self._proxy_ref = _proxy_ref = proxy(self, f)
        # only f should be enough here, but it appears that is a very
        # specific case, the proxy destructor is not called if both f and
        # _proxy_ref are not together in a tuple
        _widget_destructors[self.uid] = (f, _proxy_ref)
        return _proxy_ref

    def __eq__(self, other):
        if not isinstance(other, Widget):
            return False
        return self.proxy_ref is other.proxy_ref

    def __hash__(self):
        return id(self)

    @property
    def __self__(self):
        return self

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
        if self.disabled and self.collide_point(*touch.pos):
            return True
        for child in self.children[:]:
            if child.dispatch('on_touch_down', touch):
                return True

    def on_touch_move(self, touch):
        '''Receive a touch move event.

        See :meth:`on_touch_down` for more information
        '''
        if self.disabled:
            return
        for child in self.children[:]:
            if child.dispatch('on_touch_move', touch):
                return True

    def on_touch_up(self, touch):
        '''Receive a touch up event.

        See :meth:`on_touch_down` for more information
        '''
        if self.disabled:
            return
        for child in self.children[:]:
            if child.dispatch('on_touch_up', touch):
                return True

    def on_disabled(self, instance, value):
        for child in self.children:
            child.disabled = value

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

        widget = widget.__self__
        if widget is self:
            raise WidgetException('You cannot add yourself in a Widget')
        parent = widget.parent
        # check if widget is already a child of another widget
        if parent:
            raise WidgetException('Cannot add %r, it already has a parent %r'
                % (widget, parent))
        widget.parent = parent = self
        # child will be disabled if added to a disabled parent
        if parent.disabled:
            widget.disabled = True

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
            # we never want to insert widget _before_ canvas.before.
            if next_index == 0 and canvas.has_before:
                next_index = 1
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
        parent = widget.parent
        self.children.remove(widget)
        self.canvas.remove(widget.canvas)
        widget.parent = None

    def clear_widgets(self, children=None):
        '''Remove all widgets added to this widget.

        .. versionchanged:: 1.8.0

            `children` argument can be used to select the children we want to
            remove. It should be a children list (or filtered list) of the
            current widget.
        '''

        if not children:
            children = self.children
        remove_widget = self.remove_widget
        for child in children[:]:
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
    
    .. warning::
        Keep in mind that the `width` property is subject to layout logic, and
        that this has not happened yet at the time of the widget's `__init__`
        method.
    '''

    height = NumericProperty(100)
    '''Height of the widget.

    :data:`height` is a :class:`~kivy.properties.NumericProperty`, default
    to 100.

    .. warning::
        Keep in mind that the `height` property is subject to layout logic, and
        that this has not happened yet at the time of the widget's `__init__`
        method.
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
    '''Right position of the widget.

    :data:`right` is a :class:`~kivy.properties.AliasProperty` of
    (:data:`x` + :data:`width`)
    '''

    def get_top(self):
        return self.y + self.height

    def set_top(self, value):
        self.y = value - self.height

    top = AliasProperty(get_top, set_top, bind=('y', 'height'))
    '''Top position of the widget.

    :data:`top` is a :class:`~kivy.properties.AliasProperty` of
    (:data:`y` + :data:`height`)
    '''

    def get_center_x(self):
        return self.x + self.width / 2.

    def set_center_x(self, value):
        self.x = value - self.width / 2.
    center_x = AliasProperty(get_center_x, set_center_x, bind=('x', 'width'))
    '''X center position of the widget.

    :data:`center_x` is a :class:`~kivy.properties.AliasProperty` of
    (:data:`x` + :data:`width` / 2.)
    '''

    def get_center_y(self):
        return self.y + self.height / 2.

    def set_center_y(self, value):
        self.y = value - self.height / 2.
    center_y = AliasProperty(get_center_y, set_center_y, bind=('y', 'height'))
    '''Y center position of the widget.

    :data:`center_y` is a :class:`~kivy.properties.AliasProperty` of
    (:data:`y` + :data:`height` / 2.)
    '''

    center = ReferenceListProperty(center_x, center_y)
    '''Center position of the widget.

    :data:`center` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:data:`center_x`, :data:`center_y`)
    '''

    cls = ListProperty([])
    '''Class of the widget, used for styling.
    '''

    id = StringProperty(None, allownone=True)
    '''Unique identifier of the widget in the tree.

    :data:`id` is a :class:`~kivy.properties.StringProperty`, default to None.

    .. warning::

        If the :data:`id` is already used in the tree, an exception will
        be raised.
    '''

    children = ListProperty([])
    '''List of children of this widget.

    :data:`children` is a :class:`~kivy.properties.ListProperty` instance,
    default to an empty list.

    Use :meth:`add_widget` and :meth:`remove_widget` for manipulating the
    children list. Don't manipulate the children list directly until you know
    what you are doing.
    '''

    parent = ObjectProperty(None, allownone=True)
    '''Parent of this widget.

    :data:`parent` is a :class:`~kivy.properties.ObjectProperty` instance,
    default to None.

    The parent of a widget is set when the widget is added to another one, and
    unset when the widget is removed from its parent.
    '''

    size_hint_x = NumericProperty(1, allownone=True)
    '''X size hint. Represents how much space the widget should use in the
    direction of the X axis, relative to its parent's width.
    Only :class:`~kivy.uix.layout.Layout` and
    :class:`~kivy.core.window.Window` make use of the hint.

    The value is in percent as a float from 0. to 1., where 1. means the full
    size of his parent. 0.5 represents 50%.

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

    See :doc:`api-kivy.uix.floatlayout` for further reference.

    Position hint is only used in :class:`~kivy.uix.floatlayout.FloatLayout` and
    :class:`~kivy.core.window.Window`.

    :data:`pos_hint` is a :class:`~kivy.properties.ObjectProperty` containing a
    dict.
    '''

    ids = DictProperty({})
    '''This is a Dictionary of id's defined in your kv language. This will only
    be populated if you use id's in your kv language code.

    .. versionadded:: 1.7.0

    :data:`ids` is a :class:`~kivy.properties.DictProperty`, defaults to a empty
    dict {}.
    '''

    opacity = NumericProperty(1.0)
    '''Opacity of the widget and all the children.

    .. versionadded:: 1.4.1

    The opacity attribute controls the opacity of the widget and its children.
    Be careful, it's a cumulative attribute: the value is multiplied to the
    current global opacity, and the result is applied to the current context
    color.

    For example: if your parent have an opacity of 0.5, and one children have an
    opacity of 0.2, the real opacity of the children will be 0.5 * 0.2 = 0.1.

    Then, the opacity is applied on the shader as::

        frag_color = color * vec4(1.0, 1.0, 1.0, opacity);

    :data:`opacity` is a :class:`~kivy.properties.NumericProperty`, default to
    1.0.
    '''

    def on_opacity(self, instance, value):
        canvas = self.canvas
        if canvas is not None:
            canvas.opacity = value

    canvas = None
    '''Canvas of the widget.

    The canvas is a graphics object that contains all the drawing instructions
    for the graphical representation of the widget.

    There are no general properties for the Widget class, such as background
    color, to keep the design simple and lean. Some derived classes, such as
    Button, do add such convenience properties, but generally the developer is
    responsible for implementing the graphics representation for a custom
    widget from the ground up. See the derived widget classes for patterns to
    follow and extend.

    See :class:`~kivy.graphics.Canvas` for more information about the usage.
    '''

    disabled = BooleanProperty(False)
    '''Indicates whether this widget can interact with input or not.

    .. Note::
        1. Child Widgets when added onto a disabled widget will be disabled
        automatically
        2. Disabling/enabling a parent disables/enables all it's children.

    .. versionadded:: 1.8.0

    :data:`disabled` is a :class:`~kivy.properties.BooleanProperty`,
    default to False.
    '''
