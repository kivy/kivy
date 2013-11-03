'''
Clipboard OsX: implementation of clipboard using Appkit
'''

__all__ = ('ClipboardAppkit', )

from kivy.core.clipboard import ClipboardBase
from AppKit import NSPasteboard


class ClipboardAppkit(ClipboardBase):

    def __init__(self):
        super(ClipboardDummy, self).__init__()
        self._clipboard = NSPasteboard.generalPasteboard()

    def get(self, mimetype='text/plain'):
        pb = self._clipboard
        pb.stringForType_(NSStringPboardType)
        return self._data.get(mimetype, None)

    def put(self, data, mimetype='text/plain'):
        pb = self._clipboard
        pb.clearContents()
        pb.writeObjects((data,))

    def get_types(self):
        return list(self._data.keys())

