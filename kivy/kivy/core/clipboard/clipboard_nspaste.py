'''
Clipboard OsX: implementation of clipboard using Appkit
'''

__all__ = ('ClipboardNSPaste', )

from kivy.core.clipboard import ClipboardBase
from kivy.utils import platform

if platform != 'macosx':
    raise SystemError('Unsupported platform for appkit clipboard.')
try:
    from pyobjus import autoclass
    from pyobjus.dylib_manager import load_framework, INCLUDE
    load_framework(INCLUDE.AppKit)
except ImportError:
    raise SystemError('Pyobjus not installed. Please run the following'
        ' command to install it. `pip install --user pyobjus`')

NSPasteboard = autoclass('NSPasteboard')
NSString = autoclass('NSString')


class ClipboardNSPaste(ClipboardBase):

    def __init__(self):
        super(ClipboardNSPaste, self).__init__()
        self._clipboard = NSPasteboard.generalPasteboard()

    def get(self, mimetype='text/plain'):
        pb = self._clipboard
        data = pb.stringForType_('public.utf8-plain-text')
        if not data:
            return ""
        return data.UTF8String()

    def put(self, data, mimetype='text/plain'):
        pb = self._clipboard
        pb.clearContents()
        utf8 = NSString.alloc().initWithUTF8String_(data)
        pb.setString_forType_(utf8, 'public.utf8-plain-text')

    def get_types(self):
        return list('text/plain',)
