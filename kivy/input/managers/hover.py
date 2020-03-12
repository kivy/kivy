from collections import deque, defaultdict
from copy import deepcopy

from kivy.input.managers import EventManagerBase


class HoverEventManager(EventManagerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type_name = 'hover'
        self.dispatched_events = defaultdict(list)  # one event per device id
        self.waiting_events = deque()

    def update(self, etype, me):
        self.waiting_events.append((etype, me))

    def dispatch(self, *args):
        self.ensure_one_event_per_device()
        dispatched_events = self.dispatched_events
        while self.waiting_events:
            etype_me = self.waiting_events.popleft()
            device_id = etype_me[1].device_id
            dispatched_events[device_id].append(etype_me)
            if not etype_me[1].grab_exclusive_class:
                for listener in self.event_loop.event_listeners:
                    listener.dispatch('on_motion', *etype_me)

            # Handle grabbed events
            if len(dispatched_events[device_id]) < 2:
                continue
            _, current = dispatched_events[device_id][-1]
            _, prev = dispatched_events[device_id][-2]
            current.grab_state = True
            for weak_widget in prev.grab_list:
                if weak_widget not in current.grab_list:
                    # Notify widgets that are no longer handled by current
                    # hover event
                    widget = weak_widget()
                    if widget:
                        current.grab_current = widget
                        widget.dispatch('on_motion', 'end', current)
                        current.grab_current = None
            current.grab_state = False
            dispatched_events[device_id].pop(0)

    def ensure_one_event_per_device(self):
        if self.waiting_events:
            return
        # Dispatch copied event of last event dispatched
        for device_id, last_events in self.dispatched_events.items():
            last_etype, last_event = last_events[-1]
            if last_etype == 'update' or last_etype == 'start':
                event = type(last_event)(last_event.device,
                                         last_event.id,
                                         deepcopy(last_event.args))
                last_event.copy_to(event)
                self.waiting_events.append(('update', event))
