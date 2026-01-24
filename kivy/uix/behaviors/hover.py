"""
HoverBehavior
=============

.. versionadded:: 3.0.0

.. note::
    :class:`HoverBehavior` is part of the `hover` package which can be found in
    the GitHub `repository <https://github.com/pythonic64/hover>`_. You can
    install the `hover` package using the instructions from the GitHub page, if
    you want to use `Kivy>=2.1.0,<3.0.0`.

:class:`HoverBehavior` is a `mixin <https://en.wikipedia.org/wiki/Mixin>`_
class which handles hover events received in the
:meth:`~kivy.uix.widget.Widget.on_motion` method. It depends on
:class:`~kivy.eventmanager.hover.HoverManager` and its way of dispatching of
hover events - events with :attr:`~kivy.input.motionevent.MotionEvent.type_id`
set to "hover". Therefore, for :class:`HoverBehavior` to work,
:class:`~kivy.eventmanager.hover.HoverManager` must be registered in
:class:`~kivy.core.window.WindowBase`.

For an overview of behaviors, please refer to the :mod:`~kivy.uix.behaviors`
documentation.

As a mixin class, :class:`HoverBehavior` must be combined with other widgets::

    class HoverWidget(HoverBehavior, Widget):
        pass

Behavior supports multi-hover - if one or multiple hover events are hovering
over a widget, then its property :attr:`HoverBehavior.hovered` will be set to
`True`.

Example app showing a widget which when hovered with a mouse indicator will
change color from gray to green::

    from kivy.app import App
    from kivy.eventmanager.hover import HoverManager
    from kivy.lang import Builder
    from kivy.uix.behaviors import HoverBehavior
    from kivy.uix.widget import Widget

    Builder.load_string(\"""
    <RootWidget>:
        canvas.before:
            Color:
                rgba: [0, 0.5, 0, 1] if self.hovered else [0.5, 0.5, 0.5, 1]
            Rectangle:
                pos: self.pos
                size: self.size
    \""")


    class RootWidget(HoverBehavior, Widget):
        pass


    class HoverBehaviorApp(App):

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.hover_manager = HoverManager()

        def build(self):
            return RootWidget(size_hint=(0.5, 0.5),
                              pos_hint={'center_x': 0.5, 'center_y': 0.5})

        def on_start(self):
            super().on_start()
            self.root_window.register_event_manager(self.hover_manager)

        def on_stop(self):
            super().on_stop()
            self.root_window.unregister_event_manager(self.hover_manager)


    if __name__ == '__main__':
        HoverBehaviorApp().run()

See :class:`HoverBehavior` for details.

HoverCollideBehavior
--------------------

:class:`HoverCollideBehavior` is a
`mixin <https://en.wikipedia.org/wiki/Mixin>`_ class which filters hover events
which do not collide with a widget or events for which currently grabbed
widget is not the widget itself.

For an overview of behaviors, please refer to the :mod:`~kivy.uix.behaviors`
documentation.

:class:`HoverCollideBehavior` is meant to be used with
:class:`~kivy.uix.stencilview.StencilView` or its subclasses so that hover
events (events with :attr:`~kivy.input.motionevent.MotionEvent.type_id` set to
"hover") don't get handled when their position is outside the view.

Example of using :class:`HoverCollideBehavior` with
:class:`~kivy.uix.recycleview.RecycleView`::

    from kivy.uix.behaviors import HoverCollideBehavior
    from kivy.uix.recycleview import RecycleView


    class HoverRecycleView(HoverCollideBehavior, RecycleView):
        pass

:class:`HoverCollideBehavior` overrides
:meth:`~kivy.uix.widget.Widget.on_motion` to add event filtering::

    class HoverCollideBehavior(object):

        def on_motion(self, etype, me):
            if me.type_id != 'hover':
                return super().on_motion(etype, me)
            if me.grab_current is self or self.collide_point(*me.pos):
                return super().on_motion(etype, me)
"""

from kivy.eventmanager import MODE_DONT_DISPATCH
from kivy.properties import AliasProperty, DictProperty, OptionProperty


class HoverBehavior(object):
    """HoverBehavior `mixin <https://en.wikipedia.org/wiki/Mixin>`_ to handle
    hover events.

    Behavior will register widget to receive hover events (events with
    `type_id` set to "hover") and update attributes :attr:`hovered` and
    :attr:`hover_ids` depending on the received events.

    :Events:
        `on_hover_event`: `(etype, me)`
            Dispatched when this widget receives a hover event.
        `on_hover_enter`: `(me, )`
            Dispatched when a hover event collides with this widget for the
            first time.
        `on_hover_update`: `(me, )`
            Dispatched when a hover event position has changed, but it's still
            within this widget.
        `on_hover_leave`: `(me, )`
            Dispatched when a hover event is no longer within this widget or
            when an event type "end" is received.
    """

    def _get_hovered(self):
        return bool(self.hover_ids)

    hovered = AliasProperty(_get_hovered, bind=['hover_ids'], cache=True)
    """Indicates if this widget is hovered by at least one hover event.

    :attr:`hovered` is a :class:`~kivy.properties.AliasProperty`.
    """

    hover_ids = DictProperty()
    """Holds hover `event.uid` to `event.pos` values.

    :attr:`hover_ids` is a :class:`~kivy.properties.DictProperty`.
    """

    hover_mode = OptionProperty('default', options=['default', 'all', 'self'])
    """How this widget will dispatch received hover events.

    Options:

    - ``'default'``: Dispatch to `children` first and if none of the child
    widgets accepted the event (by returning `True`), then dispatch
    `on_hover_event` so that this widget can try to handle it.

    - ``'all'``: Same as `default`, but always dispatch `on_hover_event`.

    - ``'self'``: Don't dispatch to `children`, but dispatch `on_hover_event`.
    """

    __events__ = ('on_hover_event', 'on_hover_enter', 'on_hover_update',
                  'on_hover_leave')

    def __init__(self, **kwargs):
        self.register_for_motion_event('hover')
        super().__init__(**kwargs)

    def on_motion(self, etype, me):
        if not (me.type_id == 'hover' and 'pos' in me.profile):
            return super().on_motion(etype, me)
        if self.hover_mode == 'default':
            if super().on_motion(etype, me):
                return True
            return self.dispatch('on_hover_event', etype, me)
        prev_mode = me.dispatch_mode
        if self.hover_mode == 'self':
            me.dispatch_mode = MODE_DONT_DISPATCH
        accepted = super().on_motion(etype, me)
        accepted = self.dispatch('on_hover_event', etype, me) or accepted
        me.dispatch_mode = prev_mode
        return accepted

    def on_hover_event(self, etype, me):
        """Called when a hover event is received.

        This method will test if event collides with this widget using
        :meth:`collide_point` and dispatch `on_hover_enter`, `on_hover_update`
        or `on_hover_leave` events.

        :Parameters:
            `etype`: `str`
                Event type, one of "begin", "update" or "end"
            `me`: :class:`~kivy.input.motionevent.MotionEvent`
                Hover motion event
        """
        if etype == 'update' or etype == 'begin':
            if me.grab_current is self:
                return True
            if self.disabled and self.collide_point(*me.pos):
                return True
            if self.collide_point(*me.pos):
                me.grab(self)
                if me.uid not in self.hover_ids:
                    self.hover_ids[me.uid] = me.pos
                    self.dispatch('on_hover_enter', me)
                elif self.hover_ids[me.uid] != me.pos:
                    self.hover_ids[me.uid] = me.pos
                    self.dispatch('on_hover_update', me)
                return True
        elif etype == 'end':
            if me.grab_current is self:
                self.hover_ids.pop(me.uid)
                me.ungrab(self)
                self.dispatch('on_hover_leave', me)
                return True
            if self.disabled and self.collide_point(*me.pos):
                return True

    def on_hover_enter(self, me):
        pass

    def on_hover_update(self, me):
        pass

    def on_hover_leave(self, me):
        pass


class HoverCollideBehavior(object):
    """HoverCollideBehavior `mixin <https://en.wikipedia.org/wiki/Mixin>`_
    overrides :meth:`~kivy.uix.widget.Widget.on_motion` to filter-out hover
    events which do not collide with the widget or hover events which are not
    grabbed events.

    It's recommended to use this behavior with
    :class:`~kivy.uix.stencilview.StencilView` or its subclasses
    (`RecycleView`, `ScrollView`, etc.), so that hover events don't get handled
    when outside of stencil view.
    """

    def on_motion(self, etype, me):
        if me.type_id != 'hover':
            return super().on_motion(etype, me)
        if me.grab_current is self or self.collide_point(*me.pos):
            return super().on_motion(etype, me)
