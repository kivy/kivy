from collections import deque, defaultdict

from kivy.clock import Clock
from kivy.input.managers import EventManagerBase


class HoverEventManager(EventManagerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type_name = 'hover'
        self.min_wait_time = kwargs.get('min_wait_time', 1 / 30.0)
        self._waiting_events = deque()
        self._dispatched_events = defaultdict(list)  # event per device id
        self._event_times = {}  # time of event per device id

    def update(self, etype, me):
        self._waiting_events.append((etype, me))
        self._event_times[me.device_id] = Clock.get_time()

    def dispatch(self, *args):
        self.ensure_one_event_per_device()
        dispatched_events = self._dispatched_events
        dispatch_to_grabbed_widgets = self.dispatch_to_grabbed_widgets
        while self._waiting_events:
            etype, me = etype_me = self._waiting_events.popleft()
            device_id = me.device_id
            dispatched_events[device_id].append(etype_me)
            # Save grab_list of previous event
            _, prev_me = dispatched_events[device_id][-1]
            prev_me_grab_list = prev_me.grab_list[:]
            del me.grab_list[:]
            # Set 'me.etype' because it's needed by HoverBehavior
            me.ud['me.etype'] = etype
            # Dispatch to listeners
            if not me.grab_exclusive_class:
                for listener in self.event_loop.event_listeners:
                    listener.dispatch('on_motion', etype, me)
            # Must have 2 dispatched events to detect which widgets are not
            # handling current event `etype_me` (did not grabbed it)
            if len(dispatched_events[device_id]) > 1:
                dispatch_to_grabbed_widgets(etype, me, prev_me_grab_list)
                dispatched_events[device_id].pop(0)

    def dispatch_to_grabbed_widgets(self, etype, me, prev_me_grab_list):
        transform = self.transform_grabbed_event
        current_grab_list = me.grab_list[:]
        me.grab_state = True
        for weak_widget in prev_me_grab_list:
            if weak_widget not in current_grab_list:
                # Notify widgets that are no longer handled by current
                # hover event
                widget = weak_widget()
                if not widget:
                    continue
                root_window = widget.get_root_window()
                if root_window != widget and root_window:
                    me.push()
                    try:
                        me = transform(root_window, widget, me)
                    except AttributeError:
                        me.pop()
                        continue
                me.ud['me.etype'] = 'end'
                me.grab_current = widget
                widget._context.push()
                if widget._context.sandbox:
                    with widget._context.sandbox:
                        widget.dispatch('on_motion', 'end', me)
                else:
                    widget.dispatch('on_motion', 'end', me)
                widget._context.pop()
                me.grab_current = None
                me.ud['me.etype'] = etype
                if root_window != widget and root_window:
                    me.pop()
        me.grab_state = False

    def ensure_one_event_per_device(self):
        times = self._event_times
        dispatched_events = self._dispatched_events
        do_wait = self.min_wait_time > 0
        no_copy = self.min_wait_time < 0
        time_now = Clock.get_time()
        for_removal = []
        for device_id, last_events in dispatched_events.items():
            etype, me = last_events[-1]
            if etype == 'end':
                for_removal.append(device_id)
                continue
            if time_now == times[device_id] or no_copy:
                # Event from provider already exists in waiting list
                # or manager is only dispatching provider events
                continue
            if do_wait and time_now - times[device_id] < self.min_wait_time:
                # Wait for more time to pass
                continue
            self.update('update', me)
        for device_id in for_removal:
            del dispatched_events[device_id]
