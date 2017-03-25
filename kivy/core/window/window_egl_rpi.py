'''
EGL Rpi Window: EGL Window provider, specialized for the Pi

Inspired by: rpi_vid_core + JF002 rpi kivy  repo
'''

__all__ = ('WindowEglRpi', )

from kivy.logger import Logger
from kivy.core.window import WindowBase
from kivy.base import EventLoop, ExceptionManager, stopTouchApp
from kivy.lib.vidcore_lite import bcm, egl
from os import environ

# Default display IDs.
(DISPMANX_ID_MAIN_LCD,
 DISPMANX_ID_AUX_LCD,
 DISPMANX_ID_HDMI,
 DISPMANX_ID_SDTV,
 DISPMANX_ID_FORCE_LCD,
 DISPMANX_ID_FORCE_TV,
 DISPMANX_ID_FORCE_OTHER) = range(7)


class WindowEglRpi(WindowBase):

    _rpi_dispmanx_id = int(environ.get("KIVY_BCM_DISPMANX_ID", "0"))
    _rpi_dispmanx_layer = int(environ.get("KIVY_BCM_DISPMANX_LAYER", "0"))

    def create_window(self):
        bcm.host_init()

        w, h = bcm.graphics_get_display_size(self._rpi_dispmanx_id)
        Logger.debug('Window: Actual display size: {}x{}'.format(
            w, h))
        self._size = w, h
        self._create_window(w, h)
        self._create_egl_context(self.win, 0)
        super(WindowEglRpi, self).create_window()

    def _create_window(self, w, h):
        dst = bcm.Rect(0, 0, w, h)
        src = bcm.Rect(0, 0, w << 16, h << 16)
        display = egl.bcm_display_open(self._rpi_dispmanx_id)
        update = egl.bcm_update_start(0)
        element = egl.bcm_element_add(
            update, display, self._rpi_dispmanx_layer, dst, src)
        self.win = egl.NativeWindow(element, w, h)
        egl.bcm_update_submit_sync(update)

    def _create_egl_context(self, win, flags):
        api = egl._constants.EGL_OPENGL_ES_API
        c = egl._constants

        attribs = [
            c.EGL_RED_SIZE, 8,
            c.EGL_GREEN_SIZE, 8,
            c.EGL_BLUE_SIZE, 8,
            c.EGL_ALPHA_SIZE, 8,
            c.EGL_DEPTH_SIZE, 16,
            c.EGL_STENCIL_SIZE, 8,
            c.EGL_SURFACE_TYPE, c.EGL_WINDOW_BIT,
            c.EGL_NONE]

        attribs_context = [c.EGL_CONTEXT_CLIENT_VERSION, 2, c.EGL_NONE]

        display = egl.GetDisplay(c.EGL_DEFAULT_DISPLAY)
        egl.Initialise(display)
        egl.BindAPI(c.EGL_OPENGL_ES_API)
        egl.GetConfigs(display)
        config = egl.ChooseConfig(display, attribs, 1)[0]
        surface = egl.CreateWindowSurface(display, config, win)
        context = egl.CreateContext(display, config, None, attribs_context)
        egl.MakeCurrent(display, surface, surface, context)

        self.egl_info = (display, surface, context)
        egl.MakeCurrent(display, surface, surface, context)

    def close(self):
        egl.Terminate(self.egl_info[0])

    def flip(self):
        if not EventLoop.quit:
            egl.SwapBuffers(self.egl_info[0], self.egl_info[1])

    def _mainloop(self):
        EventLoop.idle()

    def mainloop(self):
        while not EventLoop.quit and EventLoop.status == 'started':
            try:
                self._mainloop()
            except BaseException as inst:
                # use exception manager first
                r = ExceptionManager.handle_exception(inst)
                if r == ExceptionManager.RAISE:
                    stopTouchApp()
                    raise
                else:
                    pass
