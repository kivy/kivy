'''
Event Manager
=============

The :class:`EventManagerBase` is the abstract class intended for specific
implementation of dispatching motion events
(instances of :class:`~kivy.input.motionevent.MotionEvent`) to widgets through
:meth:`~kivy.uix.widget.Widget.on_motion` method of the
:class:`~kivy.uix.widget.Widget` class.

.. warning::
    This feature is experimental and it remains so while this warning is
    present.

Manager is a layer between the window and its widgets.
:class:`~kivy.core.window.WindowBase` will forward all the events it receives
in :meth:`~kivy.core.window.WindowBase.on_motion` method to the all managers
who declared to receive types of those events. Event will continue to go
through the managers list even if one of them accept it (by returning `True`).

When to use an event manager
----------------------------

Use a manager when you want to:

- Dispatch touch, hover, keyboard, joystick or any other events to the widgets
  through :meth:`~kivy.uix.widget.Widget.on_motion` method.
- Dispatch filtered motion events by any criteria, like by a
  :attr:`~kivy.input.motionevent.MotionEvent.device` or a
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
   :attr:`EventManagerBase.type_ids` attribute.
2. Implement :meth:`EventManagerBase.dispatch` which will be called by window
   to pass event type (one of "begin", "update", "end") and an event.
3. Implement :meth:`EventManagerBase.start` and :meth:`EventManagerBase.stop`
   to allocate and release additional resources if needed.
4. Register a manager instance to window using method
   :meth:`~kivy.core.window.WindowBase.register_event_manager`. This can be
   done by overriding methods :meth:`~kivy.app.App.build` or
   :meth:`~kivy.app.App.on_start`.

All registered managers are kept in the
:attr:`~kivy.core.window.WindowBase.event_managers` list. To unregister a
manager call :meth:`~kivy.core.window.WindowBase.unregister_event_manager`
which itself can be called in :meth:`~kivy.app.App.on_stop` method.

Dispatching events to the widgets
---------------------------------

Once registered, window will start the manager and forward all events of types
declared in :attr:`EventManagerBase.type_ids` to the manager's
:meth:`EventManagerBase.dispatch` method. It's up to manager to decide how to
dispatch them, either by going through :attr:`EventManagerBase.window.children`
list and dispatching `on_motion` event or by using some different logic. It's
also up to manager to dispatch grabbed events if grab feature is supported by
the event (see :meth:`~kivy.input.motionevent.MotionEvent.grab` and
:meth:`~kivy.input.motionevent.MotionEvent.ungrab` methods).

Manager can assign a different dispatch mode to decide how event
should be dispatched throughout the widget tree by changing the value of the
:attr:`~kivy.input.motionevent.MotionEvent.dispatch_mode` attribute. Before
changing the mode manager should store/restore the current one, either by using
a local variable or by using event's
:meth:`~kivy.input.motionevent.MotionEvent.push` /
:meth:`~kivy.input.motionevent.MotionEvent.pop` methods.

Currently there are three dispatch modes (behaviors) recognized by the
`on_motion` method in :class:`~kivy.uix.widget.Widget` class:

1. Default dispatch (requires :const:`MODE_DEFAULT_DISPATCH`) - event will go
   through widget's `children` list, starting with the first widget in the
   list until event gets accepted or last widget registered for that event is
   reached. Mode :const:`MODE_DEFAULT_DISPATCH` is assigned by default in
   :class:`~kivy.input.motionevent.MotionEvent` class.
2. Filtered dispatch (requires :const:`MODE_FILTERED_DISPATCH`) - event will go
   only through registered child widgets.
3. No dispatch to children (requires :const:`MODE_DONT_DISPATCH`) - event will
   not be dispatched to child widgets.

Note that window does not have a `motion_filter` property and therefore does
not have a list of filtered widgets from its `children` list.
'''

MODE_DEFAULT_DISPATCH = 'default'
'''Assign this mode to make event dispatch through widget's `children` list,
starting with the first widget in the list until event gets accepted or last
widget registered for that event is reached. Widgets after the last registered
widget are ignored.

.. versionadded:: 2.1.0
'''

MODE_FILTERED_DISPATCH = 'filtered'
'''Assign this mode to make event dispatch only to child widgets which were
previously registered to receive events of the same
:attr:`~kivy.input.motionevent.MotionEvent.type_id` and not to all
child widgets.

.. versionadded:: 2.1.0
'''

MODE_DONT_DISPATCH = 'none'
'''Assign this mode to prevent event from dispatching to child widgets.

.. versionadded:: 2.1.0
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
    '''Override this attribute to declare the type ids of the events which
    manager wants to receive. This attribute will be used by
    :class:`~kivy.core.window.WindowBase` to know which events to pass to the
    :meth:`dispatch` method.

    .. versionadded:: 2.1.0
    '''

    window = None
    '''Holds the instance of the :class:`~kivy.core.window.WindowBase`.

    .. versionadded:: 2.1.0
    '''

    def start(self):
        '''Start the manager, bind callbacks to the objects and create
        additional resources. Attribute :attr:`window` is assigned when this
        method is called.

        .. versionadded:: 2.1.0
        '''

    def dispatch(self, etype, me):
        '''Dispatch event `me` to the widgets in the :attr:`window`.

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
        '''Stop the manager, unbind from any objects and release any allocated
        resources.

        .. versionadded:: 2.1.0
        '''
