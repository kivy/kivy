from kivy.input.managers import EventManagerBase


class HoverEventManager(EventManagerBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_name = 'hover'
        self.events = []

    def dispatch(self, etype, me):
        self.events.append(me)
        if not me.grab_exclusive_class:
            for listener in self.event_loop.event_listeners:
                listener.dispatch('on_motion', etype, me)

        # Handle grabbed events
        if len(self.events) < 2:
            return
        current = self.events[-1]
        prev = self.events[-2]
        for weak_widget in prev.grab_list:
            if weak_widget not in current.grab_list:
                # Notify widgets that are no longer handled by current
                # hover event. This handles the case when two widget are
                # overlapping and previous one wants to go to non-hovered
                # state.
                # TODO: Decide on how to flag this dispatch,
                # use `etype` argument or something else. We cannot use
                # attribute on current event.
                widget = weak_widget()
                if widget:
                    widget.dispatch('on_motion', 'end', current)
        self.events.pop(0)
