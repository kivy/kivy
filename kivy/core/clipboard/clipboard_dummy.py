'''
Clipboard Dummy: internal implementation without using system
'''

__all__ = ('ClipboardDummy', )

from . import ClipboardBase


class ClipboardDummy(ClipboardBase):

    def __init__(self):
        super(ClipboardDummy, self).__init__()
        self._data = dict()
        self._data['text/plain'] = None
        self._data['application/data'] = None

    def get(self, mimetype='text/plain'):
        return self._data.get(mimetype, None)

    def put(self, data, mimetype='text/plain'):
        self._data[mimetype] = data

    def get_types(self):
        return self._data.keys()

