import ctypes

include "../../../kivy/lib/sdl2.pxi"
include "../../include/config.pxi"

from libc.string cimport memcpy
from os import environ
from kivy.config import Config
from kivy.logger import Logger
from kivy import platform
from kivy.graphics.cgl cimport *

from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free

if not environ.get('KIVY_DOC_INCLUDE'):
    is_desktop = Config.get('kivy', 'desktop') == '1'

IF USE_WAYLAND:
    from .window_info cimport WindowInfoWayland

IF USE_X11:
    from .window_info cimport WindowInfoX11

IF UNAME_SYSNAME == 'Windows':
    from .window_info cimport WindowInfoWindows

cdef int _event_filter(void *userdata, SDL_Event *event) with gil:
    return (<_WindowSDL2Storage>userdata).cb_event_filter(event)


cdef class _WindowSDL2Storage:
    cdef SDL_Window *win
    cdef SDL_GLContext ctx
    cdef SDL_Surface *surface
    cdef SDL_Surface *icon
    cdef int win_flags
    cdef object event_filter

    def __cinit__(self):
        self.win = NULL
        self.ctx = NULL
        self.surface = NULL
        self.win_flags = 0
        self.event_filter = None

    def set_event_filter(self, event_filter):
        self.event_filter = event_filter

    cdef int cb_event_filter(self, SDL_Event *event):
        # must return 0 to eat the event, 1 to add it into the event queue
        cdef str name = None
        if not self.event_filter:
            return 1
        if event.type == SDL_WINDOWEVENT:
            if is_desktop and event.window.event == SDL_WINDOWEVENT_RESIZED:
                action = ('windowresized',
                          event.window.data1, event.window.data2)
                return self.event_filter(*action)
        elif event.type == SDL_APP_TERMINATING:
            name = 'app_terminating'
        elif event.type == SDL_APP_LOWMEMORY:
            name = 'app_lowmemory'
        elif event.type == SDL_APP_WILLENTERBACKGROUND:
            name = 'app_willenterbackground'
        elif event.type == SDL_APP_DIDENTERBACKGROUND:
            name = 'app_didenterbackground'
        elif event.type == SDL_APP_WILLENTERFOREGROUND:
            name = 'app_willenterforeground'
        elif event.type == SDL_APP_DIDENTERFOREGROUND:
            name = 'app_didenterforeground'
        if not name:
            return 1
        return self.event_filter(name)

    def die(self):
        raise RuntimeError(<bytes> SDL_GetError())

    def setup_window(self, x, y, width, height, borderless, fullscreen,
                     resizable, state, gl_backend):
        self.win_flags = SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN | SDL_WINDOW_ALLOW_HIGHDPI

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
        elif fullscreen == 'auto':
            self.win_flags |= SDL_WINDOW_FULLSCREEN_DESKTOP
        elif fullscreen is True:
            self.win_flags |= SDL_WINDOW_FULLSCREEN
        if state == 'maximized':
            self.win_flags |= SDL_WINDOW_MAXIMIZED
        elif state == 'minimized':
            self.win_flags |= SDL_WINDOW_MINIMIZED
        elif state == 'hidden':
            self.win_flags |= SDL_WINDOW_HIDDEN

        SDL_SetHint(SDL_HINT_ACCELEROMETER_AS_JOYSTICK, b'0')

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

        SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
        SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 16)
        SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_RED_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_BLUE_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_GREEN_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_ALPHA_SIZE, KIVY_SDL_GL_ALPHA_SIZE)
        SDL_GL_SetAttribute(SDL_GL_RETAINED_BACKING, 0)
        SDL_GL_SetAttribute(SDL_GL_ACCELERATED_VISUAL, 1)

        if gl_backend == "angle_sdl2":
            Logger.info("Window: Activate GLES2/ANGLE context")
            SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, 4)
            SDL_SetHint(SDL_HINT_VIDEO_WIN_D3DCOMPILER, "none")

        if x is None:
            x = SDL_WINDOWPOS_UNDEFINED
        if y is None:
            y = SDL_WINDOWPOS_UNDEFINED

        # Multisampling:
        # (The number of samples is limited to 4, because greater values
        # aren't supported with some video drivers.)
        cdef int multisamples, shaped
        multisamples = Config.getint('graphics', 'multisamples')

        # we need to tell the window to be shaped before creation, therefore
        # it's a config property like e.g. fullscreen
        shaped = Config.getint('graphics', 'shaped')

        if multisamples > 0 and shaped > 0:
            # try to create shaped window with multisampling:
            SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 1)
            SDL_GL_SetAttribute(
                SDL_GL_MULTISAMPLESAMPLES, min(multisamples, 4)
            )
            self.win = SDL_CreateShapedWindow(
                NULL, x, y, width, height, self.win_flags
            )
            if not self.win:
                # if an error occurred, create only shaped window:
                SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 0)
                SDL_GL_SetAttribute(SDL_GL_MULTISAMPLESAMPLES, 0)
                self.win = SDL_CreateShapedWindow(
                    NULL, x, y, width, height, self.win_flags
                )
            if not self.win:
                # if everything fails, create an ordinary window:
                self.win = SDL_CreateWindow(
                    NULL, x, y, width, height, self.win_flags
                )
        elif multisamples > 0:
            # try to create window with multisampling:
            SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 1)
            SDL_GL_SetAttribute(
                SDL_GL_MULTISAMPLESAMPLES, min(multisamples, 4)
            )
            self.win = SDL_CreateWindow(
                NULL, x, y, width, height, self.win_flags
            )
            if not self.win:
                # if an error occurred, create window without multisampling:
                SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 0)
                SDL_GL_SetAttribute(SDL_GL_MULTISAMPLESAMPLES, 0)
                self.win = SDL_CreateWindow(
                    NULL, x, y, width, height, self.win_flags
                )
        elif shaped > 0:
            # try to create shaped window:
            self.win = SDL_CreateShapedWindow(
                NULL, x, y, width, height, self.win_flags
            )
            if not self.win:
                # if an error occurred, create an ordinary window:
                self.win = SDL_CreateWindow(
                    NULL, x, y, width, height, self.win_flags
                )
        else:
            self.win = SDL_CreateWindow(
                NULL, x, y, width, height, self.win_flags
            )

        # post-creation fix for shaped window
        if shaped > 0 and self.is_window_shaped():
            # because SDL just set it to (-1000, -1000)
            # -> can't use UNDEFINED nor CENTER after window creation
            self.set_window_pos(100, 100)

            # SDL also changed borderless, fullscreen, resizable and shown
            # but we shouldn't care about those at __init__ as this window is
            # a special one (borders and resizing will cripple the look,
            # fullscreen might crash the window)

        if not self.win:
            self.die()

        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 2)
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 0)

        if gl_backend != "mock":
            self.ctx = SDL_GL_CreateContext(self.win)
            if not self.ctx:
                self.die()

        # vsync
        vsync = Config.get('graphics', 'vsync')
        if vsync and vsync != 'none':
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
        for joy_i in range(SDL_NumJoysticks()):
            SDL_JoystickOpen(joy_i)

        SDL_SetEventFilter(_event_filter, <void *>self)

        SDL_EventState(SDL_DROPFILE, SDL_ENABLE)
        SDL_EventState(SDL_DROPTEXT, SDL_ENABLE)
        SDL_EventState(SDL_DROPBEGIN, SDL_ENABLE)
        SDL_EventState(SDL_DROPCOMPLETE, SDL_ENABLE)
        cdef int w, h
        SDL_GetWindowSize(self.win, &w, &h)
        return w, h

    def _set_cursor_state(self, value):
        SDL_ShowCursor(value)

    def set_system_cursor(self, str name):
        # prevent the compiler to not be happy because of
        # an uninitialized value (return False in Cython is not a direct
        # return 0 in C)
        cdef SDL_SystemCursor num = SDL_SYSTEM_CURSOR_ARROW
        if name == 'arrow':
            num = SDL_SYSTEM_CURSOR_ARROW
        elif name == 'ibeam':
            num = SDL_SYSTEM_CURSOR_IBEAM
        elif name == 'wait':
            num = SDL_SYSTEM_CURSOR_WAIT
        elif name == 'crosshair':
            num = SDL_SYSTEM_CURSOR_CROSSHAIR
        elif name == 'wait_arrow':
            num = SDL_SYSTEM_CURSOR_WAITARROW
        elif name == 'size_nwse':
            num = SDL_SYSTEM_CURSOR_SIZENWSE
        elif name == 'size_nesw':
            num = SDL_SYSTEM_CURSOR_SIZENESW
        elif name == 'size_we':
            num = SDL_SYSTEM_CURSOR_SIZEWE
        elif name == 'size_ns':
            num = SDL_SYSTEM_CURSOR_SIZENS
        elif name == 'size_all':
            num = SDL_SYSTEM_CURSOR_SIZEALL
        elif name == 'no':
            num = SDL_SYSTEM_CURSOR_NO
        elif name == 'hand':
            num = SDL_SYSTEM_CURSOR_HAND
        else:
            return False
        new_cursor = SDL_CreateSystemCursor(num)
        self.set_cursor(new_cursor)
        return True

    cdef void set_cursor(self, SDL_Cursor * cursor):
        SDL_SetCursor(cursor)

    def raise_window(self):
        SDL_RaiseWindow(self.win)

    def _get_gl_size(self):
        cdef int w, h
        SDL_GL_GetDrawableSize(self.win, &w, &h)
        return w, h

    def resize_display_mode(self, w, h):
        cdef SDL_DisplayMode mode
        cdef int draw_w, draw_h
        SDL_GetWindowDisplayMode(self.win, &mode)
        if USE_IOS and self.ctx:
            SDL_GL_GetDrawableSize(self.win, &draw_w, &draw_h)
            mode.w = draw_w
            mode.h = draw_h
            SDL_SetWindowDisplayMode(self.win, &mode)
        else:
            mode.w = w
            mode.h = h
            SDL_SetWindowDisplayMode(self.win, &mode)
            SDL_GetWindowDisplayMode(self.win, &mode)

        return mode.w, mode.h

    def resize_window(self, w, h):
        if self.window_size != [w, h]:
            SDL_SetWindowSize(self.win, w, h)

    def set_minimum_size(self, w, h):
        SDL_SetWindowMinimumSize(self.win, w, h)

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
        SDL_SetWindowBordered(self.win, SDL_FALSE if state else SDL_TRUE)

    def set_fullscreen_mode(self, mode):
        if mode == 'auto':
            mode = SDL_WINDOW_FULLSCREEN_DESKTOP
        elif mode is True:
            mode = SDL_WINDOW_FULLSCREEN
        else:
            mode = False
        IF not USE_IOS:
            SDL_SetWindowFullscreen(self.win, mode)

    def set_window_title(self, title):
        SDL_SetWindowTitle(self.win, <bytes>title.encode('utf-8'))

    def get_window_pos(self):
        cdef int x, y
        SDL_GetWindowPosition(self.win, &x, &y)
        return x, y

    def set_window_pos(self, x, y):
        SDL_SetWindowPosition(self.win, x, y)

    def get_window_info(self):
        cdef SDL_SysWMinfo wm_info
        SDL_GetVersion(&wm_info.version)
        cdef SDL_bool success = SDL_GetWindowWMInfo(self.win, &wm_info)

        if not success:
            return

        IF USE_WAYLAND:
            cdef WindowInfoWayland wayland_info

            if wm_info.subsystem == SDL_SYSWM_TYPE.SDL_SYSWM_WAYLAND:
                wayland_info = WindowInfoWayland()
                wayland_info.display = wm_info.info.wl.display
                wayland_info.surface = wm_info.info.wl.surface
                wayland_info.shell_surface = wm_info.info.wl.shell_surface
                return wayland_info

        IF USE_X11:
            cdef WindowInfoX11 x11_info

            if wm_info.subsystem == SDL_SYSWM_TYPE.SDL_SYSWM_X11:
                x11_info = WindowInfoX11()
                x11_info.display = wm_info.info.x11.display
                x11_info.window = wm_info.info.x11.window
                return x11_info

        IF UNAME_SYSNAME == 'Windows':
            cdef WindowInfoWindows windows_info

            if wm_info.subsystem == SDL_SYSWM_TYPE.SDL_SYSWM_WINDOWS:
                windows_info = WindowInfoWindows()
                windows_info.window = wm_info.info.win.window
                windows_info.hdc = wm_info.info.win.hdc
                return windows_info

    # Transparent Window background
    def is_window_shaped(self):
        return SDL_IsShapedWindow(self.win)

    def set_shape(self, shape, mode, cutoff, color_key):
        cdef SDL_Surface * sdl_shape

        cpdef SDL_WindowShapeMode sdl_window_mode
        cdef SDL_WindowShapeParams parameters
        cdef SDL_Color color
        cdef int result

        parameters.binarizationCutoff = <Uint8>cutoff
        color.r = <Uint8>color_key[0]
        color.g = <Uint8>color_key[1]
        color.b = <Uint8>color_key[2]
        color.a = <Uint8>color_key[3]
        parameters.colorKey = color
        sdl_window_mode.parameters = parameters

        if mode == 'default':
            sdl_window_mode.mode = ShapeModeDefault
        elif mode == 'binalpha':
            sdl_window_mode.mode = ShapeModeBinarizeAlpha
        elif mode == 'reversebinalpha':
            sdl_window_mode.mode = ShapeModeReverseBinarizeAlpha
        elif mode == 'colorkey':
            sdl_window_mode.mode = ShapeModeColorKey

        sdl_shape = IMG_Load(<bytes>shape.encode('utf-8'))
        if not sdl_shape:
            Logger.error(
                'Window: Shape image "%s" could not be loaded!' % shape
            )

        result = SDL_SetWindowShape(self.win, sdl_shape, &sdl_window_mode)

        # SDL prevents the change with wrong input values and gives back useful
        # return values, so we pass the values to the user instead of killing
        if result == SDL_NONSHAPEABLE_WINDOW:
            Logger.error(
                'Window: Setting shape to a non-shapeable window'
            )
        elif result == SDL_INVALID_SHAPE_ARGUMENT:
            # e.g. window.size != shape_image.size
            Logger.error(
                'Window: Setting shape with an invalid shape argument'
            )
        elif result == SDL_WINDOW_LACKS_SHAPE:
            Logger.error(
                'Window: Missing shape for the window'
            )

    def get_shaped_mode(self):
        cdef SDL_WindowShapeMode mode
        SDL_GetShapedWindowMode(self.win, &mode)
        return mode
    # twb end

    def set_window_icon(self, filename):
        icon = IMG_Load(<bytes>filename.encode('utf-8'))
        SDL_SetWindowIcon(self.win, icon)

    def teardown_window(self):
        if self.ctx != NULL:
            SDL_GL_DeleteContext(self.ctx)
            self.ctx = NULL
        SDL_DestroyWindow(self.win)
        SDL_Quit()

    def show_keyboard(
        self,
        system_keyboard,
        softinput_mode,
        input_type,
        keyboard_suggestions=True,
    ):
        if SDL_IsTextInputActive():
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
                    SDL_SetTextInputRect(rect)
                elif softinput_mode == 'pan':
                    # tell Android the TextInput is at the screen
                    # bottom, so that it always pans
                    rect.y = wy - 5
                    rect.x = 0
                    rect.w = wx
                    rect.h = 5
                    SDL_SetTextInputRect(rect)
                else:
                    # Supporting 'resize' needs to call the Android
                    # API to set ADJUST_RESIZE mode, and change the
                    # java bootstrap to a different root Layout.
                    rect.y = 0
                    rect.x = 0
                    rect.w = 10
                    rect.h = 1
                    SDL_SetTextInputRect(rect)

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

            SDL_StartTextInput()
        finally:
            PyMem_Free(<void *>rect)

    def hide_keyboard(self):
        if SDL_IsTextInputActive():
            SDL_StopTextInput()

    def is_keyboard_shown(self):
        return SDL_IsTextInputActive()

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
        if event.type == SDL_QUIT:
            return ('quit', )
        elif event.type == SDL_MOUSEMOTION:
            x = event.motion.x
            y = event.motion.y
            return ('mousemotion', x, y)
        elif event.type == SDL_MOUSEBUTTONDOWN or event.type == SDL_MOUSEBUTTONUP:
            x = event.button.x
            y = event.button.y
            button = event.button.button
            action = 'mousebuttondown' if event.type == SDL_MOUSEBUTTONDOWN else 'mousebuttonup'
            return (action, x, y, button)
        elif event.type == SDL_MOUSEWHEEL:
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
        elif event.type == SDL_FINGERMOTION:
            fid = event.tfinger.fingerId
            x = event.tfinger.x
            y = event.tfinger.y
            pressure = event.tfinger.pressure
            return ('fingermotion', fid, x, y, pressure)
        elif event.type == SDL_FINGERDOWN or event.type == SDL_FINGERUP:
            fid = event.tfinger.fingerId
            x = event.tfinger.x
            y = event.tfinger.y
            pressure = event.tfinger.pressure
            action = 'fingerdown' if event.type == SDL_FINGERDOWN else 'fingerup'
            return (action, fid, x, y, pressure)
        elif event.type == SDL_JOYAXISMOTION:
            return (
                'joyaxismotion',
                event.jaxis.which, event.jaxis.axis, event.jaxis.value
            )
        elif event.type == SDL_JOYHATMOTION:
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
        elif event.type == SDL_JOYBALLMOTION:
            return (
                'joyballmotion',
                event.jball.which, event.jball.ball,
                event.jball.xrel, event.jball.yrel
            )
        elif event.type == SDL_JOYBUTTONDOWN:
            return ('joybuttondown', event.jbutton.which, event.jbutton.button)
        elif event.type == SDL_JOYBUTTONUP:
            return ('joybuttonup', event.jbutton.which, event.jbutton.button)
        elif event.type == SDL_WINDOWEVENT:
            if event.window.event == SDL_WINDOWEVENT_EXPOSED:
                action = ('windowexposed', )
            elif event.window.event == SDL_WINDOWEVENT_RESIZED:
                action = (
                    'windowresized',
                    event.window.data1, event.window.data2
                )
            elif event.window.event == SDL_WINDOWEVENT_MINIMIZED:
                action = ('windowminimized', )
            elif event.window.event == SDL_WINDOWEVENT_MAXIMIZED:
                action = ('windowmaximized', )
            elif event.window.event == SDL_WINDOWEVENT_RESTORED:
                action = ('windowrestored', )
            elif event.window.event == SDL_WINDOWEVENT_SHOWN:
                action = ('windowshown', )
            elif event.window.event == SDL_WINDOWEVENT_HIDDEN:
                action = ('windowhidden', )
            elif event.window.event == SDL_WINDOWEVENT_ENTER:
                action = ('windowenter', )
            elif event.window.event == SDL_WINDOWEVENT_LEAVE:
                action = ('windowleave', )
            elif event.window.event == SDL_WINDOWEVENT_FOCUS_GAINED:
                action = ('windowfocusgained', )
            elif event.window.event == SDL_WINDOWEVENT_FOCUS_LOST:
                action = ('windowfocuslost', )
            elif event.window.event == SDL_WINDOWEVENT_CLOSE:
                action = ('windowclose', )
            elif event.window.event == SDL_WINDOWEVENT_MOVED:
                action = (
                    'windowmoved',
                    event.window.data1, event.window.data2
                )
            else:
                #    print('receive unknown sdl window event', event.type)
                pass
            return action
        elif event.type == SDL_KEYDOWN or event.type == SDL_KEYUP:
            action = 'keydown' if event.type == SDL_KEYDOWN else 'keyup'
            mod = event.key.keysym.mod
            scancode = event.key.keysym.scancode
            key = event.key.keysym.sym
            return (action, mod, key, scancode, None)
        elif event.type == SDL_TEXTINPUT:
            s = event.text.text.decode('utf-8')
            return ('textinput', s)
        elif event.type == SDL_TEXTEDITING:
            s = event.edit.text.decode('utf-8')
            return ('textedit', s)
        elif event.type == SDL_DROPFILE:
            return ('dropfile', event.drop.file)
        elif event.type == SDL_DROPTEXT:
            return ('droptext', event.drop.file)
        elif event.type == SDL_DROPBEGIN:
            return ('dropbegin',)
        elif event.type == SDL_DROPCOMPLETE:
            return ('dropend',)
        else:
            #    print('receive unknown sdl window event', event.type)
            pass

    def flip(self):
        SDL_GL_SwapWindow(self.win)

    def save_bytes_in_png(self, filename, data, int width, int height):
        cdef SDL_Surface *surface = SDL_CreateRGBSurfaceFrom(
            <char *>data, width, height, 24, width * 3,
            0x0000ff, 0x00ff00, 0xff0000, 0
        )
        cdef bytes bytes_filename = <bytes>filename.encode('utf-8')
        cdef char *real_filename = <char *>bytes_filename

        cdef SDL_Surface *flipped_surface = flipVert(surface)
        IMG_SavePNG(flipped_surface, real_filename)
        SDL_FreeSurface(surface)
        SDL_FreeSurface(flipped_surface)

    def grab_mouse(self, grab):
        SDL_SetWindowGrab(self.win, SDL_TRUE if grab else SDL_FALSE)

    def get_relative_mouse_pos(self):
        cdef int x, y
        SDL_GetGlobalMouseState(&x, &y)
        wx, wy = self.get_window_pos()
        return x - wx, y - wy

    def set_custom_titlebar(self, titlebar_widget):
        SDL_SetWindowBordered(self.win, SDL_FALSE)
        return SDL_SetWindowHitTest(self.win,custom_titlebar_handler_callback,<void *>titlebar_widget)

    @property
    def window_size(self):
        cdef int w, h
        SDL_GetWindowSize(self.win, &w, &h)
        return [w, h]


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
    cdef SDL_Surface* result = SDL_CreateRGBSurface(
        sfc.flags, sfc.w, sfc.h, sfc.format.BytesPerPixel * 8,
        sfc.format.Rmask, sfc.format.Gmask, sfc.format.Bmask,
        sfc.format.Amask
    )

    cdef Uint8* pixels = <Uint8*>sfc.pixels
    cdef Uint8* rpixels = <Uint8*>result.pixels

    cdef tuple output = (
        <int>sfc.w, <int>sfc.h,
        <int>sfc.format.BytesPerPixel,
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
