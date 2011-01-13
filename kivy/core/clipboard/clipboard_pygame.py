'''
Clipboard Pygame: implementation of clipboard using pygame.scrap.
'''

__all__ = ('ClipboardPygame', )

import sys
from . import ClipboardBase

if sys.platform not in ('win32', 'cygwin'):
    raise SystemError('unsupported platform for pygame clipboard')

try:
    import pygame
    import pygame.scrap
except:
    raise


class ClipboardPygame(ClipboardBase):

    _is_init = False

    def init(self):
        if ClipboardPygame._is_init:
            return
        pygame.scrap.init()
        ClipboardPygame._is_init = True

    def get(self, mimetype='text/plain'):
        self.init()
        return pygame.scrap.get(mimetype)

    def put(self, data, mimetype='text/plain'):
        self.init()
        pygame.scrap.put(mimetype, data)

    def get_types(self):
        self.init()
        return pygame.scrap.get_types()

