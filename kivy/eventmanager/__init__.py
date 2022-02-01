'''
EventManagerBase
================

The :class:`EventManagerBase` is the abstract class intended for specific
implementation of dispatching motion events
(instances of :class:`~kivy.input.motionevent.MotionEvent`) to widgets through
:meth:`~kivy.uix.widget.Widget.on_motion` method.

.. warning::
    This feature is experimental and it remains so while this warning is
    present.

Manager is a layer between window and its widgets. Window will forward all the
events it receives in :meth:`~kivy.uix.widget.Widget.on_motion` method to
all managers who declared to receive types of those events. Event will continue
to go through managers even if one of them accepts it (by returning `True`).

When to use an event manager
----------------------------

Use a manager when you want to:

- Dispatch touch, hover, keyboard, joystick or any other events to the widgets
  through :meth:`~kivy.uix.widget.Widget.on_motion` method.
- Dispatch filtered motion events by any criteria, like by
  :attr:`~kivy.input.motionevent.MotionEvent.device` or
  :attr:`~kivy.input.motionevent.MotionEvent.profile`.
- Combine several motion events (touch, hover etc.) into one new event and
  dispatch it to the widgets.
- Dispatch one-time generic events, like app pause/resume.
- Write an event simulator, like a touch simulator which draws a circle on
  window's canvas for every simulated touch.

Defining and registering an event manager
-----------------------------------------

1. Inherit :class:`EventManagerBase` and set which events this manager
    should receive by declaring event types in
    `:attr:`EventManagerBase.type_ids` attribute.
2. Implement :meth:`EventManagerBase.dispatch` which will be called by window
    to pass event type (one of "begin", "update", "end") and an event.
3. Implement :meth:`EventManagerBase.start` and :meth:`EventManagerBase.stop`
    to allocate and release additional resources if needed.
4. Register a manager instance to window using method
    :meth:`~kivy.core.window.WindowBase.register_event_manager`. This can be
    done by overriding methods :meth:`~kivy.app.App.build` or
    :meth:`~kivy.app.App.on_start`.

All registered managers are kept in
:attr:`~kivy.core.window.WindowBase.event_managers` list. To unregister a
manager call :meth:`~kivy.core.window.WindowBase.unregister_event_manager`
which itself can be called in :meth:`~kivy.app.App.on_stop` method.

Dispatching events to the widgets
---------------------------------

Once registered, window will start the manager and forward all events of types
declared in :attr:`EventManagerBase.type_ids` to the manager's
:meth:`EventManagerBase.dispatch` method. It's up to manager to decide how to
dispatch them, either going through :attr:`EventManagerBase.window.children`
and dispatch `on_motion` event to them or by using some different logic. It's
also up to manager to dispatch grabbed events if widgets grab/ungrab to events
(see :meth:`~kivy.input.motionevent.MotionEvent.grab` and
:meth:`~kivy.input.motionevent.MotionEvent.ungrab` methods).

Manager can suggest how event should be dispatched further down the widget tree
by using different flags. Flags are assigned in
:attr:`~kivy.input.motionevent.MotionEvent.flags` attribute and inspected in
:meth:`~kivy.uix.widget.Widget.on_motion` method by using bitwise operations.
Widget can change the dispatch behavior by assigning different flags, but
before changing the `flags` value both manager and widget should store/restore
the current one, either by using a local variable or by using
:meth:`~kivy.input.motionevent.MotionEvent.push` /
:meth:`~kivy.input.motionevent.MotionEvent.pop` methods.

Currently there are three dispatch behaviors recognized by the
:class:`~kivy.uix.widget.Widget`:

1. Default dispatch - event will go through widget's `children` list, starting
    with the first widget in the list until event gets accepted or last widget
    registered for that event is reached. Flag :attr:`FLAG_DEFAULT_DISPATCH` is
    assigned by default in :class:`~kivy.input.motionevent.MotionEvent`.
2. Filtered dispatch (requires :attr:`FLAG_FILTERED_DISPATCH`) - event will go
    only through registered child widgets.
3. No dispatch to children (requires :attr:`FLAG_DONT_DISPATCH`) - event will
    not be dispatched to child widgets.

Note that window does not have `motion_filter` property and therefore does not
have a list of filtered widgets from its `children` list.
'''

FLAG_DONT_DISPATCH = 2 ** 0
'''Flag which suggest that event should not be dispatch to child widgets, but
only go through method resolution order of
:meth:`~kivy.uix.widget.Widget.on_motion` so that all super classes can handle
the event.
'''

FLAG_DEFAULT_DISPATCH = 2 ** 1
'''Flag which suggest that event should go through widget's `children` list,
starting with the first widget in the list until event gets accepted or last
widget registered for that event is reached. Widgets after the last registered
widget are ignored.
'''

FLAG_FILTERED_DISPATCH = 2 ** 2
'''Flag which suggest that event should be dispatched only to child widgets
which were previously registered to receive events of the same
:attr:`~kivy.input.motionevent.MotionEvent.type_id` and not to all
child widgets.
'''

NEXT_FLAG_EXP = 3
'''Next exponent value for flags. If you're creating new event flags in your
app use this value as initial value for the exponent::

    FLAG_EXAMPLE_1 = 2 ** NEXT_FLAG_EXP
    FLAG_EXAMPLE_2 = 2 ** (NEXT_FLAG_EXP + 1)
    FLAG_EXAMPLE_3 = 2 ** (NEXT_FLAG_EXP + 2)
'''


class EventManagerBase(object):
    '''Abstract class with methods :meth:`start`, :meth:`stop` and
    :meth:`dispatch` for specific class to implement.

    Example of the manager receiving touch and hover events::

        class TouchHoverManager(EventManagerBase):

            type_ids = ('touch', 'hover')

            def start(self):
                # Create additional resources, bind callbacks to self.window

            def dispatch(self, etype, me):
                if me.type_id == 'touch':
                    # Handle touch event
                elif me.type_id == 'hover'
                    # Handle hover event

            def stop(self):
                # Release resources

    '''

    type_ids = None
    '''Override this attribute to declare type ids of events which manager will
    receive. This attribute will be used by
    :class:`~kivy.core.window.WindowBase` to know which events to pass to
    method :meth:`dispatch`.

    .. versionadded:: 2.1.0
    '''

    window = None
    '''Holds an instance of :class:`~kivy.core.window.WindowBase`.

    .. versionadded:: 2.1.0
    '''

    def start(self):
        '''Start the manager, bind callbacks to objects and create additional
        resources. Attribute :attr:`window` is assigned when this method is
        called.

        .. versionadded:: 2.1.0
        '''

    def dispatch(self, etype, me):
        '''Dispatch event `me` to widgets in :attr:`window`.

        :Parameters:
            `etype`: `str`
                One of "begin", "update" or "end"
            `me`: :class:`~kivy.input.motionevent.MotionEvent`
                The Motion Event currently dispatched.
        :Returns: `bool`
            `True` to stop event dispatching

        .. versionadded:: 2.1.0
        '''

    def stop(self):
        '''Stop the manager, unbind from any objects and to release any
        allocated resources.

        .. versionadded:: 2.1.0
        '''
