class EventManagerBase(object):

    def __init__(self, **kwargs):
        self.event_loop = None

    def update(self, etype, me):
        pass

    def dispatch(self, *args):
        pass
