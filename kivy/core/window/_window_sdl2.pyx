include "../../../kivy/lib/sdl2.pxi"
include "../../../kivy/graphics/config.pxi"

from libc.string cimport memcpy
from os import environ
from kivy.config import Config
from kivy.logger import Logger
from kivy import platform

from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free

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
        if event.type == SDL_APP_TERMINATING:
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
                     resizable, state):
        self.win_flags = SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN | SDL_WINDOW_ALLOW_HIGHDPI

        IF USE_IOS:
            self.win_flags |= SDL_WINDOW_BORDERLESS | SDL_WINDOW_RESIZABLE | SDL_WINDOW_FULLSCREEN_DESKTOP
        ELSE:
            if resizable:
                self.win_flags |= SDL_WINDOW_RESIZABLE
            if borderless:
                self.win_flags |= SDL_WINDOW_BORDERLESS
            if fullscreen == 'auto':
                self.win_flags |= SDL_WINDOW_FULLSCREEN_DESKTOP
            elif fullscreen is True:
                self.win_flags |= SDL_WINDOW_FULLSCREEN
        if state == 'maximized':
            self.win_flags |= SDL_WINDOW_MAXIMIZED
        elif state == 'minimized':
            self.win_flags |= SDL_WINDOW_MINIMIZED
        elif state == 'hidden':
            self.win_flags |= SDL_WINDOW_HIDDEN

        if SDL_Init(SDL_INIT_VIDEO | SDL_INIT_JOYSTICK) < 0:
            self.die()

        # Set default orientation (force landscape for now)
        cdef bytes orientations
        if PY3:
            orientations = bytes(environ.get('KIVY_ORIENTATION',
                'LandscapeLeft LandscapeRight'), encoding='utf8')
        elif USE_IOS:
            # ios should use all if available
            orientations = <bytes>environ.get('KIVY_ORIENTATION',
                'LandscapeLeft LandscapeRight Portrait PortraitUpsideDown')
        else:
            orientations = <bytes>environ.get('KIVY_ORIENTATION',
                'LandscapeLeft LandscapeRight')
        SDL_SetHint(SDL_HINT_ORIENTATIONS, <bytes>orientations)

        SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
        SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 16)
        SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 1)
        SDL_GL_SetAttribute(SDL_GL_RED_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_BLUE_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_GREEN_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_ALPHA_SIZE, 8)
        SDL_GL_SetAttribute(SDL_GL_RETAINED_BACKING, 0)
        SDL_GL_SetAttribute(SDL_GL_ACCELERATED_VISUAL, 1)

        if x is None:
            x = SDL_WINDOWPOS_UNDEFINED
        if y is None:
            y = SDL_WINDOWPOS_UNDEFINED

        # Multisampling:
        # (The number of samples is limited to 4, because greater values
        # aren't supported with some video drivers.)
        cdef int multisamples
        multisamples = Config.getint('graphics', 'multisamples')
        if multisamples > 0:
            # try to create window with multisampling:
            SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 1)
            SDL_GL_SetAttribute(SDL_GL_MULTISAMPLESAMPLES, min(multisamples, 4))
            self.win = SDL_CreateWindow(NULL, x, y, width, height,
                                        self.win_flags)
            if not self.win:
                # if an error occurred, create window without multisampling:
                SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 0)
                SDL_GL_SetAttribute(SDL_GL_MULTISAMPLESAMPLES, 0)
                self.win = SDL_CreateWindow(NULL, x, y, width, height,
                                            self.win_flags)
        else:
            self.win = SDL_CreateWindow(NULL, x, y, width, height,
                                        self.win_flags)

        if not self.win:
            self.die()

        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 2)
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 0)

        IF not USE_OPENGL_MOCK:
            self.ctx = SDL_GL_CreateContext(self.win)
            if not self.ctx:
                self.die()
        SDL_JoystickOpen(0)

        SDL_SetEventFilter(_event_filter, <void *>self)

        SDL_EventState(SDL_DROPFILE, SDL_ENABLE)
        cdef int w, h
        SDL_GetWindowSize(self.win, &w, &h)
        return w, h

    def _set_cursor_state(self, value):
        SDL_ShowCursor(value)

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
        if USE_IOS and not USE_OPENGL_MOCK:
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

    def set_window_title(self,  title):
        SDL_SetWindowTitle(self.win, <bytes>title.encode('utf-8'))

    def set_window_icon(self, filename):
        icon = IMG_Load(<bytes>filename.encode('utf-8'))
        SDL_SetWindowIcon(self.win, icon)

    def teardown_window(self):
        IF not USE_OPENGL_MOCK:
            SDL_GL_DeleteContext(self.ctx)
        SDL_DestroyWindow(self.win)
        SDL_Quit()

    def show_keyboard(self, system_keyboard, softinput_mode):
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
                    rect.y = max(0, wy - target.to_window(0, target.top)[1]) if target else 0
                    rect.x = max(0, target.to_window(target.x, 0)[0]) if target else 0
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
        elif event.type == SDL_DROPFILE:
            return ('dropfile', event.drop.file)
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
            x = event.button.x
            y = event.button.y
            button = event.button.button
            action = 'mousewheel' + ('down' if x > 0 else 'up') if x != 0 else ('left' if y < 0 else 'right')
            return (action, x, y, button)
        elif event.type == SDL_FINGERMOTION:
            fid = event.tfinger.fingerId
            x = event.tfinger.x
            y = event.tfinger.y
            return ('fingermotion', fid, x, y)
        elif event.type == SDL_FINGERDOWN or event.type == SDL_FINGERUP:
            fid = event.tfinger.fingerId
            x = event.tfinger.x
            y = event.tfinger.y
            action = 'fingerdown' if event.type == SDL_FINGERDOWN else 'fingerup'
            return (action, fid, x, y)
        elif event.type == SDL_JOYAXISMOTION:
            return ('joyaxismotion', event.jaxis.which, event.jaxis.axis, event.jaxis.value)
        elif event.type == SDL_JOYHATMOTION:
            vx = 0
            vy = 0
            if (event.jhat.value != SDL_HAT_CENTERED):
                if (event.jhat.value & SDL_HAT_UP):
                    vy=1
                elif (event.jhat.value & SDL_HAT_DOWN):
                    vy=-1
                if (event.jhat.value & SDL_HAT_RIGHT):
                    vx=1
                elif (event.jhat.value & SDL_HAT_LEFT):
                    vx=-1
            return ('joyhatmotion', event.jhat.which, event.jhat.hat, (vx,vy))
        elif event.type == SDL_JOYBALLMOTION:
            return ('joyballmotion', event.jball.which,
                       event.jball.ball, event.jball.xrel, event.jball.yrel)
        elif event.type == SDL_JOYBUTTONDOWN:
            return ('joybuttondown', event.jbutton.which, event.jbutton.button)
        elif event.type == SDL_JOYBUTTONUP:
            return ('joybuttonup', event.jbutton.which, event.jbutton.button)
        elif event.type == SDL_WINDOWEVENT:
            if event.window.event == SDL_WINDOWEVENT_EXPOSED:
                action = ('windowexposed', )
            elif event.window.event == SDL_WINDOWEVENT_RESIZED:
                action = ('windowresized', event.window.data1, event.window.data2)
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
                action = ('windowmoved', event.window.data1, event.window.data2)
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
        else:
            #    print('receive unknown sdl event', event.type)
            pass

    def flip(self):
        SDL_GL_SwapWindow(self.win)

    def save_bytes_in_png(self, filename, data, int width, int height):

        cdef SDL_Surface *surface = SDL_CreateRGBSurfaceFrom(
            <char *>data, width, height, 24, width*3,
            0x0000ff, 0x00ff00, 0xff0000, 0)
        cdef bytes bytes_filename = <bytes>filename.encode('utf-8')
        cdef char *real_filename = <char *>bytes_filename

        cdef SDL_Surface *flipped_surface = flipVert(surface)
        IMG_SavePNG(flipped_surface, real_filename)

    def grab_mouse(self, grab):
        SDL_SetWindowGrab(self.win, SDL_TRUE if grab else SDL_FALSE)



    property window_size:
        def __get__(self):
            cdef int w, h
            SDL_GetWindowSize(self.win, &w, &h)
            return [w, h]


# Based on the example at
# http://content.gpwiki.org/index.php/OpenGL:Tutorials:Taking_a_Screenshot
cdef SDL_Surface* flipVert(SDL_Surface* sfc):
    cdef SDL_Surface* result = SDL_CreateRGBSurface(
        sfc.flags, sfc.w, sfc.h, sfc.format.BytesPerPixel * 8,
        sfc.format.Rmask, sfc.format.Gmask, sfc.format.Bmask,
        sfc.format.Amask)


    cdef Uint8* pixels = <Uint8*>sfc.pixels
    cdef Uint8* rpixels = <Uint8*>result.pixels

    cdef tuple output = (<int>sfc.w, <int>sfc.h, <int>sfc.format.BytesPerPixel,
                         <int>sfc.pitch)
    print(output)

    cdef Uint32 pitch = sfc.pitch
    cdef Uint32 pxlength = pitch*sfc.h

    cdef Uint32 pos

    cdef int line
    for line in range(sfc.h):
        pos = line * pitch;
        memcpy(&rpixels[pos], &pixels[(pxlength-pos)-pitch], pitch)

    return result
