'''
Clipboard OsX: implementation of clipboard using Appkit
'''

__all__ = ('ClipboardAppkit', )

from kivy.core.clipboard import ClipboardBase
from kivy.utils import platform
try:
    from AppKit import NSPasteboard
except ImportError:
    raise SystemError(
        'required package Appkit not installed,' +
        ' run `pip install appkit` from your console')

if platform != 'mac':
    raise SystemError('unsupported platform for appkit clipboard')


class ClipboardAppkit(ClipboardBase):

    def __init__(self):
        super(ClipboardDummy, self).__init__()
        self._clipboard = NSPasteboard.generalPasteboard()

    def get(self, mimetype='text/plain'):
        pb = self._clipboard
        return pb.stringForType_(NSStringPboardType)

    def put(self, data, mimetype='text/plain'):
        pb = self._clipboard
        pb.clearContents()
        pb.writeObjects((data,))

    def get_types(self):
        return list('text/plain',)
