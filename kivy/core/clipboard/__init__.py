'''
Clipboard
=========

Core class for accessing to the Clipboard. If we are not able to access to the
system clipboard, a fake one will be used.
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
    ('dummy', 'clipboard_dummy', 'ClipboardDummy')), True)

