from collections import deque, defaultdict
from copy import deepcopy

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
        dispatch_grabbed_events = self.dispatch_grabbed_events
        while self._waiting_events:
            etype_me = self._waiting_events.popleft()
            device_id = etype_me[1].device_id
            dispatched_events[device_id].append(etype_me)
            etype_me[1].ud['me.etype'] = etype_me[0]
            if not etype_me[1].grab_exclusive_class:
                for listener in self.event_loop.event_listeners:
                    listener.dispatch('on_motion', *etype_me)
            # Must have 2 dispatched events to detect which widgets are not
            # handling current event `etype_me` (did not grabbed it)
            if len(dispatched_events[device_id]) > 1:
                dispatch_grabbed_events(device_id)

    def dispatch_grabbed_events(self, device_id):
        current_etype, current = self._dispatched_events[device_id][-1]
        _, prev = self._dispatched_events[device_id][-2]
        transform = self.transform_grabbed_event
        current.grab_state = True
        for weak_widget in prev.grab_list:
            if weak_widget not in current.grab_list:
                # Notify widgets that are no longer handled by current
                # hover event
                widget = weak_widget()
                if not widget:
                    continue
                root_window = widget.get_root_window()
                if root_window != widget and root_window:
                    current.push()
                    try:
                        current = transform(root_window, widget, current)
                    except AttributeError:
                        current.pop()
                        continue
                current.ud['me.etype'] = 'end'
                current.grab_current = widget
                widget._context.push()
                if widget._context.sandbox:
                    with widget._context.sandbox:
                        widget.dispatch('on_motion', 'end', current)
                else:
                    widget.dispatch('on_motion', 'end', current)
                widget._context.pop()
                current.grab_current = None
                current.ud['me.etype'] = current_etype
                if root_window != widget and root_window:
                    current.pop()
        current.grab_state = False
        self._dispatched_events[device_id].pop(0)

    def ensure_one_event_per_device(self):
        times = self._event_times
        dispatched_events = self._dispatched_events
        do_wait = self.min_wait_time != 0
        time_now = Clock.get_time()
        for_removal = []
        for device_id, last_events in dispatched_events.items():
            etype, me = last_events[-1]
            if etype == 'end':
                for_removal.append(device_id)
                continue
            if do_wait and time_now - times[device_id] < self.min_wait_time:
                continue
            # Dispatch copied event of last event dispatched
            event = type(me)(me.device, me.id, deepcopy(me.args))
            me.copy_to(event)
            self.update('update', event)
        for device_id in for_removal:
            del dispatched_events[device_id]
