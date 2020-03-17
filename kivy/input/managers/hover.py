from collections import deque, defaultdict
from copy import deepcopy

from kivy.clock import Clock
from kivy.input.managers import EventManagerBase


class HoverEventManager(EventManagerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type_name = 'hover'
        self.min_wait_time = kwargs.get('min_wait_time', 1/30.0)
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
            if not etype_me[1].grab_exclusive_class:
                for listener in self.event_loop.event_listeners:
                    listener.dispatch('on_motion', *etype_me)
            # Handle grabbed events
            # Must have 2 dispatched events to detect on which widgets
            # indicator is no longer hovering
            if len(dispatched_events[device_id]) < 2:
                continue
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
                    current.grab_current = widget
                    widget.dispatch('on_motion', 'end', current)
                    current.grab_current = None
                if root_window != widget and root_window:
                    current.pop()
        current.grab_state = False
        if current_etype == 'end':
            del self._dispatched_events[device_id]
            del self._event_times[device_id]
        else:
            self._dispatched_events[device_id].pop(0)

    def ensure_one_event_per_device(self):
        times = self._event_times
        for device_id, last_events in self._dispatched_events.items():
            if Clock.get_time() - times[device_id] < self.min_wait_time:
                continue
            # Dispatch copied event of last event dispatched
            last_etype, last_event = last_events[-1]
            if last_etype == 'update' or last_etype == 'start':
                event = type(last_event)(last_event.device,
                                         last_event.id,
                                         deepcopy(last_event.args))
                last_event.copy_to(event)
                self.update('update', event)
