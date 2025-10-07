import ctypes

from .. import accessibility

include "../../../kivy/lib/sdl3.pxi"
include "../../include/config.pxi"

from libc.string cimport memcpy
from os import environ
from kivy.config import Config
from kivy.logger import Logger
from kivy import platform
from kivy import setupconfig
from kivy.graphics.cgl cimport *
from kivy.graphics.egl_backend.egl_angle cimport EGLANGLE

from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free

if not environ.get('KIVY_DOC_INCLUDE'):
    is_desktop = Config.get('kivy', 'desktop') == '1'

from .window_info cimport (
    WindowInfoiOS,
    WindowInfomacOS,
    WindowInfoX11,
    WindowInfoWayland,
    WindowInfoWindows,
    WindowInfoAndroid
)

cdef int _event_filter(void *userdata, SDL_Event *event) with gil:
    return (<_WindowSDL3Storage>userdata).cb_event_filter(event)


cdef class _WindowSDL3Storage:
    cdef SDL_Window *win
    cdef SDL_GLContext ctx
    cdef SDL_Surface *surface
    cdef SDL_Surface *icon
    cdef SDL_Surface *shape_surface
    cdef char * _shape_image_pixels
    cdef int win_flags
    cdef object event_filter
    cdef object accessibility
    cdef str gl_backend_name
    cdef int sdl_manages_egl_context
    cdef EGLANGLE egl_angle_storage
    cdef bint _is_shapable
    cdef bint _first_swap_done

    def __cinit__(self):
        self.win = NULL
        self.ctx = NULL
        self.surface = NULL
        self.shape_surface = NULL
        self._shape_image_pixels = NULL
        self.win_flags = 0
        self.event_filter = None
        self.gl_backend_name = None
        self.egl_angle_storage = None
        self._is_shapable = False
        self._first_swap_done = False

    def set_event_filter(self, event_filter):
        self.event_filter = event_filter

    cdef int cb_event_filter(self, SDL_Event *event):
        # must return 0 to eat the event, 1 to add it into the event queue
        cdef str name = None
        if not self.event_filter:
            return 1
        if is_desktop and event.type == SDL_EVENT_WINDOW_RESIZED:
            action = ('windowresized',
                        event.window.data1, event.window.data2)
            return self.event_filter(*action)
        elif event.type == SDL_EVENT_TERMINATING:
            name = 'app_terminating'
        elif event.type == SDL_EVENT_LOW_MEMORY:
            name = 'app_lowmemory'
        elif event.type == SDL_EVENT_WILL_ENTER_BACKGROUND:
            name = 'app_willenterbackground'
        elif event.type == SDL_EVENT_DID_ENTER_BACKGROUND:
            name = 'app_didenterbackground'
        elif event.type == SDL_EVENT_WILL_ENTER_FOREGROUND:
            name = 'app_willenterforeground'
        elif event.type == SDL_EVENT_DID_ENTER_FOREGROUND:
            name = 'app_didenterforeground'
        if not name:
            return 1
        return self.event_filter(name)

    def die(self):
        raise RuntimeError(<bytes> SDL_GetError())

    cdef SDL_Window * _setup_sdl_window(self, width, height, multisamples, shaped):
        cdef SDL_Window *win
        cdef int _win_flags = self.win_flags

        if multisamples:
            if self.sdl_manages_egl_context:
                SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 1)
                SDL_GL_SetAttribute(
                    SDL_GL_MULTISAMPLESAMPLES, min(multisamples, 4)
                )
            else:
                # Non-SDL GL context, so we can't set the multisample
                # attributes.
                return NULL
        else:
            if self.sdl_manages_egl_context:
                SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 0)
                SDL_GL_SetAttribute(SDL_GL_MULTISAMPLESAMPLES, 0)

        if shaped:
            _win_flags |= SDL_WINDOW_TRANSPARENT

        win = SDL_CreateWindow(NULL, width, height, _win_flags)

        return win

    cdef _create_egl_context(self):

        cdef void *native_layer

        if self.gl_backend_name == "mock":
            return

        if self.sdl_manages_egl_context:
            self.ctx = SDL_GL_CreateContext(self.win)
            if not self.ctx:
                self.die()
            return

        if self.gl_backend_name == "angle":

            if platform in ("macosx", "ios"):
                native_layer = SDL_Metal_GetLayer(SDL_Metal_CreateView(self.win))
            else:
                Logger.error("WindowSDL: ANGLE is only supported on iOS and macOS")
                self.die()

            self.egl_angle_storage = EGLANGLE()
            self.egl_angle_storage.set_native_layer(native_layer)
            self.egl_angle_storage.create_context()

    cdef _destroy_egl_context(self):

        if self.gl_backend_name == "mock":
            return

        if self.sdl_manages_egl_context:
            if self.ctx != NULL:
                SDL_GL_DestroyContext(self.ctx)
            return

        if self.gl_backend_name == "angle":
            self.egl_angle_storage.destroy_context()
            return

    def _set_sdl_gl_common_attributes(self):
        SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
        SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 16)
        SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_RED_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_BLUE_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_GREEN_SIZE, 8)

        config_alpha_size = Config.getint('graphics', 'alpha_size')
        SDL_GL_SetAttribute(SDL_GL_ALPHA_SIZE, config_alpha_size)

        SDL_GL_SetAttribute(SDL_GL_RETAINED_BACKING, 0)
        SDL_GL_SetAttribute(SDL_GL_ACCELERATED_VISUAL, 1)

        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 2)
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 0)

        if self.gl_backend_name == "angle_sdl3":
            Logger.info("Window: Activate GLES2/ANGLE context")
            SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, 4)
            SDL_SetHint(SDL_HINT_VIDEO_WIN_D3DCOMPILER, "none")

    def setup_window(self, x, y, width, height, borderless, fullscreen, resizable, state, gl_backend, accessibility):
        self.gl_backend_name = gl_backend
        self.sdl_manages_egl_context = gl_backend not in ("mock", "angle")

        # Reset _is_shapable value, if the user requested a shaped window,
        # and we have the capability to create one, we will set it later.
        self._is_shapable = False

        # Always create a hidden window first, then show it after the
        # window is fully initialized, so we can make changes to the
        # window without the user seeing them.
        self.win_flags  = SDL_WINDOW_HIDDEN | SDL_WINDOW_HIGH_PIXEL_DENSITY

        if self.sdl_manages_egl_context:
            self.win_flags |= SDL_WINDOW_OPENGL

        if not self.sdl_manages_egl_context and platform in ("macosx", "ios"):
            self.win_flags |= SDL_WINDOW_METAL

        if resizable:
            self.win_flags |= SDL_WINDOW_RESIZABLE

        if not USE_IOS:
            if borderless:
                self.win_flags |= SDL_WINDOW_BORDERLESS

        if USE_ANDROID:
            # Android is handled separately because it is important to create the window with
            # the same fullscreen setting as AndroidManifest.xml.
            if environ.get('P4A_IS_WINDOWED', 'True') == 'False':
                self.win_flags |= SDL_WINDOW_FULLSCREEN
        elif USE_IOS:
            if environ.get('IOS_IS_WINDOWED', 'True') == 'False':
                self.win_flags |= SDL_WINDOW_FULLSCREEN | SDL_WINDOW_BORDERLESS
        elif fullscreen is True:
            self.win_flags |= SDL_WINDOW_FULLSCREEN
        if state == 'maximized':
            self.win_flags |= SDL_WINDOW_MAXIMIZED
        elif state == 'minimized':
            self.win_flags |= SDL_WINDOW_MINIMIZED
        elif state == 'hidden':
            self.win_flags |= SDL_WINDOW_HIDDEN

        show_taskbar_icon = Config.getboolean('graphics', 'show_taskbar_icon')
        if not show_taskbar_icon:
            self.win_flags |= SDL_WINDOW_UTILITY

        SDL_SetHintWithPriority(b'SDL_ANDROID_TRAP_BACK_BUTTON', b'1',
                                SDL_HINT_OVERRIDE)

        if SDL_Init(SDL_INIT_VIDEO | SDL_INIT_JOYSTICK) < 0:
            self.die()

        # Set default orientation (force landscape for now)
        orientations = 'LandscapeLeft LandscapeRight'

        # Set larger set of iOS default orientations if applicable
        if USE_IOS:
            orientations = 'LandscapeLeft LandscapeRight Portrait PortraitUpsideDown'

        if USE_ANDROID:
            # Do not hint anything: by default the value in the AndroidManifest.xml will be used
            # Note that the user can still override this via $KIVY_ORIENTATION if they wish
            orientations = ''

        # Override the orientation based on the KIVY_ORIENTATION env
        # var. Note that this takes priority over any other setting.
        orientations = environ.get('KIVY_ORIENTATION', orientations)

        SDL_SetHint(SDL_HINT_ORIENTATIONS, <bytes>(orientations.encode('utf-8')))

        if self.sdl_manages_egl_context:
            self._set_sdl_gl_common_attributes()

        # Multisampling:
        # (The number of samples is limited to 4, because greater values
        # aren't supported with some video drivers.)
        cdef int config_multisamples, config_shaped
        config_multisamples = Config.getint('graphics', 'multisamples')

        # we need to tell the window to be shaped before creation, therefore
        # it's a config property like e.g. fullscreen
        config_shaped = Config.getint('graphics', 'shaped')

        # Due to the uncertainty regarding the window's capability for shaping 
        # and multisampling, we iterate through all possible combinations in 
        # the most correct order:
        # 1. Shaped window with multisampling
        # 2. Shaped window without multisampling
        # 3. Ordinary window with multisampling
        # 4. Ordinary window without multisampling
        sdl_window_configs = []
        if config_multisamples and config_shaped:
            sdl_window_configs.append((config_multisamples, config_shaped))
        if config_shaped:
            sdl_window_configs.append((0, config_shaped))
        if config_multisamples:
            sdl_window_configs.append((config_multisamples, 0))
        sdl_window_configs.append((0, 0))

        for multisamples, shaped in sdl_window_configs:
            win = self._setup_sdl_window(width, height, multisamples, shaped)
            if win:
                self.win = win

                # Get win flags after creation, as may be different
                # from the initially requested ones.
                self.win_flags = SDL_GetWindowFlags(win)
                break

        if not self.win:
            self.die()

        cdef int w, h
        SDL_GetWindowSize(self.win, &w, &h)

        # Install the accessibility provider and show the window if necessary
        # TODO: There is currently no way to retrieve the handle of an NSWindow.
        window_info = self.get_window_info()
        if accessibility is not None:
            accessibility.install(window_info, w, h)
        IF UNAME_SYSNAME == 'Windows':
            self.show_window()

        # Set shape in case the user requested a shaped window and the window
        # have the capability to be shaped (SDL_WINDOW_TRANSPARENT flag is set)
        if config_shaped and self.win_flags & SDL_WINDOW_TRANSPARENT:
            self._is_shapable = True

        self.set_window_pos(x, y)

        self._create_egl_context()

        # vsync
        vsync = Config.get('graphics', 'vsync')
        if self.sdl_manages_egl_context and vsync and vsync != 'none':
            vsync = Config.getint('graphics', 'vsync')

            Logger.debug(f'WindowSDL: setting vsync interval=={vsync}')
            res = SDL_GL_SetSwapInterval(vsync)

            if res == -1:
                status = ''
                if vsync not in (0, 1):
                    res = SDL_GL_SetSwapInterval(1)
                    status = ', trying fallback to 1: ' + ('failed' if res == -1 else 'succeeded')

                Logger.debug('WindowSDL: requested vsync failed' + status)

        # Open all available joysticks
        cdef int joy_i
        cdef int numjoysticks
        SDL_GetJoysticks(&numjoysticks)
        for joy_i in range(numjoysticks):
            SDL_OpenJoystick(joy_i)

        SDL_SetEventFilter(<SDL_EventFilter>_event_filter, <void *>self)

        SDL_SetEventEnabled(SDL_EVENT_DROP_FILE, True)
        SDL_SetEventEnabled(SDL_EVENT_DROP_TEXT, True)
        SDL_SetEventEnabled(SDL_EVENT_DROP_BEGIN, True)
        SDL_SetEventEnabled(SDL_EVENT_DROP_COMPLETE, True)

        # At this point, the window is fully initialized, so we can show it.
        SDL_ShowWindow(self.win)

        return w, h

    def _set_cursor_state(self, value):
        if value:
            SDL_ShowCursor()
        else:
            SDL_HideCursor()

    def set_system_cursor(self, str name):
        # prevent the compiler to not be happy because of
        # an uninitialized value (return False in Cython is not a direct
        # return 0 in C)
        cdef SDL_SystemCursor num = SDL_SYSTEM_CURSOR_DEFAULT
        if name == 'arrow':
            num = SDL_SYSTEM_CURSOR_DEFAULT
        elif name == 'ibeam':
            num = SDL_SYSTEM_CURSOR_TEXT
        elif name == 'wait':
            num = SDL_SYSTEM_CURSOR_WAIT
        elif name == 'crosshair':
            num = SDL_SYSTEM_CURSOR_CROSSHAIR
        elif name == 'wait_arrow':
            num = SDL_SYSTEM_CURSOR_PROGRESS
        elif name == 'size_nwse':
            num = SDL_SYSTEM_CURSOR_NWSE_RESIZE
        elif name == 'size_nesw':
            num = SDL_SYSTEM_CURSOR_NESW_RESIZE
        elif name == 'size_we':
            num = SDL_SYSTEM_CURSOR_EW_RESIZE
        elif name == 'size_ns':
            num = SDL_SYSTEM_CURSOR_NS_RESIZE
        elif name == 'size_all':
            num = SDL_SYSTEM_CURSOR_MOVE
        elif name == 'no':
            num = SDL_SYSTEM_CURSOR_NOT_ALLOWED
        elif name == 'hand':
            num = SDL_SYSTEM_CURSOR_POINTER
        else:
            return False
        new_cursor = SDL_CreateSystemCursor(num)
        self.set_cursor(new_cursor)
        return True

    cdef void set_cursor(self, SDL_Cursor * cursor):
        SDL_SetCursor(cursor)

    def raise_window(self):
        SDL_RaiseWindow(self.win)

    def _resize_fullscreen(self, w, h):
        cdef SDL_DisplayMode* mode

        if USE_IOS or USE_ANDROID:
            # Changing the fullscreen size on iOS and Android is not supported
            # When the app switches to fullscreen, it will use the size of the
            # screen.
            return

        mode = SDL_GetWindowFullscreenMode(self.win)
        mode.w = w
        mode.h = h
        SDL_SetWindowFullscreenMode(self.win, mode)

        return mode.w, mode.h

    def _resize_windowed(self, w, h):
        SDL_SetWindowSize(self.win, w, h)

    def resize_window(self, w, h):

        if self.window_size == [w, h]:
            return

        if SDL_GetWindowFlags(self.win) & SDL_WINDOW_FULLSCREEN:
            # If the window is in fullscreen mode, we need to change the
            # size by setting the display mode
            Logger.debug(f'WindowSDL: Resize fullscreen to {w}x{h}')
            self._resize_fullscreen(w, h)
        else:
            # If the window is not in fullscreen mode, we can change the
            # size of the window directly
            Logger.debug(f'WindowSDL: Resize window to {w}x{h}')
            self._resize_windowed(w, h)

    def set_minimum_size(self, w, h):
        SDL_SetWindowMinimumSize(self.win, w, h)

    def set_always_on_top(self, always_on_top):
        SDL_SetWindowAlwaysOnTop(self.win, always_on_top)

    def set_allow_screensaver(self, allow_screensaver):
        if allow_screensaver:
            SDL_EnableScreenSaver()
        else:
            SDL_DisableScreenSaver()

    def maximize_window(self):
        SDL_MaximizeWindow(self.win)

    def minimize_window(self):
        SDL_MinimizeWindow(self.win)

    def restore_window(self):
        SDL_RestoreWindow(self.win)

    def hide_window(self):
        SDL_HideWindow(self.win)

    def show_window(self):
        SDL_ShowWindow(self.win)

    def set_border_state(self, state):
        SDL_SetWindowBordered(self.win, not state)

    def set_fullscreen_mode(self, mode):
        if mode is True:
            mode = SDL_WINDOW_FULLSCREEN
        else:
            mode = False

        SDL_SetWindowFullscreen(self.win, mode)

    def set_window_title(self, title):
        SDL_SetWindowTitle(self.win, <bytes>title.encode('utf-8'))

    def get_window_pixel_density(self):
        cdef float pixel_density
        pixel_density = SDL_GetWindowPixelDensity(self.win)
        if pixel_density == 0.0:
            pixel_density = 1.0
        return pixel_density

    def get_window_display_scale(self):
        cdef float scale
        scale = SDL_GetWindowDisplayScale(self.win)
        if scale == 0.0:
            scale = 1.0
        return scale

    def get_window_pos(self):
        cdef int x, y
        SDL_GetWindowPosition(self.win, &x, &y)
        return x, y

    def set_window_pos(self, x, y):

        if x is None:
            x = SDL_WINDOWPOS_UNDEFINED
        if y is None:
            y = SDL_WINDOWPOS_UNDEFINED

        SDL_SetWindowPosition(self.win, x, y)

    def set_window_opacity(self, opacity):
        if SDL_SetWindowOpacity(self.win, opacity):
            message = (<bytes>SDL_GetError()).decode('utf-8', 'replace')
            Logger.error(f'WindowSDL: Setting opacity to {opacity} failed - '
                         f'{message}')
            return False
        return True

    def get_window_opacity(self):
        return SDL_GetWindowOpacity(self.win)

    def _get_current_video_driver(self):
        cdef char *driver = SDL_GetCurrentVideoDriver()
        if driver is NULL:
            return None
        return driver.decode('utf-8')

    def _get_window_info_macos(self):
        cdef WindowInfomacOS window_info
        window_info = WindowInfomacOS()

        window_info.set_window(
            SDL_GetPointerProperty(
                SDL_GetWindowProperties(self.win),
                "SDL.window.cocoa.window",
                NULL,
            )
        )

        return window_info

    def _get_window_info_ios(self):
        cdef WindowInfoiOS window_info
        window_info = WindowInfoiOS()

        window_info.set_window(
            SDL_GetPointerProperty(
                SDL_GetWindowProperties(self.win),
                "SDL.window.uikit.window",
                NULL,
            )
        )

        return window_info

    def _get_window_info_wayland(self):
        cdef WindowInfoWayland window_info
        window_info = WindowInfoWayland()

        window_info.set_display(
            SDL_GetPointerProperty(
                SDL_GetWindowProperties(self.win),
                "SDL.window.wayland.display",
                NULL,
            )
        )

        window_info.set_surface(
            SDL_GetPointerProperty(
                SDL_GetWindowProperties(self.win),
                "SDL.window.wayland.surface",
                NULL,
            )
        )

        return window_info

    def _get_window_info_x11(self):
        cdef WindowInfoX11 window_info
        window_info = WindowInfoX11()

        window_info.set_display(
            SDL_GetPointerProperty(
                SDL_GetWindowProperties(self.win),
                "SDL.window.x11.display",
                NULL,
            )
        )

        window_info.set_window(
            SDL_GetNumberProperty(
                SDL_GetWindowProperties(self.win),
                "SDL.window.x11.window",
                0,
            )
        )

        return window_info

    def _get_window_info_windows(self):
        cdef WindowInfoWindows window_info
        window_info = WindowInfoWindows()

        window_info.set_hwnd(
            SDL_GetPointerProperty(
                SDL_GetWindowProperties(self.win),
                "SDL.window.win32.hwnd",
                NULL,
            )
        )
        window_info.set_hdc(
            SDL_GetPointerProperty(
                SDL_GetWindowProperties(self.win),
                "SDL.window.win32.hdc",
                NULL,
            )
        )

        return window_info

    def _get_window_info_android(self):
        cdef WindowInfoAndroid window_info
        window_info = WindowInfoAndroid()

        window_info.set_window(
            SDL_GetPointerProperty(
                SDL_GetWindowProperties(self.win),
                "SDL.window.android.window",
                NULL,
            )
        )
        window_info.set_surface(
            SDL_GetPointerProperty(
                SDL_GetWindowProperties(self.win),
                "SDL.window.android.surface",
                NULL,
            )
        )

        return window_info

    def get_window_info(self):
        if platform == "macosx":
            return self._get_window_info_macos()
        elif platform == "ios":
            return self._get_window_info_ios()
        elif platform == "win":
            return self._get_window_info_windows()
        elif platform == "linux":
            _video_driver = self._get_current_video_driver()
            if _video_driver == "wayland":
                return self._get_window_info_wayland()
            elif _video_driver == "x11":
                return self._get_window_info_x11()
        elif platform == "android":
            return self._get_window_info_android()
        return None

    def get_native_handle(self):
        window_info = self.get_window_info()
        if window_info is None:
            return None
        
        return window_info.native_handle

    def is_window_shapable(self):
        return self._is_shapable

    @staticmethod
    cdef SDL_PixelFormat _get_pixel_format_from_image(image):
        cdef SDL_PixelFormat _format

        if image.texture.colorfmt == 'rgba':
            _format = SDL_GetPixelFormatForMasks(32, 0xff000000, 0x00ff0000, 0x0000ff00, 0x000000ff)
        elif image.texture.colorfmt == 'rgb':
            _format = SDL_GetPixelFormatForMasks(24, 0xff0000, 0x00ff00, 0x0000ff, 0)
        else:
            raise ValueError('Unsupported color format')

        return _format

    @staticmethod
    cdef int _get_pitch_from_image(image):
        cdef int _pitch

        if image.texture.colorfmt == 'rgba':
            _pitch = image.width * 4
        elif image.texture.colorfmt == 'rgb':
            _pitch = image.width * 3
        else:
            raise ValueError('Unsupported color format')

        return _pitch

    cpdef set_shape(self, shape_image):
        cdef char* error = NULL
        cdef SDL_PixelFormat _format
        cdef int _pitch

        if self.shape_surface != NULL:
            SDL_DestroySurface(self.shape_surface)
        
        if self._shape_image_pixels != NULL:
            free(self._shape_image_pixels)

        _format = _WindowSDL3Storage._get_pixel_format_from_image(shape_image)
        _pitch = _WindowSDL3Storage._get_pitch_from_image(shape_image)

        self._shape_image_pixels = <char *> malloc(_pitch * shape_image.height)
        memcpy(self._shape_image_pixels, <char *>shape_image.texture.pixels, _pitch * shape_image.height)
        

        self.shape_surface = SDL_CreateSurfaceFrom(
            shape_image.width,
            shape_image.height,
            _format,
            <char *>self._shape_image_pixels,
            _pitch,
        )
            
        if SDL_SetWindowShape(self.win, self.shape_surface) is False:
            error = SDL_GetError()
            Logger.error(
                'Window: Setting shape failed: %s' % error
            )
            return

    # twb end

    def set_window_icon(self, filename):
        icon = IMG_Load(<bytes>filename.encode('utf-8'))
        SDL_SetWindowIcon(self.win, icon)

    def teardown_window(self):
        self._destroy_egl_context()

        SDL_DestroyWindow(self.win)
        SDL_Quit()

    def show_keyboard(
        self,
        system_keyboard,
        softinput_mode,
        input_type,
        keyboard_suggestions=True,
    ):
        if SDL_TextInputActive(self.win):
            return
        cdef SDL_Rect *rect = <SDL_Rect *>PyMem_Malloc(sizeof(SDL_Rect))
        if not rect:
            raise MemoryError('Memory error in rect allocation')
        try:
            if platform == 'android':
                # This could probably be safely done on every platform
                # (and should behave correctly with e.g. the windows
                # software keyboard), but this hasn't been tested

                wx, wy = self.window_size

                # Note Android's coordinate system has y=0 at the top
                # of the screen

                if softinput_mode == 'below_target':
                    target = system_keyboard.target
                    rect.y = max(
                        0, wy - target.to_window(0, target.top)[1]
                    ) if target else 0
                    rect.x = max(
                        0, target.to_window(target.x, 0)[0]
                    ) if target else 0
                    rect.w = max(0, target.width) if target else 0
                    rect.h = max(0, target.height) if target else 0
                    SDL_SetTextInputArea(self.win, rect, 0)
                elif softinput_mode == 'pan':
                    # tell Android the TextInput is at the screen
                    # bottom, so that it always pans
                    rect.y = wy - 5
                    rect.x = 0
                    rect.w = wx
                    rect.h = 5
                    SDL_SetTextInputArea(self.win, rect, 0)
                else:
                    # Supporting 'resize' needs to call the Android
                    # API to set ADJUST_RESIZE mode, and change the
                    # java bootstrap to a different root Layout.
                    rect.y = 0
                    rect.x = 0
                    rect.w = 10
                    rect.h = 1
                    SDL_SetTextInputArea(self.win, rect, 0)

                """
                Android input type selection.
                Based on input_type and keyboard_suggestions arguments, set the
                keyboard type to be shown. Note that text suggestions will only
                work when input_type is "text" or a text variation.
                """

                from android import mActivity

                # InputType definitions, from Android documentation

                TYPE_CLASS_DATETIME = 4
                TYPE_CLASS_NUMBER = 2
                TYPE_CLASS_PHONE = 3
                TYPE_CLASS_TEXT = 1
                TYPE_CLASS_NULL = 0

                TYPE_TEXT_VARIATION_EMAIL_ADDRESS = 32
                TYPE_TEXT_VARIATION_URI = 16
                TYPE_TEXT_VARIATION_POSTAL_ADDRESS = 112

                TYPE_TEXT_FLAG_NO_SUGGESTIONS = 524288

                input_type_value = {
                                "null": TYPE_CLASS_NULL,
                                "text": TYPE_CLASS_TEXT,
                                "number": TYPE_CLASS_NUMBER,
                                "url":
                                TYPE_CLASS_TEXT |
                                TYPE_TEXT_VARIATION_URI,
                                "mail":
                                TYPE_CLASS_TEXT |
                                TYPE_TEXT_VARIATION_EMAIL_ADDRESS,
                                "datetime": TYPE_CLASS_DATETIME,
                                "tel": TYPE_CLASS_PHONE,
                                "address":
                                TYPE_CLASS_TEXT |
                                TYPE_TEXT_VARIATION_POSTAL_ADDRESS
                              }.get(input_type, TYPE_CLASS_TEXT)

                text_keyboards = {"text", "url", "mail", "address"}

                if not keyboard_suggestions and input_type in text_keyboards:
                    """
                    Looks like some (major) device vendors and keyboards are de-facto ignoring this flag,
                    so we can't really rely on this one to disable suggestions.
                    """
                    input_type_value |= TYPE_TEXT_FLAG_NO_SUGGESTIONS

                mActivity.changeKeyboard(input_type_value)

            SDL_StartTextInput(self.win)
        finally:
            PyMem_Free(<void *>rect)

    def hide_keyboard(self):
        if SDL_TextInputActive(self.win):
            SDL_StopTextInput(self.win)

    def is_keyboard_shown(self):
        return SDL_TextInputActive(self.win)

    def get_current_key_modifiers(self):
        return SDL_GetModState()

    def wait_event(self):
        with nogil:
            SDL_WaitEvent(NULL)

    def poll(self):
        cdef SDL_Event event
        cdef int rv
        with nogil:
            rv = SDL_PollEvent(&event)
        if rv == 0:
            return False
        action = None
        if event.type == SDL_EVENT_QUIT:
            return ('quit', )
        elif event.type == SDL_EVENT_MOUSE_MOTION:
            x = event.motion.x
            y = event.motion.y
            return ('mousemotion', x, y)
        elif event.type == SDL_EVENT_MOUSE_BUTTON_DOWN or event.type == SDL_EVENT_MOUSE_BUTTON_UP:
            x = event.button.x
            y = event.button.y
            button = event.button.button
            action = 'mousebuttondown' if event.type == SDL_EVENT_MOUSE_BUTTON_DOWN else 'mousebuttonup'
            return (action, x, y, button)
        elif event.type == SDL_EVENT_MOUSE_WHEEL:
            x = event.wheel.x
            y = event.wheel.y
            # TODO we should probably support events with both an x and y offset
            if x != 0:
                suffix = 'left' if x > 0 else 'right'
            elif y != 0:
                suffix = 'down' if y > 0 else 'up'
            else:
                # It's possible to get mouse wheel events with no offset in
                # either x or y direction, we just ignore them
                # https://wiki.libsdl.org/SDL_MouseWheelEvent
                return None
            action = 'mousewheel' + suffix
            return (action, x, y, None)
        elif event.type == SDL_EVENT_FINGER_MOTION:
            fid = event.tfinger.fingerID
            x = event.tfinger.x
            y = event.tfinger.y
            pressure = event.tfinger.pressure
            return ('fingermotion', fid, x, y, pressure)
        elif event.type == SDL_EVENT_FINGER_DOWN or event.type == SDL_EVENT_FINGER_UP:
            fid = event.tfinger.fingerID
            x = event.tfinger.x
            y = event.tfinger.y
            pressure = event.tfinger.pressure
            action = 'fingerdown' if event.type == SDL_EVENT_FINGER_DOWN else 'fingerup'
            return (action, fid, x, y, pressure)
        elif event.type == SDL_EVENT_JOYSTICK_AXIS_MOTION:
            return (
                'joyaxismotion',
                event.jaxis.which, event.jaxis.axis, event.jaxis.value
            )
        elif event.type == SDL_EVENT_JOYSTICK_HAT_MOTION:
            vx = 0
            vy = 0
            if (event.jhat.value != SDL_HAT_CENTERED):
                if (event.jhat.value & SDL_HAT_UP):
                    vy = 1
                elif (event.jhat.value & SDL_HAT_DOWN):
                    vy = -1
                if (event.jhat.value & SDL_HAT_RIGHT):
                    vx = 1
                elif (event.jhat.value & SDL_HAT_LEFT):
                    vx = -1
            return ('joyhatmotion', event.jhat.which, event.jhat.hat, (vx, vy))
        elif event.type == SDL_EVENT_JOYSTICK_BALL_MOTION:
            return (
                'joyballmotion',
                event.jball.which, event.jball.ball,
                event.jball.xrel, event.jball.yrel
            )
        elif event.type == SDL_EVENT_JOYSTICK_BUTTON_DOWN:
            return ('joybuttondown', event.jbutton.which, event.jbutton.button)
        elif event.type == SDL_EVENT_JOYSTICK_BUTTON_UP:
            return ('joybuttonup', event.jbutton.which, event.jbutton.button)
        elif event.type >= SDL_EVENT_WINDOW_FIRST and event.type <= SDL_EVENT_WINDOW_LAST:
            if event.type == SDL_EVENT_WINDOW_EXPOSED:
                action = ('windowexposed', )
            elif event.type == SDL_EVENT_WINDOW_RESIZED:
                action = (
                    'windowresized',
                    event.window.data1, event.window.data2
                )
            elif event.type == SDL_EVENT_WINDOW_MINIMIZED:
                action = ('windowminimized', )
            elif event.type == SDL_EVENT_WINDOW_MAXIMIZED:
                action = ('windowmaximized', )
            elif event.type == SDL_EVENT_WINDOW_RESTORED:
                action = ('windowrestored', )
            elif event.type == SDL_EVENT_WINDOW_SHOWN:
                action = ('windowshown', )
            elif event.type == SDL_EVENT_WINDOW_HIDDEN:
                action = ('windowhidden', )
            elif event.type == SDL_EVENT_WINDOW_MOUSE_ENTER:
                action = ('windowenter', )
            elif event.type == SDL_EVENT_WINDOW_MOUSE_LEAVE:
                action = ('windowleave', )
            elif event.type == SDL_EVENT_WINDOW_FOCUS_GAINED:
                action = ('windowfocusgained', )
            elif event.type == SDL_EVENT_WINDOW_FOCUS_LOST:
                action = ('windowfocuslost', )
            elif event.type == SDL_EVENT_WINDOW_CLOSE_REQUESTED:
                action = ('windowclose', )
            elif event.type == SDL_EVENT_WINDOW_MOVED:
                action = (
                    'windowmoved',
                    event.window.data1, event.window.data2
                )
            elif event.type == SDL_EVENT_WINDOW_DISPLAY_CHANGED:
                action = ('windowdisplaychanged', event.window.data1)
            elif event.type == SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED:
                action = ('windowpixelsizechanged',)
            elif event.type == SDL_EVENT_WINDOW_DISPLAY_SCALE_CHANGED:
                action = (
                    'windowdisplayscalechanged',
                    event.window.data1, event.window.data2
                )
            else:
                #    print('receive unknown sdl window event', event.type)
                pass
            return action
        elif event.type == SDL_EVENT_KEY_DOWN or event.type == SDL_EVENT_KEY_UP:
            action = 'keydown' if event.type == SDL_EVENT_KEY_DOWN else 'keyup'
            mod = event.key.mod
            scancode = event.key.scancode
            key = event.key.key
            return (action, mod, key, scancode, None)
        elif event.type == SDL_EVENT_TEXT_INPUT:
            s = event.text.text.decode('utf-8')
            return ('textinput', s)
        elif event.type == SDL_EVENT_TEXT_EDITING:
            s = event.edit.text.decode('utf-8')
            return ('textedit', s)
        elif event.type == SDL_EVENT_DROP_FILE:
            # return ('dropfile', event.drop.file)
            pass
        elif event.type == SDL_EVENT_DROP_TEXT:
            # return ('droptext', event.drop.file)
            pass
        elif event.type == SDL_EVENT_DROP_BEGIN:
            return ('dropbegin',)
        elif event.type == SDL_EVENT_DROP_COMPLETE:
            return ('dropend',)
        else:
            #    print('receive unknown sdl window event', event.type)
            pass

    def flip(self):
        # On Android (and potentially other platforms), SDL_GL_SwapWindow may
        # lock the thread waiting for a mutex from another thread to be
        # released. Calling SDL_GL_SwapWindow with the GIL released allow the
        # other thread to run (e.g. to process the event filter callback) and
        # release the mutex SDL_GL_SwapWindow is waiting for.
        if self.sdl_manages_egl_context:
            with nogil:
                SDL_GL_SwapWindow(self.win)
        else:
            self.egl_angle_storage.swap_buffers()

        # Trigger ready event after first successful swap
        if not self._first_swap_done:
            self._first_swap_done = True
            # Get the running app instance and trigger ready
            from kivy.app import App
            if App.get_running_app() is not None:
                App.get_running_app()._trigger_ready_once()

    def save_bytes_in_png(self, filename, data, int width, int height):
        cdef SDL_Surface *surface = SDL_CreateSurfaceFrom(
            width,
            height,
            SDL_GetPixelFormatForMasks(width * 3, 0x0000ff, 0x00ff00, 0xff0000, 0),
            <char *>data,
            24
        )
        cdef bytes bytes_filename = <bytes>filename.encode('utf-8')
        cdef char *real_filename = <char *>bytes_filename

        cdef SDL_Surface *flipped_surface = flipVert(surface)
        IMG_SavePNG(flipped_surface, real_filename)
        SDL_DestroySurface(surface)
        SDL_DestroySurface(flipped_surface)

    def grab_mouse(self, grab):
        SDL_SetWindowMouseGrab(self.win, grab)

    def get_relative_mouse_pos(self):
        cdef float x, y
        SDL_GetGlobalMouseState(&x, &y)
        wx, wy = self.get_window_pos()
        return x - wx, y - wy

    def set_custom_titlebar(self, titlebar_widget):
        SDL_SetWindowBordered(self.win, False)
        return SDL_SetWindowHitTest(self.win, <SDL_HitTest>custom_titlebar_handler_callback,<void *>titlebar_widget)

    @property
    def window_size(self):
        cdef int w, h
        SDL_GetWindowSize(self.win, &w, &h)
        return [w, h]

    cpdef str get_system_theme(self):
        cdef SDL_SystemTheme current_theme
        cdef str result

        with nogil:
            current_theme = SDL_GetSystemTheme()

        if current_theme == SDL_SYSTEM_THEME_LIGHT:
            result = "light"
        elif current_theme == SDL_SYSTEM_THEME_DARK:
            result = "dark"
        else:
            # SDL_SYSTEM_THEME_UNKNOWN or any unexpected value
            result = "unknown"

        return result

    @property
    def window_pixel_size(self):
        """
        The window size in pixels may differ from window size
        returned by SDL_GetWindowSize as it returns the size in
        window coordinates, which may be different from the size
        in pixels if the window is on a high-DPI display.
        """
        cdef int w, h
        SDL_GetWindowSizeInPixels(self.win, &w, &h)
        return w, h


cdef SDL_HitTestResult custom_titlebar_handler_callback(SDL_Window* win, const SDL_Point* pts, void* data) with gil:

    cdef int border = max(
        Config.getdefaultint('graphics','custom_titlebar_border',5),
        Config.getint('graphics', 'custom_titlebar_border')
    ) # pixels
    cdef int w, h
    SDL_GetWindowSize(<SDL_Window *> win, &w, &h)
    # shift y origin in widget as sdl origin is in top-left
    if Config.getboolean('graphics', 'resizable'):
        if pts.x < border and pts.y < border:
            return SDL_HITTEST_RESIZE_TOPLEFT
        elif pts.x < border < h - pts.y:
            return SDL_HITTEST_RESIZE_LEFT
        elif pts.x < border and h - pts.y < border:
            return SDL_HITTEST_RESIZE_BOTTOMLEFT
        elif w - pts.x < border > pts.y:
            return SDL_HITTEST_RESIZE_TOPRIGHT
        elif w - pts.x  > border > pts.y:
            return SDL_HITTEST_RESIZE_TOP
        elif w - pts.x  < border < h - pts.y:
            return SDL_HITTEST_RESIZE_RIGHT
        elif w - pts.x  < border > h - pts.y:
            return SDL_HITTEST_RESIZE_BOTTOMRIGHT
        elif w - pts.x  > border > h - pts.y:
            return SDL_HITTEST_RESIZE_BOTTOM
    widget = <object> data
    if widget.collide_point(pts.x, h - pts.y):
        in_drag_area = getattr(widget, 'in_drag_area', None)
        if callable(in_drag_area):
            if in_drag_area(pts.x, h - pts.y):
                return SDL_HITTEST_DRAGGABLE
            else:
                return SDL_HitTestResult.SDL_HITTEST_NORMAL
        for child in widget.walk():
            drag = getattr(child, 'draggable', None)
            if drag is not None and not drag and child.collide_point(pts.x, h - pts.y):
                return SDL_HitTestResult.SDL_HITTEST_NORMAL
        return SDL_HITTEST_DRAGGABLE


    return SDL_HitTestResult.SDL_HITTEST_NORMAL
# Based on the example at
# http://content.gpwiki.org/index.php/OpenGL:Tutorials:Taking_a_Screenshot


cdef SDL_Surface* flipVert(SDL_Surface* sfc):
    cdef SDL_PixelFormatDetails* sfc_fmt = SDL_GetPixelFormatDetails(sfc.format)
    cdef SDL_Surface* result = SDL_CreateSurface(sfc.w, sfc.h,
            SDL_GetPixelFormatForMasks(
                sfc_fmt.bytes_per_pixel * 8,
                sfc_fmt.Rmask,
                sfc_fmt.Gmask,
                sfc_fmt.Bmask,
                sfc_fmt.Amask
            )
    )

    cdef Uint8* pixels = <Uint8*>sfc.pixels
    cdef Uint8* rpixels = <Uint8*>result.pixels

    cdef tuple output = (
        <int>sfc.w, <int>sfc.h,
        <int>sfc_fmt.bytes_per_pixel,
        <int>sfc.pitch
    )
    Logger.debug("Window: Screenshot output dimensions {output}")

    cdef Uint32 pitch = sfc.pitch
    cdef Uint32 pxlength = pitch * sfc.h

    cdef Uint32 pos

    cdef int line
    for line in range(sfc.h):
        pos = line * pitch
        memcpy(&rpixels[pos], &pixels[(pxlength - pos) - pitch], pitch)

    return result