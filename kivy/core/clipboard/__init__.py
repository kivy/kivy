'''
Clipboard
=========

Core class for accessing the Clipboard. If we are not able to access the
system clipboard, a fake one will be used.

Usage example:

.. code-block:: kv

    #:import Clipboard kivy.core.clipboard.Clipboard

    Button:
        on_release:
            self.text = Clipboard.paste()
            Clipboard.copy('Data')
'''

__all__ = ('ClipboardBase', 'Clipboard')

from kivy import Logger
from kivy.core import core_select_lib
from kivy.utils import platform
from kivy.setupconfig import USE_SDL2


class ClipboardBase(object):

    def get(self, mimetype):
        '''Get the current data in clipboard, using the mimetype if possible.
        You not use this method directly. Use :meth:`paste` instead.
        '''
        return None

    def put(self, data, mimetype):
        '''Put data on the clipboard, and attach a mimetype.
        You should not use this method directly. Use :meth:`copy` instead.
        '''
        pass

    def get_types(self):
        '''Return a list of supported mimetypes
        '''
        return []

    def _ensure_clipboard(self):
        ''' Ensure that the clipboard has been properly initialised.
        '''

        if hasattr(self, '_clip_mime_type'):
            return

        if platform == 'win':
            self._clip_mime_type = 'text/plain;charset=utf-8'
            # windows clipboard uses a utf-16 little endian encoding
            self._encoding = 'utf-16-le'
        elif platform == 'linux':
            self._clip_mime_type = 'text/plain;charset=utf-8'
            self._encoding = 'utf-8'
        else:
            self._clip_mime_type = 'text/plain'
            self._encoding = 'utf-8'

    def copy(self, data=''):
        ''' Copy the value provided in argument `data` into current clipboard.
        If data is not of type string it will be converted to string.

        .. versionadded:: 1.9.0

        '''
        if data:
            self._copy(data)

    def paste(self):
        ''' Get text from the system clipboard and return it a usable string.

        .. versionadded:: 1.9.0

        '''
        return self._paste()

    def _copy(self, data):
        self._ensure_clipboard()
        if not isinstance(data, bytes):
            data = data.encode(self._encoding)
        self.put(data, self._clip_mime_type)

    def _paste(self):
        self._ensure_clipboard()
        _clip_types = Clipboard.get_types()

        mime_type = self._clip_mime_type
        if mime_type not in _clip_types:
            mime_type = 'text/plain'

        data = self.get(mime_type)
        if data is not None:
            # decode only if we don't have unicode
            # we would still need to decode from utf-16 (windows)
            # data is of type bytes in PY3
            if isinstance(data, bytes):
                data = data.decode(self._encoding, 'ignore')
            # remove null strings mostly a windows issue
            data = data.replace(u'\x00', u'')
            return data
        return u''


# load clipboard implementation
_clipboards = []
if platform == 'android':
    _clipboards.append(
        ('android', 'clipboard_android', 'ClipboardAndroid'))
elif platform == 'macosx':
    _clipboards.append(
        ('nspaste', 'clipboard_nspaste', 'ClipboardNSPaste'))
elif platform == 'win':
    _clipboards.append(
        ('winctypes', 'clipboard_winctypes', 'ClipboardWindows'))
elif platform == 'linux':
    _clipboards.append(
        ('dbusklipper', 'clipboard_dbusklipper', 'ClipboardDbusKlipper'))
    _clipboards.append(
        ('gtk3', 'clipboard_gtk3', 'ClipboardGtk3'))
    _clipboards.append(
        ('xclip', 'clipboard_xclip', 'ClipboardXclip'))
    _clipboards.append(
        ('xsel', 'clipboard_xsel', 'ClipboardXsel'))

if USE_SDL2:
    _clipboards.append(
        ('sdl2', 'clipboard_sdl2', 'ClipboardSDL2'))
else:
    _clipboards.append(
        ('pygame', 'clipboard_pygame', 'ClipboardPygame'))

_clipboards.append(
    ('dummy', 'clipboard_dummy', 'ClipboardDummy'))

Clipboard = core_select_lib('clipboard', _clipboards, True)
CutBuffer = None

if platform == 'linux':
    _cutbuffers = [
        ('xclip', 'clipboard_xclip', 'ClipboardXclip'),
        ('xsel', 'clipboard_xsel', 'ClipboardXsel'),
    ]

    if Clipboard.__class__.__name__ in (c[2] for c in _cutbuffers):
        CutBuffer = Clipboard
    else:
        CutBuffer = core_select_lib('cutbuffer', _cutbuffers, True,
                                    basemodule='clipboard')

    if CutBuffer:
        Logger.info('CutBuffer: cut buffer support enabled')
