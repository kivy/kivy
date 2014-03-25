'''
Widget class
============

The :class:`Widget` class is the base class required to create a Widget.
This widget class is designed with a couple of principles in mind:

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
        Every widget has its own :class:`~kivy.graphics.Canvas` that you
        can use to draw. This separation allows Kivy to run your
        application in a very efficient manner.

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


We also have some default values and behaviors that you should be aware of:

* A :class:`Widget` is not a :class:`~kivy.uix.layout.Layout`: it will not
  change the position or the size of its children. If you want control over
  positioning or sizing, use a :class:`~kivy.uix.layout.Layout`.

* The default size of a widget is (100, 100). This is only changed if the
  parent is a :class:`~kivy.uix.layout.Layout`.
  For example, if you add a :class:`Label` inside a
  :class:`Button`, the label will not inherit the buttons size or position
  because the button is not a *Layout*: it's just another *Widget*.

* The default size_hint is (1, 1). If the parent is a :class:`Layout`, then the
  widget size will be the parent/layout size.

* :meth:`Widget.on_touch_down`, :meth:`Widget.on_touch_move`,
  :meth:`Widget.on_touch_up` don't do any sort of collisions. If you want to
  know if the touch is inside your widget, use :meth:`Widget.collide_point`.

Using Properties
----------------

When you read the documentation, all properties are described in the format::

    <name> is a <property class> and defaults to <default value>.

e.g.

    :attr:`~kivy.uix.label.Label.text` is a
    :class:`~kivy.properties.StringProperty` and defaults to ''.

If you want to be notified when the pos attribute changes, i.e. when the
widget moves, you can bind your own callback function like this::

    def callback_pos(instance, value):
        print('The widget', instance, 'moved to', value)

    wid = Widget()
    wid.bind(pos=callback_pos)

Read more about :doc:`/api-kivy.properties`.

Basic drawing
-------------

Widgets support a range of drawing instructions that you can use to customize
the look of your widgets and layouts. For example, to draw a background image
for your widget, you can do the following::

    def redraw(self, args):
        with self.canvas:
            Rectangle(source="cover.jpg", pos=self.pos, size=self.size)

    widget = Widget()
    widget.bind(pos=redraw, size=redraw)

.. highlight:: kv

To draw a background in kv::

    Widget:
        canvas:
            Rectangle:
                source: "cover.jpg"
                size: self.size
                pos: self.pos

These examples only scratch the surface. Please see the :mod:`kivy.graphics`
documentation for more information.

Widget event bubbling
---------------------

When you use the Kivy property changes to catch events, you sometimes
need to be aware of the order in which these events are propogated. In Kivy,
events bubble up from the most recently added widget and then backwards through
it's children (from the most recently added back to the first child).

In effect, this event model does not follow either of the conventional
"bubble up" or "bubble down" approaches, but propogates events according to the
natural order in which the widgets have been added. If you want to reverse this
order, you can raise events in the children before the parent by using the
`super` command.

Linguistically, this can be difficult to explain and sound complicated,
but it's really quite simple. Lets look at an example. In our kv file::

    <EventBubbler>:
        Label:
            text: '1'
            on_touch_down: root.printme("label 1 on_touch_down")
        Label:
            text: '2'
            on_touch_down: root.printme("label 2 on_touch_down")
        BoxLayout:
            on_touch_down: root.printme("BoxLayout on_touch_down")
            Label:
                text: '3'
                on_touch_down: root.printme("label 3 on_touch_down")
            Label:
                text: '4'
                on_touch_down: root.printme("label 4 on_touch_down")
        MyBoxLayout:
            # We use this class to demonsrate using 'super' to raise the child
            # events first
            Label:
                text: '5'
                on_touch_down: root.printme("label 5 on_touch_down")
            Label:
                text: '6'
                on_touch_down: root.printme("label 6 on_touch_down")

.. highlight:: python

In your Python file::

    from kivy.app import App
    from kivy.lang import Builder
    from kivy.uix.boxlayout import BoxLayout
    from kivy.properties import StringProperty


    class EventBubbler(BoxLayout):

        @staticmethod
        def printme(msg):
            print msg


    class MyBoxLayout(BoxLayout):
        def on_touch_down(self, touch):
            print "Before super(MyBoxLayout, self).on_touch_down(touch)"
            super(MyBoxLayout, self).on_touch_down(touch)
            print "After super(MyBoxLayout, self).on_touch_down(touch)"


    class BubbleApp(App):
        def build(self):
            return EventBubbler()

    BubbleApp().run()

This produces the following output::

    >>> Before super(MyBoxLayout, self).on_touch_down(touch)
    >>> label 6 on_touch_down
    >>> label 5 on_touch_down
    >>> After super(MyBoxLayout, self).on_touch_down(touch)
    >>> BoxLayout on_touch_up
    >>> label 4 on_touch_down
    >>> label 3 on_touch_down
    >>> label 2 on_touch_down
    >>> label 1 on_touch_down

This order is the same for the `on_touch_move` and `on_touch_up` events.
Notice how using the `super` command raises the child events immediately
when it is called. This approach gives you total control over the order in which
Kivy's events are propogated.

'''

__all__ = ('Widget', 'WidgetException')

from kivy.event import EventDispatcher
from kivy.factory import Factory
from kivy.properties import (NumericProperty, StringProperty, AliasProperty,
                             ReferenceListProperty, ObjectProperty,
                             ListProperty, DictProperty, BooleanProperty)
from kivy.graphics import (Canvas, PushMatrix, PopMatrix, Translate, Rectangle,
                           Fbo, ClearColor, ClearBuffers)
from kivy.base import EventLoop
from kivy.lang import Builder
from kivy.context import get_current_context
from weakref import proxy
from functools import partial
from itertools import islice


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
    '''Metaclass to automatically register new widgets for the
    :class:`~kivy.factory.Factory`

    .. warning::
        This metaclass is used by the Widget. Do not use it directly !
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
            Fired when a new touch event occurs
        `on_touch_move`:
            Fired when an existing touch moves
        `on_touch_up`:
            Fired when an existing touch disappears

    .. versionchanged:: 1.0.9
        Everything related to event properties has been moved to the
        :class:`~kivy.event.EventDispatcher`. Event properties can now be used
        when contructing a simple class without subclassing :class:`Widget`.

    .. versionchanged:: 1.5.0
        The constructor now accepts on_* arguments to automatically bind
        callbacks to properties or events, as in the Kv language.
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
        '''Return a proxy reference to the widget, i.e. without creating a
        reference to the widget. See `weakref.proxy
        <http://docs.python.org/2/library/weakref.html?highlight\
        =proxy#weakref.proxy>`_ for more information.

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
                Touch received. The touch is in parent coordinates. See
                :mod:`~kivy.uix.relativelayout` for a discussion on
                coordinate systems.

        :Returns:
            bool. If True, the dispatching of the touch event will stop.
        '''
        if self.disabled and self.collide_point(*touch.pos):
            return True
        for child in self.children[:]:
            if child.dispatch('on_touch_down', touch):
                return True

    def on_touch_move(self, touch):
        '''Receive a touch move event. The touch is in parent coordinates.

        See :meth:`on_touch_down` for more information.
        '''
        if self.disabled:
            return
        for child in self.children[:]:
            if child.dispatch('on_touch_move', touch):
                return True

    def on_touch_up(self, touch):
        '''Receive a touch up event. The touch is in parent coordinates.

        See :meth:`on_touch_down` for more information.
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
            `index`: int, defaults to 0
                Index to insert the widget in the list

                .. versionadded:: 1.0.5

        >>> from kivy.uix.button import Button
        >>> from kivy.uix.slider import Slider
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

        >>> from kivy.uix.button import Button
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

    def clear_widgets(self, children=None):
        '''Remove all widgets added to this widget.

        .. versionchanged:: 1.8.0
            `children` argument can be used to select the children we want to
            remove. It should be a list of children (or filtered list) of the
            current widget.
        '''

        if not children:
            children = self.children
        remove_widget = self.remove_widget
        for child in children[:]:
            remove_widget(child)

    def export_to_png(self, filename, *args):
        '''Saves an image of the widget and its children in png format at the
        specified filename. Works by removing the widget canvas from its
        parent, rendering to an :class:`~kivy.graphics.fbo.Fbo`, and calling
        :meth:`~kivy.graphics.texture.Texture.save`.

        .. note::

            The image includes only this widget and its children. If you want to
            include widgets elsewhere in the tree, you must call
            :meth:`~Widget.export_to_png` from their common parent, or use
            :meth:`~kivy.core.window.Window.screenshot` to capture the whole
            window.

        .. note::

            The image will be saved in png format, you should include the
            extension in your filename.

        .. versionadded:: 1.8.1
        '''

        if self.parent is not None:
            canvas_parent_index = self.parent.canvas.indexof(self.canvas)
            self.parent.canvas.remove(self.canvas)

        fbo = Fbo(size=self.size)

        with fbo:
            ClearColor(0, 0, 0, 1)
            ClearBuffers()
            Translate(-self.x, -self.y, 0)

        fbo.add(self.canvas)
        fbo.draw()
        fbo.texture.save(filename)
        fbo.remove(self.canvas)

        if self.parent is not None:
            self.parent.canvas.insert(canvas_parent_index, self.canvas)

        return True

    def get_root_window(self):
        '''Return the root window.

        :Returns:
            Instance of the root window. Can be a
            :class:`~kivy.core.window.WindowBase` or
            :class:`Widget`.
        '''
        if self.parent:
            return self.parent.get_root_window()

    def get_parent_window(self):
        '''Return the parent window.

        :Returns:
            Instance of the parent window. Can be a
            :class:`~kivy.core.window.WindowBase` or
            :class:`Widget`.
        '''
        if self.parent:
            return self.parent.get_parent_window()

    def _walk(self, restrict=False, loopback=False, index=None):
        # we pass index only when we are going on the parent.
        # so don't yield the parent as well.
        if index is None:
            index = len(self.children)
            yield self

        for child in reversed(self.children[:index]):
            for walk_child in child._walk(restrict=True):
                yield walk_child

        # if we want to continue with our parent, just do it
        if not restrict:
            parent = self.parent
            try:
                if parent is None or not isinstance(parent, Widget):
                    raise ValueError
                index = parent.children.index(self)
            except ValueError:
                # self is root, if wanted to loopback from first element then ->
                if not loopback:
                    return
                # if we started with root (i.e. index==None), then we have to
                # start from root again, so we return self again. Otherwise, we
                # never returned it, so return it now starting with it
                parent = self
                index = None
            for walk_child in parent._walk(loopback=loopback, index=index):
                yield walk_child

    def walk(self, restrict=False, loopback=False):
        ''' Iterator that walks the widget tree starting with this widget and
        goes forward returning widgets in the order in which layouts display
        them.

        :Parameters:
            `restrict`:
                If True, it will only iterate through the widget and its
                children (or children of its children etc.). Defaults to False.
            `loopback`:
                If True, when the last widget in the tree is reached,
                it'll loop back to the uppermost root and start walking until
                we hit this widget again. Naturally, it can only loop back when
                `restrict` is False. Defaults to False.

        :return:
            A generator that walks the tree, returning widgets in the
            forward layout order.

        For example, given a tree with the following structure::

            GridLayout:
                Button
                BoxLayout:
                    id: box
                    Widget
                    Button
                Widget

        walking this tree::

            >>> # Call walk on box with loopback True, and restrict False
            >>> [type(widget) for widget in box.walk(loopback=True)]
            [<class 'BoxLayout'>, <class 'Widget'>, <class 'Button'>,
                <class 'Widget'>, <class 'GridLayout'>, <class 'Button'>]
            >>> # Now with loopback False, and restrict False
            >>> [type(widget) for widget in box.walk()]
            [<class 'BoxLayout'>, <class 'Widget'>, <class 'Button'>,
                <class 'Widget'>]
            >>> # Now with restrict True
            >>> [type(widget) for widget in box.walk(restrict=True)]
            [<class 'BoxLayout'>, <class 'Widget'>, <class 'Button'>]

        .. versionadded:: 1.8.1
        '''
        gen = self._walk(restrict, loopback)
        yield next(gen)
        for node in gen:
            if node is self:
                return
            yield node

    def _walk_reverse(self, loopback=False, go_up=False):
        # process is walk up level, walk down its children tree, then walk up
        # next level etc.
        # default just walk down the children tree
        root = self
        index = 0
        # we need to go up a level before walking tree
        if go_up:
            root = self.parent
            try:
                if root is None or not isinstance(root, Widget):
                    raise ValueError
                index = root.children.index(self) + 1
            except ValueError:
                if not loopback:
                    return
                index = 0
                go_up = False
                root = self

        # now walk children tree starting with last-most child
        for child in islice(root.children, index, None):
            for walk_child in child._walk_reverse(loopback=loopback):
                yield walk_child
        # we need to return ourself last, in all cases
        yield root

        # if going up, continue walking up the parent tree
        if go_up:
            for walk_child in root._walk_reverse(loopback=loopback,
                                                 go_up=go_up):
                yield walk_child

    def walk_reverse(self, loopback=False):
        ''' Iterator that walks the widget tree backwards starting with the
        widget before this, and going backwards returning widgets in the
        reverse order in which layouts display them.

        This walks in the opposite direction of :meth:`walk`, so a list of the
        tree generated with :meth:`walk` will be in reverse order compared
        to the list generated with this, provided `loopback` is True.

        :Parameters:
            `loopback`:
                If True, when the uppermost root in the tree is
                reached, it'll loop back to the last widget and start walking
                back until after we hit widget again. Defaults to False

        :return:
            A generator that walks the tree, returning widgets in the
            reverse layout order.

        For example, given a tree with the following structure::

            GridLayout:
                Button
                BoxLayout:
                    id: box
                    Widget
                    Button
                Widget

        walking this tree::

            >>> # Call walk on box with loopback True
            >>> [type(widget) for widget in box.walk_reverse(loopback=True)]
            [<class 'Button'>, <class 'GridLayout'>, <class 'Widget'>,
                <class 'Button'>, <class 'Widget'>, <class 'BoxLayout'>]
            >>> # Now with loopback False
            >>> [type(widget) for widget in box.walk_reverse()]
            [<class 'Button'>, <class 'GridLayout'>]
            >>> forward = [w for w in box.walk(loopback=True)]
            >>> backward = [w for w in box.walk_reverse(loopback=True)]
            >>> forward == backward[::-1]
            True

        .. versionadded:: 1.8.1

        '''
        for node in self._walk_reverse(loopback=loopback, go_up=True):
            yield node
            if node is self:
                return

    def to_widget(self, x, y, relative=False):
        '''Convert the given coordinate from window to local widget
        coordinates. See :mod:`~kivy.uix.relativelayout` for details on the
        coordinate systems.
        '''
        if self.parent:
            x, y = self.parent.to_widget(x, y)
        return self.to_local(x, y, relative=relative)

    def to_window(self, x, y, initial=True, relative=False):
        '''Transform local coordinates to window coordinates. See
        :mod:`~kivy.uix.relativelayout` for details on the coordinate systems.
        '''
        if not initial:
            x, y = self.to_parent(x, y, relative=relative)
        if self.parent:
            return self.parent.to_window(x, y, initial=False,
                                         relative=relative)
        return (x, y)

    def to_parent(self, x, y, relative=False):
        '''Transform local coordinates to parent coordinates. See
        :mod:`~kivy.uix.relativelayout` for details on the coordinate systems.

        :Parameters:
            `relative`: bool, defaults to False
                Change to True if you want to translate relative positions from
                a widget to its parent coordinates.
        '''
        if relative:
            return (x + self.x, y + self.y)
        return (x, y)

    def to_local(self, x, y, relative=False):
        '''Transform parent coordinates to local coordinates. See
        :mod:`~kivy.uix.relativelayout` for details on the coordinate systems.

        :Parameters:
            `relative`: bool, defaults to False
                Change to True if you want to translate coordinates to
                relative widget coordinates.
        '''
        if relative:
            return (x - self.x, y - self.y)
        return (x, y)

    x = NumericProperty(0)
    '''X position of the widget.

    :attr:`x` is a :class:`~kivy.properties.NumericProperty` and defaults to 0.
    '''

    y = NumericProperty(0)
    '''Y position of the widget.

    :attr:`y` is a :class:`~kivy.properties.NumericProperty` and defaults to 0.
    '''

    width = NumericProperty(100)
    '''Width of the widget.

    :attr:`width` is a :class:`~kivy.properties.NumericProperty` ans defaults
    to 100.

    .. warning::
        Keep in mind that the `width` property is subject to layout logic and
        that this has not yet happened at the time of the widget's `__init__`
        method.
    '''

    height = NumericProperty(100)
    '''Height of the widget.

    :attr:`height` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 100.

    .. warning::
        Keep in mind that the `height` property is subject to layout logic and
        that this has not yet happened at the time of the widget's `__init__`
        method.
    '''

    pos = ReferenceListProperty(x, y)
    '''Position of the widget.

    :attr:`pos` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`x`, :attr:`y`) properties.
    '''

    size = ReferenceListProperty(width, height)
    '''Size of the widget.

    :attr:`size` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`width`, :attr:`height`) properties.
    '''

    def get_right(self):
        return self.x + self.width

    def set_right(self, value):
        self.x = value - self.width

    right = AliasProperty(get_right, set_right, bind=('x', 'width'))
    '''Right position of the widget.

    :attr:`right` is an :class:`~kivy.properties.AliasProperty` of
    (:attr:`x` + :attr:`width`),
    '''

    def get_top(self):
        return self.y + self.height

    def set_top(self, value):
        self.y = value - self.height

    top = AliasProperty(get_top, set_top, bind=('y', 'height'))
    '''Top position of the widget.

    :attr:`top` is an :class:`~kivy.properties.AliasProperty` of
    (:attr:`y` + :attr:`height`),
    '''

    def get_center_x(self):
        return self.x + self.width / 2.

    def set_center_x(self, value):
        self.x = value - self.width / 2.
    center_x = AliasProperty(get_center_x, set_center_x, bind=('x', 'width'))
    '''X center position of the widget.

    :attr:`center_x` is an :class:`~kivy.properties.AliasProperty` of
    (:attr:`x` + :attr:`width` / 2.),
    '''

    def get_center_y(self):
        return self.y + self.height / 2.

    def set_center_y(self, value):
        self.y = value - self.height / 2.
    center_y = AliasProperty(get_center_y, set_center_y, bind=('y', 'height'))
    '''Y center position of the widget.

    :attr:`center_y` is an :class:`~kivy.properties.AliasProperty` of
    (:attr:`y` + :attr:`height` / 2.)
    '''

    center = ReferenceListProperty(center_x, center_y)
    '''Center position of the widget.

    :attr:`center` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`center_x`, :attr:`center_y`)
    '''

    cls = ListProperty([])
    '''Class of the widget, used for styling.
    '''

    id = StringProperty(None, allownone=True)
    '''Unique identifier of the widget in the tree.

    :attr:`id` is a :class:`~kivy.properties.StringProperty` and defaults to
    None.

    .. warning::

        If the :attr:`id` is already used in the tree, an exception will
        be raised.
    '''

    children = ListProperty([])
    '''List of children of this widget.

    :attr:`children` is a :class:`~kivy.properties.ListProperty` and
    defaults to an empty list.

    Use :meth:`add_widget` and :meth:`remove_widget` for manipulating the
    children list. Don't manipulate the children list directly unless you know
    what you are doing.
    '''

    parent = ObjectProperty(None, allownone=True)
    '''Parent of this widget.

    :attr:`parent` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.

    The parent of a widget is set when the widget is added to another widget
    and unset when the widget is removed from its parent.
    '''

    size_hint_x = NumericProperty(1, allownone=True)
    '''X size hint. Represents how much space the widget should use in the
    direction of the X axis relative to its parent's width.
    Only the :class:`~kivy.uix.layout.Layout` and
    :class:`~kivy.core.window.Window` classes make use of the hint.

    The value is in percent as a float from 0. to 1., where 1. means the full
    size of his parent. 0.5 represents 50%.

    :attr:`size_hint_x` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 1.
    '''

    size_hint_y = NumericProperty(1, allownone=True)
    '''Y size hint.

    :attr:`size_hint_y` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 1.

    See :attr:`size_hint_x` for more information
    '''

    size_hint = ReferenceListProperty(size_hint_x, size_hint_y)
    '''Size hint.

    :attr:`size_hint` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`size_hint_x`, :attr:`size_hint_y`).

    See :attr:`size_hint_x` for more information
    '''

    pos_hint = ObjectProperty({})
    '''Position hint. This property allows you to set the position of
    the widget inside its parent layout, in percent (similar to
    size_hint).

    For example, if you want to set the top of the widget to be at 90%
    height of its parent layout, you can write:

        widget = Widget(pos_hint={'top': 0.9})

    The keys 'x', 'right' and 'center_x' will use the parent width.
    The keys 'y', 'top' and 'center_y' will use the parent height.

    See :doc:`api-kivy.uix.floatlayout` for further reference.

    Position hint is only used by the
    :class:`~kivy.uix.floatlayout.FloatLayout` and
    :class:`~kivy.core.window.Window`.

    :attr:`pos_hint` is an :class:`~kivy.properties.ObjectProperty`
    containing a dict.
    '''

    ids = DictProperty({})
    '''This is a Dictionary of id's defined in your kv language. This will only
    be populated if you use id's in your kv language code.

    .. versionadded:: 1.7.0

    :attr:`ids` is a :class:`~kivy.properties.DictProperty` and defaults to a
    empty dict {}.
    '''

    opacity = NumericProperty(1.0)
    '''Opacity of the widget and all the children.

    .. versionadded:: 1.4.1

    The opacity attribute controls the opacity of the widget and its children.
    Be careful, it's a cumulative attribute: the value is multiplied by the
    current global opacity and the result is applied to the current context
    color.

    For example, if the parent has an opacity of 0.5 and a child has an
    opacity of 0.2, the real opacity of the child will be 0.5 * 0.2 = 0.1.

    Then, the opacity is applied by the shader as::

        frag_color = color * vec4(1.0, 1.0, 1.0, opacity);

    :attr:`opacity` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 1.0.
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
    Button, do add such convenience properties but generally the developer is
    responsible for implementing the graphics representation for a custom
    widget from the ground up. See the derived widget classes for patterns to
    follow and extend.

    See :class:`~kivy.graphics.Canvas` for more information about the usage.
    '''

    disabled = BooleanProperty(False)
    '''Indicates whether this widget can interact with input or not.

    .. note::
        1. Child Widgets, when added to a disabled widget, will be disabled
        automatically,
        2. Disabling/enabling a parent disables/enables all it's children.

    .. versionadded:: 1.8.0

    :attr:`disabled` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''
