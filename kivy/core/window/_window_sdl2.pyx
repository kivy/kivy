include "../../../kivy/lib/sdl2.pxi"

cdef class _WindowSDL2Storage:
    cdef SDL_Window *win
    cdef SDL_GLContext ctx
    cdef SDL_Surface *surface
    cdef SDL_Surface *icon
    cdef int win_flags

    def __cinit__(self):
        self.win = NULL
        self.ctx = NULL
        self.surface = NULL
        self.win_flags = 0

    def die(self):
        raise RuntimeError(<bytes> SDL_GetError())

    def setup_window(self, x, y, width, height, use_fake, use_fullscreen,
                     shaped=False):
        self.win_flags = SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE
        if use_fake or shaped:
            self.win_flags |= SDL_WINDOW_BORDERLESS
        if use_fullscreen == 'auto':
            self.win_flags |= SDL_WINDOW_FULLSCREEN_DESKTOP
        elif use_fullscreen:
            self.win_flags |= SDL_WINDOW_FULLSCREEN

        if SDL_Init(SDL_INIT_VIDEO| SDL_INIT_JOYSTICK) < 0:
            self.die()

        '''
        # Set default orientation (force landscape for now)
        cdef bytes orientations
        orientations = <bytes>environ.get('KIVY_ORIENTATION',
                'LandscapeLeft LandscapeRight');
        SDL_SetHint(SDL_HINT_ORIENTATIONS, orientations);
        '''

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

        if not shaped:
            self.win = SDL_CreateWindow(NULL, x, y, width, height,
                                        self.win_flags)
        else:
            self.win = SDL_CreateShapedWindow(NULL, x, y, width, height,
                                              self.win_flags)
            #shape_mode = SDL_WindowShapeMode()
            #shape_mode.mode = ShapeModeColorKey
            #shape_mode.parameters.colorKey = (0, 0, 0, 255)
            #SDL_SetWindowShape(Self.win, circle_sf, shape_mode)

        if not self.win:
            self.die()

        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 2)
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 0)

        self.ctx = SDL_GL_CreateContext(self.win)
        if not self.ctx:
            self.die()
        cdef SDL_DisplayMode mode
        SDL_GetWindowDisplayMode(self.win, &mode)
        SDL_JoystickOpen(0)

        SDL_EventState(SDL_DROPFILE, SDL_ENABLE)
        return mode.w, mode.h

    def resize_display_mode(self, w, h):
        cdef SDL_DisplayMode mode
        SDL_GetWindowDisplayMode(self.win, &mode)
        mode.w = w
        mode.h = h
        SDL_SetWindowDisplayMode(self.win, &mode)
        SDL_GetWindowDisplayMode(self.win, &mode)

    def resize_window(self, w, h):
        SDL_SetWindowSize(self.win, w, h)

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

    def set_window_title(self, str title):
        SDL_SetWindowTitle(self.win, <bytes>title.encode('utf-8'))

    def set_window_icon(self, str filename):
        icon = IMG_Load(<bytes>filename.encode('utf-8'))
        SDL_SetWindowIcon(self.win, icon)

    def teardown_window(self):
        SDL_GL_DeleteContext(self.ctx)
        SDL_DestroyWindow(self.win)
        SDL_Quit()

    def show_keyboard(self):
        if not SDL_IsTextInputActive():
            SDL_StartTextInput()

    def hide_keyboard(self):
        if SDL_IsTextInputActive():
            SDL_StopTextInput()

    def is_keyboard_shown(self):
        return SDL_IsTextInputActive()

    def poll(self):
        cdef SDL_Event event

        if SDL_PollEvent(&event) == 0:
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
                if __debug__:
                    print('receive unknown sdl window event', event.type)
                pass
            return action
        elif event.type == SDL_KEYDOWN or event.type == SDL_KEYUP:
            action = 'keydown' if event.type == SDL_KEYDOWN else 'keyup'
            mod = event.key.keysym.mod
            scancode = event.key.keysym.get('scancode', '')
            key = event.key.keysym.sym
            return (action, mod, key, scancode, None)
        elif event.type == SDL_TEXTINPUT:
            s = event.text.text.decode('utf-8')
            return ('textinput', s)
        else:
            if __debug__:
                print('receive unknown sdl event', event.type)
            pass

    def flip(self):
        SDL_GL_SwapWindow(self.win)


