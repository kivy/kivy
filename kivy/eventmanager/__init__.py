DONT_DISPATCH = 1
'''Suggest that event should not be dispatch to child widgets, but only go
through method resolution order of :meth:`~kivy.uix.widget.Widget.on_motion` so
that all super classes can handle the event.
'''

FILTERED_DISPATCH = 2
'''Suggest that event should be dispatched only to child widgets which were
previously registered to receive events of the same `type_id` and not to all
child widgets.
'''


class EventManagerBase(object):

    type_ids = tuple()

    def __init__(self):
        self.window = None

    def start(self):
        pass

    def dispatch(self, etype, me):
        pass

    def stop(self):
        pass
