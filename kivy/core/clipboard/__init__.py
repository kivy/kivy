'''
Clipboard: get/put data from system clipboard
'''

__all__ = ('ClipboardBase', 'Clipboard')

from kivy.core import core_select_lib

class ClipboardBase(object):
    def get(self, mimetype):
        '''Get the current data in clipboard, using the mimetype if possible
        '''
        return None

    def put(self, data, mimetype):
        '''Put data on the clipboard, and attach a mimetype
        '''
        pass

    def get_types(self):
        '''Return a list of supported mimetypes
        '''
        return []

# load clipboard implementation
Clipboard = core_select_lib('clipboard', (
    ('pygame', 'clipboard_pygame', 'ClipboardPygame'),
    ('dummy', 'clipboard_dummy', 'ClipboardDummy')
), True)
