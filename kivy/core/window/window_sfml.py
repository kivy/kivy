'''
Window Pygame: windowing provider based on Pygame
.. versionadded: 1.4.0
'''

__all__ = ('WindowSFML', )

import os
import sfml.window as sf
from kivy.base import stopTouchApp, EventLoop, ExceptionManager
from kivy.core.window import WindowBase
from kivy.core  import CoreCriticalException
from kivy.config import Config
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.utils import platform

android = None
if platform() == 'android':
    import android

    glReadPixels = GL_RGBA = GL_UNSIGNED_BYTE = None

class WindowSFML(WindowBase):

    def create_window(self, *largs):
        self.dispatch('on_mouse_up', 0, 0, 'all', [])
        self._prepare_window()
        self._prepare_keyboard()

    def _prepare_window(self, *largs):

        mode = sf.VideoMode.get_desktop_mode()
        title = self.title
        self.flags = sf.Style.DEFAULT
        if (platform() in ('linux', 'macosx', 'win')
            and Config.getint('graphics', 'resizable')):
            self.style |= sf.Style.RESIZE

        multisamples = Config.getint('graphics', 'multisamples')
        settings = sf.ContextSettings(
            depth=16, stencil=1, antialiasing=multisamples)

        # TODO: move to WindowBase
        if self.position == 'auto':
            self._pos = None
        elif self.position == 'custom':
            self._pos = self.left, self.top
        else:
            raise ValueError('position token in configuration accept only '
                             '"auto" or "custom"')

        if self.fullscreen == 'fake':
            Logger.debug('WinSFML: Set window to fake fullscreen mode.')
            self.flags = sf.Style.NONE | sf.Style.FULL
        elif self.fullscreen is True:
            Logger.debug('WinSFML: Set window to fullscreen mode')
            self.flags = sf.Style.F

        self._pos = self._pos or (0, 0)
        self._window = sf.RenderWindow(mode, title, self.fl, settings)

    def _prepare_keyboard(self, *largs):
