'''
Clipboard
=========

Core class for accessing the Clipboard. If we are not able to access the
system clipboard, a fake one will be used.

Usage example::

    >>> from kivy.core.clipboard import Clipboard
    >>> Clipboard.get_types()
    ['TIMESTAMP', 'TARGETS', 'MULTIPLE', 'SAVE_TARGETS', 'UTF8_STRING',
    'COMPOUND_TEXT', 'TEXT', 'STRING', 'text/plain;charset=utf-8',
    'text/plain']
    >>> Clipboard.get('TEXT')
    'Hello World'
    >>> Clipboard.put('Great', 'UTF8_STRING')
    >>> Clipboard.get_types()
    ['UTF8_STRING']
    >>> Clipboard.get('UTF8_STRING')
    'Great'

.. note:: The main implementation relies on Pygame and works well with
          text/strings. Anything else might not work the same on all platforms.
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

