"""
HoverManager
============

.. versionadded:: 3.0.0

.. note::
    :class:`HoverManager` is part of the `hover` package which can be found in
    the GitHub `repository <https://github.com/pythonic64/hover>`_. You can
    install the `hover` package using the instructions from the GitHub page, if
    you want to use `Kivy>=2.1.0,<3.0.0`.

:class:`HoverManager` is responsible for dispatching of hover events to widgets
in the `Window`'s :attr:`~kivy.core.window.WindowBase.children` list. Widgets
must register for hover events using
:meth:`~kivy.uix.widget.Widget.register_for_motion_event` to be able to receive
those events in the :meth:`~kivy.uix.widget.Widget.on_motion` method.

For your app to use a hover manager, you must register it with
:meth:`~kivy.core.window.WindowBase.register_event_manager` when app starts
and then unregister it with
:meth:`~kivy.core.window.WindowBase.unregister_event_manager` when app stops.

Example of how to register/unregister a hover manager::

    from kivy.app import App
    from kivy.eventmanager.hover import HoverManager

    class HoverApp(App):

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.hover_manager = HoverManager()

        def on_start(self):
            super().on_start()
            self.root_window.register_event_manager(self.hover_manager)

        def on_stop(self):
            super().on_stop()
            self.root_window.unregister_event_manager(self.hover_manager)

Manager expects every widget to always grab the event, if they want to receive
event type "end" for that same event while the event is in the grabbed state.
To grab an event use :meth:`~kivy.input.motionevent.MotionEvent.grab` and to
ungrab it use :meth:`~kivy.input.motionevent.MotionEvent.ungrab`. Manager
manipulates event's :attr:`~kivy.input.motionevent.MotionEvent.grab_list`
when dispatching an event to widgets, which is needed to ensure that widgets
receive "end" event type for the same event. It will also restore the original
:attr:`~kivy.input.motionevent.MotionEvent.grab_list`, received in its
:meth:`~kivy.eventmanager.EventManagerBase.dispatch` method, after the dispatch
is done.

Event dispatching works in the following way:

1. If an event is received for the first time, manager will dispatch it to all
   widgets in the :attr:`~kivy.core.window.WindowBase.children` list and
   internally store the event itself, copy of the new
   :attr:`~kivy.input.motionevent.MotionEvent.grab_list`, and the time of the
   dispatch. Values are stored for every event, per its
   :attr:`~kivy.input.motionevent.MotionEvent.uid`.
2. When the same event is received for the second time, step 1. is done again,
   and then follows the dispatch to the widgets who grabbed that same event.
   Manager will dispatch event type "end" to the widgets who are found in the
   previously stored :attr:`~kivy.input.motionevent.MotionEvent.grab_list` and
   not found in the event's current `grab_list`. This way is ensured that
   widgets can handle their state if they didn't receive "update" or "begin"
   event type in the second time dispatch.
3. If a hover event is static (its position doesn't change) and
   :attr:`HoverManager.event_repeat_timeout` is greater or equal to 0, manager
   will dispatch an event type "update" to all events stored in step 1. using
   :attr:`HoverManager.event_repeat_timeout` as timeout between the static
   events.
4. On the event type "end", data stored in the step 1. is removed from the
   manager's internal storage.

See :class:`HoverManager` for details.
"""

from collections import defaultdict

from kivy.eventmanager import EventManagerBase

Clock = None


class HoverManager(EventManagerBase):
    """Manager for dispatching hover events to widgets in the window children
    list.

    When registered, manager will receive all events with `type_id` set to
    "hover", transform them to match :attr:`window` size and then dispatch them
    through the `window.children` list using the `on_motion` event.

    To handle a case when the hover event position did not change within
    `event_repeat_timeout` seconds, manager will re-dispatch the event with all
    delta values set to 0, so that widgets can re-handle the event.
    This is useful for the case when a mouse is used to scroll a recyclable
    list of widgets, but the mouse indicator position is not changing.
    """

    type_ids = ('hover',)

    event_repeat_timeout = 1 / 30.0
    """Minimum wait time to repeat existing static hover events and it defaults
    to `1/30.0` seconds. Negative value will turn off the feature.

    To change the default value use `event_repeat_timeout` keyword while making
    a manager instance or set it directly after the instance is made. Changing
    the value after the manager has started will have no effect.
    """

    def __init__(self, **kwargs):
        super().__init__()
        self.event_repeat_timeout = kwargs.get(
            'event_repeat_timeout',
            HoverManager.event_repeat_timeout
        )
        self._events = defaultdict(list)  # me.uid -> [(me, me.grab_list[:]),]
        self._event_times = {}  # me.uid -> Clock.get_time()
        self._clock_event = None

    def start(self):
        if self.event_repeat_timeout >= 0:
            global Clock
            if not Clock:
                from kivy.clock import Clock
            self._clock_event = Clock.schedule_interval(
                self._dispatch_from_clock,
                self.event_repeat_timeout
            )

    def stop(self):
        self._events.clear()
        self._event_times.clear()
        if self._clock_event:
            self._clock_event.cancel()
            self._clock_event = None

    def dispatch(self, etype, me):
        me_grab_list = me.grab_list[:]
        del me.grab_list[:]
        accepted = self._dispatch_to_widgets(etype, me)
        self._events[me.uid].insert(0, (me, me.grab_list[:]))
        self._event_times[me.uid] = Clock.get_time() if Clock else 0
        if len(self._events[me.uid]) == 2:
            _, prev_me_grab_list = self._events[me.uid].pop()
            self._dispatch_to_grabbed_widgets(me, prev_me_grab_list)
        if etype == 'end':
            del self._events[me.uid]
            del self._event_times[me.uid]
        me.grab_list[:] = me_grab_list
        return accepted

    def _dispatch_to_widgets(self, etype, me):
        accepted = False
        me.push()
        self.window.transform_motion_event_2d(me)
        for widget in self.window.children[:]:
            if widget.dispatch('on_motion', etype, me):
                accepted = True
                break
        me.pop()
        return accepted

    def _dispatch_to_grabbed_widgets(self, me, prev_me_grab_list):
        prev_grab_state = me.grab_state
        prev_time_end = me.time_end
        me_grab_list = me.grab_list[:]
        me.grab_list[:] = prev_me_grab_list
        me.update_time_end()
        me.grab_state = True
        for weak_widget in prev_me_grab_list:
            if weak_widget not in me_grab_list:
                widget = weak_widget()
                if widget:
                    self._dispatch_to_widget('end', me, widget)
        me.grab_list[:] = me_grab_list
        me.grab_state = prev_grab_state
        me.time_end = prev_time_end

    def _dispatch_to_widget(self, etype, me, widget):
        root_window = widget.get_root_window()
        if root_window and root_window != widget:
            me.push()
            try:
                self.window.transform_motion_event_2d(me, widget)
            except AttributeError:
                me.pop()
                return
        prev_grab_current = me.grab_current
        me.grab_current = widget
        widget._context.push()
        if widget._context.sandbox:
            with widget._context.sandbox:
                widget.dispatch('on_motion', etype, me)
        else:
            widget.dispatch('on_motion', etype, me)
        widget._context.pop()
        me.grab_current = prev_grab_current
        if root_window and root_window != widget:
            me.pop()

    def _dispatch_from_clock(self, *args):
        times = self._event_times
        time_now = Clock.get_time()
        events_to_update = []
        for me_id, items in self._events.items():
            me, _ = items[0]
            if time_now - times[me.uid] < self.event_repeat_timeout:
                continue
            events_to_update.append(me)
        for me in events_to_update:
            psx, psy, psz = me.psx, me.psy, me.psz
            dsx, dsy, dsz = me.dsx, me.dsy, me.dsz
            me.psx, me.psy, me.psz = me.sx, me.sy, me.sz
            me.dsx = me.dsy = me.dsz = 0.0
            self.dispatch('update', me)
            me.psx, me.psy, me.psz = psx, psy, psz
            me.dsx, me.dsy, me.dsz = dsx, dsy, dsz
