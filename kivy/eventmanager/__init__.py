class EventManagerBase(object):

    type_ids = tuple()

    def __init__(self):
        self.window = None

    def start(self):
        pass

    def update(self, etype, me):
        pass

    def stop(self):
        pass
