'''
Widget class
============

The :class:`Widget` class is the base class required for creating Widgets.
This widget class was designed with a couple of principles in mind:

* *Event Driven*

  Widget interaction is built on top of events that occur. If a property
  changes, the widget can respond to the change in the 'on_<propname>'
  callback. If nothing changes, nothing will be done. That's the main
  goal of the :class:`~kivy.properties.Property` class.

* *Separation Of Concerns (the widget and its graphical representation)*

  Widgets don't have a `draw()` method. This is done on purpose: The idea
  is to allow you to create your own graphical representation outside the
  widget class.
  Obviously you can still use all the available properties to do that, so
  that your representation properly reflects the widget's current state.
  Every widget has its own :class:`~kivy.graphics.Canvas` that you
  can use to draw. This separation allows Kivy to run your
  application in a very efficient manner.

* *Bounding Box / Collision*

  Often you want to know if a certain point is within the bounds of your
  widget. An example would be a button widget where you only want to
  trigger an action when the button itself is actually touched.
  For this, you can use the :meth:`~Widget.collide_point` method, which
  will return True if the point you pass to it is inside the axis-aligned
  bounding box defined by the widget's position and size.
  If a simple AABB is not sufficient, you can override the method to
  perform the collision checks with more complex shapes, e.g. a polygon.
  You can also check if a widget collides with another widget with
  :meth:`~Widget.collide_widget`.


We also have some default values and behaviors that you should be aware of:

* A :class:`Widget` is not a :class:`~kivy.uix.layout.Layout`: it will not
  change the position or the size of its children. If you want control over
  positioning or sizing, use a :class:`~kivy.uix.layout.Layout`.

* The default size of a widget is (100, 100). This is only changed if the
  parent is a :class:`~kivy.uix.layout.Layout`.
  For example, if you add a :class:`Label` inside a
  :class:`Button`, the label will not inherit the button's size or position
  because the button is not a *Layout*: it's just another *Widget*.

* The default size_hint is (1, 1). If the parent is a :class:`Layout`, then the
  widget size will be the parent layout's size.

* :meth:`~Widget.on_touch_down`, :meth:`~Widget.on_touch_move`,
  :meth:`~Widget.on_touch_up` don't do any sort of collisions. If you want to
  know if the touch is inside your widget, use :meth:`~Widget.collide_point`.

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
for your widget, you can do the following:

.. code-block:: python

    def redraw(self, args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

    widget = Widget()
    with widget.canvas:
        widget.bg_rect = Rectangle(source="cover.jpg", pos=self.pos, \
size=self.size)
    widget.bind(pos=redraw, size=redraw)

To draw a background in kv:

.. code-block:: kv

    Widget:
        canvas:
            Rectangle:
                source: "cover.jpg"
                size: self.size
                pos: self.pos

These examples only scratch the surface. Please see the :mod:`kivy.graphics`
documentation for more information.

.. _widget-event-bubbling:

Widget touch event bubbling
---------------------------

When you catch touch events between multiple widgets, you often
need to be aware of the order in which these events are propagated. In Kivy,
events bubble up from the first child upwards through the other children.
If a widget has children, the event is passed through its children before
being passed on to the widget after it.

As the :meth:`~kivy.uix.widget.Widget.on_touch_up` method inserts widgets at
index 0 by default, this means the event goes from the most recently added
widget back to the first one added. Consider the following:

.. code-block:: python

    box = BoxLayout()
    box.add_widget(Label(text="a"))
    box.add_widget(Label(text="b"))
    box.add_widget(Label(text="c"))

The label with text "c" gets the event first, "b" second and "a" last. You can
reverse this order by manually specifying the index:

.. code-block:: python

    box = BoxLayout()
    box.add_widget(Label(text="a"), index=0)
    box.add_widget(Label(text="b"), index=1)
    box.add_widget(Label(text="c"), index=2)

Now the order would be "a", "b" then "c". One thing to keep in mind when using
kv is that declaring a widget uses the
:meth:`~kivy.uix.widget.Widget.add_widget` method for insertion. Hence, using

.. code-block:: kv

    BoxLayout:
        MyLabel:
            text: "a"
        MyLabel:
            text: "b"
        MyLabel:
            text: "c"

would result in the event order "c", "b" then "a" as "c" was actually the last
added widget. It thus has index 0, "b" index 1 and "a" index 2. Effectively,
the child order is the reverse of its listed order.

This ordering is the same for the :meth:`~kivy.uix.widget.Widget.on_touch_move`
and :meth:`~kivy.uix.widget.Widget.on_touch_up` events.

In order to stop this event bubbling, a method can return `True`. This tells
Kivy the event has been handled and the event propagation stops. For example:

.. code-block:: python

    class MyWidget(Widget):
        def on_touch_down(self, touch):
            If <some_condition>:
                # Do stuff here and kill the event
                return True
            else:
                return super(MyWidget, self).on_touch_down(touch)

This approach gives you good control over exactly how events are dispatched
and managed. Sometimes, however, you may wish to let the event be completely
propagated before taking action. You can use the
:class:`~kivy.clock.Clock` to help you here:

.. code-block:: python

    class MyWidget(Label):
        def on_touch_down(self, touch, after=False):
            if after:
                print "Fired after the event has been dispatched!"
            else:
                Clock.schedule_once(lambda dt: self.on_touch_down(touch, True))
                return super(MyWidget, self).on_touch_down(touch)

Usage of :attr:`Widget.center`, :attr:`Widget.right`, and :attr:`Widget.top`
----------------------------------------------------------------------------

A common mistake when using one of the computed properties such as
:attr:`Widget.right` is to use it to make a widget follow its parent with a
KV rule such as `right: self.parent.right`. Consider, for example:

.. code-block:: kv

    FloatLayout:
        id: layout
        width: 100
        Widget:
            id: wid
            right: layout.right

The (mistaken) expectation is that this rule ensures that wid's right will
always be whatever layout's right is - that is wid.right and layout.right will
always be identical. In actual fact, this rule only says that "whenever
layout's `right` changes, wid's right will be set to that value". The
difference being that as long as `layout.right` doesn't change, `wid.right`
could be anything, even a value that will make them different.

Specifically, for the KV code above, consider the following example::

    >>> print(layout.right, wid.right)
    (100, 100)
    >>> wid.x = 200
    >>> print(layout.right, wid.right)
    (100, 300)

As can be seen, initially they are in sync, however, when we change `wid.x`
they go out of sync because `layout.right` is not changed and the rule is not
triggered.

The proper way to make the widget follow its parent's right is to use
:attr:`Widget.pos_hint`. If instead of `right: layout.right` we did
`pos_hint: {'right': 1}`, then the widgets right will always be set to be
at the parent's right at each layout update.
'''

__all__ = ('Widget', 'WidgetException')

from kivy.event import EventDispatcher
from kivy.eventmanager import (
    MODE_DONT_DISPATCH,
    MODE_FILTERED_DISPATCH,
    MODE_DEFAULT_DISPATCH
)
from kivy.factory import Factory
from kivy.properties import (
    NumericProperty, StringProperty, AliasProperty, ReferenceListProperty,
    ObjectProperty, ListProperty, DictProperty, BooleanProperty)
from kivy.graphics import (
    Canvas, Translate, Fbo, ClearColor, ClearBuffers, Scale)
from kivy.graphics.transformation import Matrix
from kivy.base import EventLoop
from kivy.lang import Builder
from kivy.context import get_current_context
from kivy.weakproxy import WeakProxy
from functools import partial
from itertools import islice


# References to all the widget destructors (partial method with widget uid as
# key).
_widget_destructors = {}


def _widget_destructor(uid, r):
    # Internal method called when a widget is deleted from memory. the only
    # thing we remember about it is its uid. Clear all the associated callbacks
    # created in kv language.
    del _widget_destructors[uid]
    Builder.unbind_widget(uid)


class WidgetException(Exception):
    '''Fired when the widget gets an exception.
    '''
    pass


class WidgetMetaclass(type):
    '''Metaclass to automatically register new widgets for the
    :class:`~kivy.factory.Factory`.

    .. warning::
        This metaclass is used by the Widget. Do not use it directly!
    '''
    def __init__(mcs, name, bases, attrs):
        super(WidgetMetaclass, mcs).__init__(name, bases, attrs)
        Factory.register(name, cls=mcs)


#: Base class used for Widget, that inherits from :class:`EventDispatcher`
WidgetBase = WidgetMetaclass('WidgetBase', (EventDispatcher, ), {})


class Widget(WidgetBase):
    '''Widget class. See module documentation for more information.

    :Events:
        `on_touch_down`: `(touch, )`
            Fired when a new touch event occurs. `touch` is the touch object.
        `on_touch_move`: `(touch, )`
            Fired when an existing touch moves. `touch` is the touch object.
        `on_touch_up`: `(touch, )`
            Fired when an existing touch disappears. `touch` is the touch
            object.
        `on_kv_post`: `(base_widget, )`
            Fired after all the kv rules associated with the widget
            and all other widgets that are in any of those rules have had
            all their kv rules applied. `base_widget` is the base-most widget
            whose instantiation triggered the kv rules (i.e. the widget
            instantiated from Python, e.g. ``MyWidget()``).

            .. versionchanged:: 1.11.0

    .. warning::
        Adding a `__del__` method to a class derived from Widget with Python
        prior to 3.4 will disable automatic garbage collection for instances
        of that class. This is because the Widget class creates reference
        cycles, thereby `preventing garbage collection
        <https://docs.python.org/2/library/gc.html#gc.garbage>`_.

    .. versionchanged:: 1.0.9
        Everything related to event properties has been moved to the
        :class:`~kivy.event.EventDispatcher`. Event properties can now be used
        when constructing a simple class without subclassing :class:`Widget`.

    .. versionchanged:: 1.5.0
        The constructor now accepts on_* arguments to automatically bind
        callbacks to properties or events, as in the Kv language.
    '''

    __metaclass__ = WidgetMetaclass
    __events__ = (
        'on_motion', 'on_touch_down', 'on_touch_move', 'on_touch_up',
        'on_kv_post'
    )
    _proxy_ref = None

    def __init__(self, **kwargs):
        # Before doing anything, ensure the windows exist.
        EventLoop.ensure_window()

        # Assign the default context of the widget creation.
        if not hasattr(self, '_context'):
            self._context = get_current_context()

        no_builder = '__no_builder' in kwargs
        self._disabled_value = False
        if no_builder:
            del kwargs['__no_builder']
        on_args = {k: v for k, v in kwargs.items() if k[:3] == 'on_'}
        for key in on_args:
            del kwargs[key]

        self._disabled_count = 0

        super(Widget, self).__init__(**kwargs)

        # Create the default canvas if it does not exist.
        if self.canvas is None:
            self.canvas = Canvas(opacity=self.opacity)

        # Apply all the styles.
        if not no_builder:
            rule_children = []
            self.apply_class_lang_rules(
                ignored_consts=self._kwargs_applied_init,
                rule_children=rule_children)

            for widget in rule_children:
                widget.dispatch('on_kv_post', self)
            self.dispatch('on_kv_post', self)

        # Bind all the events.
        if on_args:
            self.bind(**on_args)

    @property
    def proxy_ref(self):
        '''Return a proxy reference to the widget, i.e. without creating a
        reference to the widget. See `weakref.proxy
        <http://docs.python.org/2/library/weakref.html?highlight\
        =proxy#weakref.proxy>`_ for more information.

        .. versionadded:: 1.7.2
        '''
        _proxy_ref = self._proxy_ref
        if _proxy_ref is not None:
            return _proxy_ref

        f = partial(_widget_destructor, self.uid)
        self._proxy_ref = _proxy_ref = WeakProxy(self, f)
        # Only f should be enough here, but it appears that is a very
        # specific case, the proxy destructor is not called if both f and
        # _proxy_ref are not together in a tuple.
        _widget_destructors[self.uid] = (f, _proxy_ref)
        return _proxy_ref

    def __hash__(self):
        return id(self)

    def apply_class_lang_rules(
            self, root=None, ignored_consts=set(), rule_children=None):
        '''
        Method that is called by kivy to apply the kv rules of this widget's
        class.

        :Parameters:
            `root`: :class:`Widget`
                The root widget that instantiated this widget in kv, if the
                widget was instantiated in kv, otherwise ``None``.
            `ignored_consts`: set
                (internal) See :meth:`~kivy.lang.builder.BuilderBase.apply`.
            `rule_children`: list
                (internal) See :meth:`~kivy.lang.builder.BuilderBase.apply`.

        This is useful to be able to execute code before/after the class kv
        rules are applied to the widget. E.g. if the kv code requires some
        properties to be initialized before it is used in a binding rule.
        If overwriting remember to call ``super``, otherwise the kv rules will
        not be applied.

        In the following example,

        .. code-block:: python

            class MyWidget(Widget):
                pass

            class OtherWidget(MyWidget):
                pass

        .. code-block:: kv

        <MyWidget>:
            my_prop: some_value

        <OtherWidget>:
            other_prop: some_value

        When ``OtherWidget`` is instantiated with ``OtherWidget()``, the
        widget's :meth:`apply_class_lang_rules` is called and it applies the
        kv rules of this class - ``<MyWidget>`` and ``<OtherWidget>``.

        Similarly, when the widget is instantiated from kv, e.g.

        .. code-block:: kv

            <MyBox@BoxLayout>:
                height: 55
                OtherWidget:
                    width: 124

        ``OtherWidget``'s :meth:`apply_class_lang_rules` is called and it
        applies the kv rules of this class - ``<MyWidget>`` and
        ``<OtherWidget>``.

        .. note::

            It applies only the class rules not the instance rules. I.e. in the
            above kv example in the ``MyBox`` rule when ``OtherWidget`` is
            instantiated, its :meth:`apply_class_lang_rules` applies the
            ``<MyWidget>`` and ``<OtherWidget>`` rules to it - it does not
            apply the ``width: 124`` rule. The ``width: 124`` rule is part of
            the ``MyBox`` rule and is applied by the ``MyBox``'s instance's
            :meth:`apply_class_lang_rules`.

        .. versionchanged:: 1.11.0
        '''
        Builder.apply(
            self, ignored_consts=ignored_consts,
            rule_children=rule_children)

    #
    # Collision
    #
    def collide_point(self, x, y):
        '''
        Check if a point (x, y) is inside the widget's axis aligned bounding
        box.

        :Parameters:
            `x`: numeric
                x position of the point (in parent coordinates)
            `y`: numeric
                y position of the point (in parent coordinates)

        :Returns:
            A bool. True if the point is inside the bounding box, False
            otherwise.

        .. code-block:: python

            >>> Widget(pos=(10, 10), size=(50, 50)).collide_point(40, 40)
            True
        '''
        return self.x <= x <= self.right and self.y <= y <= self.top

    def collide_widget(self, wid):
        '''
        Check if another widget collides with this widget. This function
        performs an axis-aligned bounding box intersection test by default.

        :Parameters:
            `wid`: :class:`Widget` class
                Widget to test collision with.

        :Returns:
            bool. True if the other widget collides with this widget, False
            otherwise.

        .. code-block:: python

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

    def on_motion(self, etype, me):
        '''Called when a motion event is received.

        :Parameters:
            `etype`: `str`
                Event type, one of "begin", "update" or "end"
            `me`: :class:`~kivy.input.motionevent.MotionEvent`
                Received motion event
        :Returns: `bool`
            `True` to stop event dispatching

        .. versionadded:: 2.1.0

        .. warning::
            This is an experimental method and it remains so while this warning
            is present.
        '''
        if self.disabled or me.dispatch_mode == MODE_DONT_DISPATCH:
            return
        if me.type_id not in self.motion_filter:
            return
        filtered = self.motion_filter[me.type_id]
        if filtered[0] is self and len(filtered) == 1:
            return
        if me.dispatch_mode == MODE_DEFAULT_DISPATCH:
            last_filtered = filtered[-1]
            for widget in self.children[:]:
                if widget.dispatch('on_motion', etype, me):
                    return True
                if widget is last_filtered:
                    return
        if me.dispatch_mode == MODE_FILTERED_DISPATCH:
            widgets = filtered[1:] if filtered[0] is self else filtered[:]
            for widget in widgets:
                if widget.dispatch('on_motion', etype, me):
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

        :Returns: bool
            If True, the dispatching of the touch event will stop.
            If False, the event will continue to be dispatched to the rest
            of the widget tree.
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

    def on_kv_post(self, base_widget):
        pass

    #
    # Tree management
    #
    def add_widget(self, widget, index=0, canvas=None):
        '''Add a new widget as a child of this widget.

        :Parameters:
            `widget`: :class:`Widget`
                Widget to add to our list of children.
            `index`: int, defaults to 0
                Index to insert the widget in the list. Notice that the default
                of 0 means the widget is inserted at the beginning of the list
                and will thus be drawn on top of other sibling widgets. For a
                full discussion of the index and widget hierarchy, please see
                the :doc:`Widgets Programming Guide <guide/widgets>`.

                .. versionadded:: 1.0.5
            `canvas`: str, defaults to None
                Canvas to add widget's canvas to. Can be 'before', 'after' or
                None for the default canvas.

                .. versionadded:: 1.9.0

    .. code-block:: python

        >>> from kivy.uix.button import Button
        >>> from kivy.uix.slider import Slider
        >>> root = Widget()
        >>> root.add_widget(Button())
        >>> slider = Slider()
        >>> root.add_widget(slider)

        '''
        if not isinstance(widget, Widget):
            raise WidgetException(
                'add_widget() can be used only with instances'
                ' of the Widget class.')

        widget = widget.__self__
        if widget is self:
            raise WidgetException(
                'Widget instances cannot be added to themselves.')
        parent = widget.parent
        # Check if the widget is already a child of another widget.
        if parent:
            raise WidgetException('Cannot add %r, it already has a parent %r'
                                  % (widget, parent))
        widget.parent = parent = self
        # Child will be disabled if added to a disabled parent.
        widget.inc_disabled(self._disabled_count)

        canvas = self.canvas.before if canvas == 'before' else \
            self.canvas.after if canvas == 'after' else self.canvas

        if index == 0 or len(self.children) == 0:
            self.children.insert(0, widget)
            canvas.add(widget.canvas)
        else:
            canvas = self.canvas
            children = self.children
            if index >= len(children):
                index = len(children)
                next_index = canvas.indexof(children[-1].canvas)
            else:
                next_child = children[index]
                next_index = canvas.indexof(next_child.canvas)
                if next_index == -1:
                    next_index = canvas.length()
                else:
                    next_index += 1

            children.insert(index, widget)
            # We never want to insert widget _before_ canvas.before.
            if next_index == 0 and canvas.has_before:
                next_index = 1
            canvas.insert(next_index, widget.canvas)
        for type_id in widget.motion_filter:
            self.register_for_motion_event(type_id, widget)
        widget.fbind('motion_filter', self._update_motion_filter)

    def remove_widget(self, widget):
        '''Remove a widget from the children of this widget.

        :Parameters:
            `widget`: :class:`Widget`
                Widget to remove from our children list.

    .. code-block:: python

        >>> from kivy.uix.button import Button
        >>> root = Widget()
        >>> button = Button()
        >>> root.add_widget(button)
        >>> root.remove_widget(button)
        '''
        if widget not in self.children:
            return
        self.children.remove(widget)
        if widget.canvas in self.canvas.children:
            self.canvas.remove(widget.canvas)
        elif widget.canvas in self.canvas.after.children:
            self.canvas.after.remove(widget.canvas)
        elif widget.canvas in self.canvas.before.children:
            self.canvas.before.remove(widget.canvas)
        for type_id in widget.motion_filter:
            self.unregister_for_motion_event(type_id, widget)
        widget.funbind('motion_filter', self._update_motion_filter)
        widget.parent = None
        widget.dec_disabled(self._disabled_count)

    def clear_widgets(self, children=None):
        '''
        Remove all (or the specified) :attr:`~Widget.children` of this widget.
        If the 'children' argument is specified, it should be a list (or
        filtered list) of children of the current widget.

        .. versionchanged:: 1.8.0
            The `children` argument can be used to specify the children you
            want to remove.
        .. versionchanged:: 2.1.0

            Specifying an empty ``children`` list leaves the widgets unchanged.
            Previously it was treated like ``None`` and all children were
            removed.
        '''
        if children is None or children is self.children:
            children = self.children[:]

        remove_widget = self.remove_widget
        for child in children:
            remove_widget(child)

    def _update_motion_filter(self, child_widget, child_motion_filter):
        old_events = []
        for type_id, widgets in self.motion_filter.items():
            if child_widget in widgets:
                old_events.append(type_id)
        for type_id in old_events:
            if type_id not in child_motion_filter:
                self.unregister_for_motion_event(type_id, child_widget)
        for type_id in child_motion_filter:
            if type_id not in old_events:
                self.register_for_motion_event(type_id, child_widget)

    def _find_index_in_motion_filter(self, type_id, widget):
        if widget is self:
            return 0
        find_index = self.children.index
        max_index = find_index(widget) + 1
        motion_widgets = self.motion_filter[type_id]
        insert_index = 1 if motion_widgets[0] is self else 0
        for index in range(insert_index, len(motion_widgets)):
            if find_index(motion_widgets[index]) < max_index:
                insert_index += 1
            else:
                break
        return insert_index

    def register_for_motion_event(self, type_id, widget=None):
        '''Register to receive motion events of `type_id`.

        Override :meth:`on_motion` or bind to `on_motion` event to handle
        the incoming motion events.

        :Parameters:
            `type_id`: `str`
                Motion event type id (eg. "touch", "hover", etc.)
            `widget`: `Widget`
                Child widget or `self` if omitted

        .. versionadded:: 2.1.0

        .. note::
            Method can be called multiple times with the same arguments.

        .. warning::
            This is an experimental method and it remains so while this warning
            is present.
        '''
        a_widget = widget or self
        motion_filter = self.motion_filter
        if type_id not in motion_filter:
            motion_filter[type_id] = [a_widget]
        elif widget not in motion_filter[type_id]:
            index = self._find_index_in_motion_filter(type_id, a_widget)
            motion_filter[type_id].insert(index, a_widget)

    def unregister_for_motion_event(self, type_id, widget=None):
        '''Unregister to receive motion events of `type_id`.

        :Parameters:
            `type_id`: `str`
                Motion event type id (eg. "touch", "hover", etc.)
            `widget`: `Widget`
                Child widget or `self` if omitted

        .. versionadded:: 2.1.0

        .. note::
            Method can be called multiple times with the same arguments.

        .. warning::
            This is an experimental method and it remains so while this warning
            is present.
        '''
        a_widget = widget or self
        motion_filter = self.motion_filter
        if type_id in motion_filter:
            if a_widget in motion_filter[type_id]:
                motion_filter[type_id].remove(a_widget)
                if not motion_filter[type_id]:
                    del motion_filter[type_id]

    def export_to_png(self, filename, *args, **kwargs):
        '''Saves an image of the widget and its children in png format at the
        specified filename. Works by removing the widget canvas from its
        parent, rendering to an :class:`~kivy.graphics.fbo.Fbo`, and calling
        :meth:`~kivy.graphics.texture.Texture.save`.

        .. note::

            The image includes only this widget and its children. If you want
            to include widgets elsewhere in the tree, you must call
            :meth:`~Widget.export_to_png` from their common parent, or use
            :meth:`~kivy.core.window.WindowBase.screenshot` to capture the
            whole window.

        .. note::

            The image will be saved in png format, you should include the
            extension in your filename.

        .. versionadded:: 1.9.0

        :Parameters:
            `filename`: str
                The filename with which to save the png.
            `scale`: float
                The amount by which to scale the saved image, defaults to 1.

                .. versionadded:: 1.11.0
        '''
        self.export_as_image(*args, **kwargs).save(filename, flipped=False)

    def export_as_image(self, *args, **kwargs):
        '''Return an core :class:`~kivy.core.image.Image` of the actual
        widget.

        .. versionadded:: 1.11.0
        '''
        from kivy.core.image import Image
        scale = kwargs.get('scale', 1)

        if self.parent is not None:
            canvas_parent_index = self.parent.canvas.indexof(self.canvas)
            if canvas_parent_index > -1:
                self.parent.canvas.remove(self.canvas)

        fbo = Fbo(size=(self.width * scale, self.height * scale),
                  with_stencilbuffer=True)

        with fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            Scale(1, -1, 1)
            Scale(scale, scale, 1)
            Translate(-self.x, -self.y - self.height, 0)

        fbo.add(self.canvas)
        fbo.draw()
        img = Image(fbo.texture)
        fbo.remove(self.canvas)

        if self.parent is not None and canvas_parent_index > -1:
            self.parent.canvas.insert(canvas_parent_index, self.canvas)

        return img

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
        # We pass index only when we are going on the parent
        # so don't yield the parent as well.
        if index is None:
            index = len(self.children)
            yield self

        for child in reversed(self.children[:index]):
            for walk_child in child._walk(restrict=True):
                yield walk_child

        # If we want to continue with our parent, just do it.
        if not restrict:
            parent = self.parent
            try:
                if parent is None or not isinstance(parent, Widget):
                    raise ValueError
                index = parent.children.index(self)
            except ValueError:
                # Self is root, if we want to loopback from the first element:
                if not loopback:
                    return
                # If we started with root (i.e. index==None), then we have to
                # start from root again, so we return self again. Otherwise, we
                # never returned it, so return it now starting with it.
                parent = self
                index = None
            for walk_child in parent._walk(loopback=loopback, index=index):
                yield walk_child

    def walk(self, restrict=False, loopback=False):
        ''' Iterator that walks the widget tree starting with this widget and
        goes forward returning widgets in the order in which layouts display
        them.

        :Parameters:
            `restrict`: bool, defaults to False
                If True, it will only iterate through the widget and its
                children (or children of its children etc.). Defaults to False.
            `loopback`: bool, defaults to False
                If True, when the last widget in the tree is reached,
                it'll loop back to the uppermost root and start walking until
                we hit this widget again. Naturally, it can only loop back when
                `restrict` is False. Defaults to False.

        :return:
            A generator that walks the tree, returning widgets in the
            forward layout order.

        For example, given a tree with the following structure:

        .. code-block:: kv

            GridLayout:
                Button
                BoxLayout:
                    id: box
                    Widget
                    Button
                Widget

        walking this tree:

        .. code-block:: python

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

        .. versionadded:: 1.9.0
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
            `loopback`: bool, defaults to False
                If True, when the uppermost root in the tree is
                reached, it'll loop back to the last widget and start walking
                back until after we hit widget again. Defaults to False.

        :return:
            A generator that walks the tree, returning widgets in the
            reverse layout order.

        For example, given a tree with the following structure:

        .. code-block:: kv

            GridLayout:
                Button
                BoxLayout:
                    id: box
                    Widget
                    Button
                Widget

        walking this tree:

        .. code-block:: python

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

        .. versionadded:: 1.9.0

        '''
        for node in self._walk_reverse(loopback=loopback, go_up=True):
            yield node
            if node is self:
                return

    def to_widget(self, x, y, relative=False):
        '''Convert the coordinate from window to local (current widget)
        coordinates.

        See :mod:`~kivy.uix.relativelayout` for details on the coordinate
        systems.
        '''
        if self.parent:
            x, y = self.parent.to_widget(x, y)
        return self.to_local(x, y, relative=relative)

    def to_window(self, x, y, initial=True, relative=False):
        """If ``initial`` is True, the default, it transforms **parent**
        coordinates to window coordinates. Otherwise, it transforms **local**
        (current widget) coordinates to window coordinates.

        See :mod:`~kivy.uix.relativelayout` for details on the coordinate
        systems.
        """
        if not initial:
            x, y = self.to_parent(x, y, relative=relative)
        if self.parent:
            return self.parent.to_window(x, y, initial=False,
                                         relative=relative)
        return (x, y)

    def to_parent(self, x, y, relative=False):
        """Transform local (current widget) coordinates to parent coordinates.

        See :mod:`~kivy.uix.relativelayout` for details on the coordinate
        systems.

        :Parameters:
            `relative`: bool, defaults to False
                Change to True if you want to translate relative positions from
                a widget to its parent coordinates.
        """
        if relative:
            return (x + self.x, y + self.y)
        return (x, y)

    def to_local(self, x, y, relative=False):
        """Transform parent coordinates to local (current widget) coordinates.

        See :mod:`~kivy.uix.relativelayout` for details on the coordinate
        systems.

        :Parameters:
            `relative`: bool, defaults to False
                Change to True if you want to translate coordinates to
                relative widget coordinates.
        """
        if relative:
            return (x - self.x, y - self.y)
        return (x, y)

    def _apply_transform(self, m, pos=None):
        if self.parent:
            x, y = self.parent.to_widget(relative=True,
                                         *self.to_window(*(pos or self.pos)))
            m.translate(x, y, 0)
            m = self.parent._apply_transform(m) if self.parent else m
        return m

    def get_window_matrix(self, x=0, y=0):
        '''Calculate the transformation matrix to convert between window and
        widget coordinates.

        :Parameters:
            `x`: float, defaults to 0
                Translates the matrix on the x axis.
            `y`: float, defaults to 0
                Translates the matrix on the y axis.
        '''
        m = Matrix()
        m.translate(x, y, 0)
        m = self._apply_transform(m)
        return m

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

    :attr:`width` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 100.

    .. warning::
        Keep in mind that the `width` property is subject to layout logic and
        that this has not yet happened at the time of the widget's `__init__`
        method.

    .. warning::
        A negative width is not supported.
    '''

    height = NumericProperty(100)
    '''Height of the widget.

    :attr:`height` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 100.

    .. warning::
        Keep in mind that the `height` property is subject to layout logic and
        that this has not yet happened at the time of the widget's `__init__`
        method.

    .. warning::
        A negative height is not supported.
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

    right = AliasProperty(get_right, set_right,
                          bind=('x', 'width'),
                          cache=True, watch_before_use=False)
    '''Right position of the widget.

    :attr:`right` is an :class:`~kivy.properties.AliasProperty` of
    (:attr:`x` + :attr:`width`).
    '''

    def get_top(self):
        return self.y + self.height

    def set_top(self, value):
        self.y = value - self.height

    top = AliasProperty(get_top, set_top,
                        bind=('y', 'height'),
                        cache=True, watch_before_use=False)
    '''Top position of the widget.

    :attr:`top` is an :class:`~kivy.properties.AliasProperty` of
    (:attr:`y` + :attr:`height`).
    '''

    def get_center_x(self):
        return self.x + self.width / 2.

    def set_center_x(self, value):
        self.x = value - self.width / 2.

    center_x = AliasProperty(get_center_x, set_center_x,
                             bind=('x', 'width'),
                             cache=True, watch_before_use=False)
    '''X center position of the widget.

    :attr:`center_x` is an :class:`~kivy.properties.AliasProperty` of
    (:attr:`x` + :attr:`width` / 2.).
    '''

    def get_center_y(self):
        return self.y + self.height / 2.

    def set_center_y(self, value):
        self.y = value - self.height / 2.

    center_y = AliasProperty(get_center_y, set_center_y,
                             bind=('y', 'height'),
                             cache=True, watch_before_use=False)
    '''Y center position of the widget.

    :attr:`center_y` is an :class:`~kivy.properties.AliasProperty` of
    (:attr:`y` + :attr:`height` / 2.).
    '''

    center = ReferenceListProperty(center_x, center_y)
    '''Center position of the widget.

    :attr:`center` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`center_x`, :attr:`center_y`) properties.
    '''

    cls = ListProperty([])
    '''Class of the widget, used for styling.
    '''

    children = ListProperty([])
    '''List of children of this widget.

    :attr:`children` is a :class:`~kivy.properties.ListProperty` and
    defaults to an empty list.

    Use :meth:`add_widget` and :meth:`remove_widget` for manipulating the
    children list. Don't manipulate the children list directly unless you know
    what you are doing.
    '''

    parent = ObjectProperty(None, allownone=True, rebind=True)
    '''Parent of this widget. The parent of a widget is set when the widget
    is added to another widget and unset when the widget is removed from its
    parent.

    :attr:`parent` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    size_hint_x = NumericProperty(1, allownone=True)
    '''x size hint. Represents how much space the widget should use in the
    direction of the x axis relative to its parent's width.
    Only the :class:`~kivy.uix.layout.Layout` and
    :class:`~kivy.core.window.Window` classes make use of the hint.

    The size_hint is used by layouts for two purposes:

    - When the layout considers widgets on their own rather than in
      relation to its other children, the size_hint_x is a direct proportion
      of the parent width, normally between 0.0 and 1.0. For instance, a
      widget with ``size_hint_x=0.5`` in
      a vertical BoxLayout will take up half the BoxLayout's width, or
      a widget in a FloatLayout with ``size_hint_x=0.2`` will take up 20%
      of the FloatLayout width. If the size_hint is greater than 1, the
      widget will be wider than the parent.
    - When multiple widgets can share a row of a layout, such as in a
      horizontal BoxLayout, their widths will be their size_hint_x as a
      fraction of the sum of widget size_hints. For instance, if the
      size_hint_xs are (0.5, 1.0, 0.5), the first widget will have a
      width of 25% of the parent width.

    :attr:`size_hint_x` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 1.
    '''

    size_hint_y = NumericProperty(1, allownone=True)
    '''y size hint.

    :attr:`size_hint_y` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 1.

    See :attr:`size_hint_x` for more information, but with widths and heights
    swapped.
    '''

    size_hint = ReferenceListProperty(size_hint_x, size_hint_y)
    '''Size hint.

    :attr:`size_hint` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`size_hint_x`, :attr:`size_hint_y`) properties.

    See :attr:`size_hint_x` for more information.
    '''

    pos_hint = ObjectProperty({})
    '''Position hint. This property allows you to set the position of
    the widget inside its parent layout (similar to
    size_hint).

    For example, if you want to set the top of the widget to be at 90%
    height of its parent layout, you can write::

        widget = Widget(pos_hint={'top': 0.9})

    The keys 'x', 'right' and 'center_x' will use the parent width.
    The keys 'y', 'top' and 'center_y' will use the parent height.

    See :doc:`api-kivy.uix.floatlayout` for further reference.

    .. note::
        :attr:`pos_hint` is not used by all layouts. Check the documentation
        of the layout in question to see if it supports pos_hint.

    :attr:`pos_hint` is an :class:`~kivy.properties.ObjectProperty`
    containing a dict.
    '''

    size_hint_min_x = NumericProperty(None, allownone=True)
    '''When not None, the x-direction minimum size (in pixels,
    like :attr:`width`) when :attr:`size_hint_x` is also not None.

    When :attr:`size_hint_x` is not None, it is the minimum width that the
    widget will be set due to the :attr:`size_hint_x`. I.e. when a smaller size
    would be set, :attr:`size_hint_min_x` is the value used instead for the
    widget width. When None, or when :attr:`size_hint_x` is None,
    :attr:`size_hint_min_x` doesn't do anything.

    Only the :class:`~kivy.uix.layout.Layout` and
    :class:`~kivy.core.window.Window` classes make use of the hint.

    :attr:`size_hint_min_x` is a :class:`~kivy.properties.NumericProperty` and
    defaults to None.

    .. versionadded:: 1.10.0
    '''

    size_hint_min_y = NumericProperty(None, allownone=True)
    '''When not None, the y-direction minimum size (in pixels,
    like :attr:`height`) when :attr:`size_hint_y` is also not None.

    When :attr:`size_hint_y` is not None, it is the minimum height that the
    widget will be set due to the :attr:`size_hint_y`. I.e. when a smaller size
    would be set, :attr:`size_hint_min_y` is the value used instead for the
    widget height. When None, or when :attr:`size_hint_y` is None,
    :attr:`size_hint_min_y` doesn't do anything.

    Only the :class:`~kivy.uix.layout.Layout` and
    :class:`~kivy.core.window.Window` classes make use of the hint.

    :attr:`size_hint_min_y` is a :class:`~kivy.properties.NumericProperty` and
    defaults to None.

    .. versionadded:: 1.10.0
    '''

    size_hint_min = ReferenceListProperty(size_hint_min_x, size_hint_min_y)
    '''Minimum size when using :attr:`size_hint`.

    :attr:`size_hint_min` is a :class:`~kivy.properties.ReferenceListProperty`
    of (:attr:`size_hint_min_x`, :attr:`size_hint_min_y`) properties.

    .. versionadded:: 1.10.0
    '''

    size_hint_max_x = NumericProperty(None, allownone=True)
    '''When not None, the x-direction maximum size (in pixels,
    like :attr:`width`) when :attr:`size_hint_x` is also not None.

    Similar to :attr:`size_hint_min_x`, except that it sets the maximum width.

    :attr:`size_hint_max_x` is a :class:`~kivy.properties.NumericProperty` and
    defaults to None.

    .. versionadded:: 1.10.0
    '''

    size_hint_max_y = NumericProperty(None, allownone=True)
    '''When not None, the y-direction maximum size (in pixels,
    like :attr:`height`) when :attr:`size_hint_y` is also not None.

    Similar to :attr:`size_hint_min_y`, except that it sets the maximum height.

    :attr:`size_hint_max_y` is a :class:`~kivy.properties.NumericProperty` and
    defaults to None.

    .. versionadded:: 1.10.0
    '''

    size_hint_max = ReferenceListProperty(size_hint_max_x, size_hint_max_y)
    '''Maximum size when using :attr:`size_hint`.

    :attr:`size_hint_max` is a :class:`~kivy.properties.ReferenceListProperty`
    of (:attr:`size_hint_max_x`, :attr:`size_hint_max_y`) properties.

    .. versionadded:: 1.10.0
    '''

    ids = DictProperty({})
    '''This is a dictionary of ids defined in your kv language. This will only
    be populated if you use ids in your kv language code.

    .. versionadded:: 1.7.0

    :attr:`ids` is a :class:`~kivy.properties.DictProperty` and defaults to an
    empty dict {}.

    The :attr:`ids` are populated for each root level widget definition. For
    example:

    .. code-block:: kv

        # in kv
        <MyWidget@Widget>:
            id: my_widget
            Label:
                id: label_widget
                Widget:
                    id: inner_widget
                    Label:
                        id: inner_label
            TextInput:
                id: text_input
            OtherWidget:
                id: other_widget


        <OtherWidget@Widget>
            id: other_widget
            Label:
                id: other_label
                TextInput:
                    id: other_textinput

    Then, in python:

    .. code-block:: python

        >>> widget = MyWidget()
        >>> print(widget.ids)
        {'other_widget': <weakproxy at 041CFED0 to OtherWidget at 041BEC38>,
        'inner_widget': <weakproxy at 04137EA0 to Widget at 04138228>,
        'inner_label': <weakproxy at 04143540 to Label at 04138260>,
        'label_widget': <weakproxy at 04137B70 to Label at 040F97A0>,
        'text_input': <weakproxy at 041BB5D0 to TextInput at 041BEC00>}
        >>> print(widget.ids['other_widget'].ids)
        {'other_textinput': <weakproxy at 041DBB40 to TextInput at 041BEF48>,
        'other_label': <weakproxy at 041DB570 to Label at 041BEEA0>}
        >>> print(widget.ids['label_widget'].ids)
        {}
    '''

    opacity = NumericProperty(1.0)
    '''Opacity of the widget and all its children.

    .. versionadded:: 1.4.1

    The opacity attribute controls the opacity of the widget and its children.
    Be careful, it's a cumulative attribute: the value is multiplied by the
    current global opacity and the result is applied to the current context
    color.

    For example, if the parent has an opacity of 0.5 and a child has an
    opacity of 0.2, the real opacity of the child will be 0.5 * 0.2 = 0.1.

    Then, the opacity is applied by the shader as:

    .. code-block:: python

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

    def get_disabled(self):
        return self._disabled_count > 0

    def set_disabled(self, value):
        # Necessary to ensure a change between value of equal truthiness
        # doesn't mess up the count
        value = bool(value)
        if value != self._disabled_value:
            self._disabled_value = value
            if value:
                self.inc_disabled()
            else:
                self.dec_disabled()
            return True

    def inc_disabled(self, count=1):
        self._disabled_count += count
        if self._disabled_count - count < 1 <= self._disabled_count:
            self.property('disabled').dispatch(self)
        for c in self.children:
            c.inc_disabled(count)

    def dec_disabled(self, count=1):
        self._disabled_count -= count
        if self._disabled_count <= 0 < self._disabled_count + count:
            self.property('disabled').dispatch(self)
        for c in self.children:
            c.dec_disabled(count)

    disabled = AliasProperty(get_disabled, set_disabled, watch_before_use=False)
    '''Indicates whether this widget can interact with input or not.

    :attr:`disabled` is an :class:`~kivy.properties.AliasProperty` and
    defaults to False.

    .. note::

      1. Child Widgets, when added to a disabled widget, will be disabled
         automatically.
      2. Disabling/enabling a parent disables/enables all
         of its children.

    .. versionadded:: 1.8.0

    .. versionchanged:: 1.10.1

        :attr:`disabled` was changed from a
        :class:`~kivy.properties.BooleanProperty` to an
        :class:`~kivy.properties.AliasProperty` to allow access to its
        previous state when a parent's disabled state is changed.
    '''

    motion_filter = DictProperty()
    '''Holds a dict of `type_id` to `list` of child widgets registered to
    receive motion events of `type_id`.

    Don't change the property directly but use
    :meth:`register_for_motion_event` and :meth:`unregister_for_motion_event`
    to register and unregister for motion events. If `self` is registered it
    will always be the first element in the list.

    .. versionadded:: 2.1.0

    .. warning::
        This is an experimental property and it remains so while this warning
        is present.
    '''
