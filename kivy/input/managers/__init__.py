class EventManagerBase(object):

    def __init__(self, **kwargs):
        self.event_loop = None

    def dispatch(self, etype, me):
        pass
