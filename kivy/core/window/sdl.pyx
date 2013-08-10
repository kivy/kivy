from os import environ
from libcpp cimport bool

cdef extern from "Python.h":
    object PyUnicode_FromString(char *s)

cdef extern from "SDL.h":
    ctypedef void *SDL_Window
    ctypedef void *SDL_GLContext
    ctypedef void *SDL_Surface

    ctypedef enum SDL_bool:
        pass

    ctypedef struct SDL_DisplayMode:
        int w
        int h

    ctypedef struct SDL_MouseMotionEvent:
        int x
        int y

    ctypedef struct SDL_MouseButtonEvent:
        int x
        int y
        unsigned char button
        unsigned char state

    ctypedef struct SDL_WindowEvent:
        unsigned char event
        int data1
        int data2

    ctypedef struct SDL_Keysym:
        unsigned int scancode
        unsigned int sym
        unsigned short mod
        unsigned int unicode

    ctypedef struct SDL_KeyboardEvent:
        unsigned char state
        unsigned char repeat
        SDL_Keysym keysym

    ctypedef struct SDL_TextInputEvent:
        unsigned char *text

    ctypedef struct SDL_TouchFingerEvent:
        long touchId
        long fingerId
        unsigned char state
        unsigned short x
        unsigned short y
        short dx
        short dy
        unsigned short pressure

    ctypedef struct SDL_Event:
        unsigned int type
        SDL_MouseMotionEvent motion
        SDL_MouseButtonEvent button
        SDL_WindowEvent window
        SDL_KeyboardEvent key
        SDL_TextInputEvent text
        SDL_TouchFingerEvent tfinger

    # Events
    int SDL_QUIT
    int SDL_WINDOWEVENT
    int SDL_SYSWMEVENT
    int SDL_KEYDOWN
    int SDL_KEYUP
    int SDL_MOUSEMOTION
    int SDL_MOUSEBUTTONDOWN
    int SDL_MOUSEBUTTONUP
    int SDL_TEXTINPUT
    int SDL_FINGERDOWN
    int SDL_FINGERUP
    int SDL_FINGERMOTION

    # GL Attribute
    int SDL_GL_DEPTH_SIZE
    int SDL_GL_RED_SIZE
    int SDL_GL_BLUE_SIZE
    int SDL_GL_GREEN_SIZE
    int SDL_GL_ALPHA_SIZE
    int SDL_GL_STENCIL_SIZE
    int SDL_GL_DOUBLEBUFFER
    int SDL_GL_CONTEXT_MAJOR_VERSION
    int SDL_GL_CONTEXT_MINOR_VERSION
    int SDL_GL_RETAINED_BACKING
    int SDL_GL_ACCELERATED_VISUAL

    # Init flags
    int SDL_INIT_VIDEO
    int SDL_INIT_EVERYTHING

    # Window flags
    int SDL_WINDOW_OPENGL
    int SDL_WINDOW_SHOWN
    int SDL_WINDOW_BORDERLESS
    int SDL_WINDOW_RESIZABLE
    int SDL_WINDOW_FULLSCREEN

    ## Window event
    int SDL_WINDOWEVENT_EXPOSED
    int SDL_WINDOWEVENT_RESIZED
    int SDL_WINDOWEVENT_MINIMIZED
    int SDL_WINDOWEVENT_RESTORED

    ## Hints
    char *SDL_HINT_ORIENTATIONS

    int SDL_Init(unsigned int)
    void SDL_Quit()

    SDL_Window *SDL_CreateWindow(char *, int, int, int, int, unsigned int)
    void SDL_DestroyWindow(SDL_Window *)
    void SDL_GL_SetAttribute(int, int)
    void SDL_SetWindowTitle(SDL_Window *, char *)
    int SDL_GetWindowDisplayMode(SDL_Window *, SDL_DisplayMode *)
    int SDL_SetWindowDisplayMode(SDL_Window *, SDL_DisplayMode *)
    void SDL_GL_SwapWindow(SDL_Window *)

    #int SDL_GL_SetSwapInterval(int)
    int SDL_Flip(SDL_Surface *)
    SDL_Surface *SDL_GetWindowSurface(SDL_Window *)
    SDL_GLContext SDL_GL_CreateContext(SDL_Window *)
    void SDL_GL_DeleteContext(SDL_GLContext)

    int SDL_PollEvent(SDL_Event *)
    void SDL_PumpEvents()
    int SDL_EventState(unsigned int, int)

    char *SDL_GetError()
    bool SDL_SetHint(char *, char *)

cdef extern void SDL_StartTextInput()
cdef extern void SDL_StopTextInput()
cdef extern SDL_bool SDL_IsTextInputActive()
cdef SDL_Window *win = NULL
cdef SDL_GLContext ctx = NULL
cdef SDL_Surface *surface = NULL
cdef int win_flags = 0

def die():
    raise RuntimeError(<bytes> SDL_GetError())

def setup_window(width, height, use_fake, use_fullscreen):
    global win, ctx, win_flags

    win_flags = SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN | SDL_WINDOW_BORDERLESS | SDL_WINDOW_RESIZABLE
    '''
    win_flags = SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE | SDL_WINDOW_SHOWN
    if use_fake:
        win_flags |= SDL_WINDOW_BORDERLESS
    if use_fullscreen:
        win_flags |= SDL_WINDOW_FULLSCREEN
    '''

    if SDL_Init(SDL_INIT_VIDEO) < 0:
        die()

    # Set default orientation (force landscape for now)
    cdef bytes orientations
    orientations = <bytes>environ.get('KIVY_ORIENTATION',
            'LandscapeLeft LandscapeRight');
    SDL_SetHint(SDL_HINT_ORIENTATIONS, orientations);


    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
    SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 16)
    SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 1)
    SDL_GL_SetAttribute(SDL_GL_RED_SIZE, 8)
    SDL_GL_SetAttribute(SDL_GL_BLUE_SIZE, 8)
    SDL_GL_SetAttribute(SDL_GL_GREEN_SIZE, 8)
    SDL_GL_SetAttribute(SDL_GL_ALPHA_SIZE, 8)
    SDL_GL_SetAttribute(SDL_GL_RETAINED_BACKING, 0)
    SDL_GL_SetAttribute(SDL_GL_ACCELERATED_VISUAL, 1)

    '''
    # optimized flags, but incompatible with kivy ?
    # like stencil is needed for ScrollView / Stencil, and alpha.. ?
    SDL_GL_SetAttribute(SDL_GL_RED_SIZE, 5);
    SDL_GL_SetAttribute(SDL_GL_GREEN_SIZE, 6);
    SDL_GL_SetAttribute(SDL_GL_BLUE_SIZE, 5);
    SDL_GL_SetAttribute(SDL_GL_ALPHA_SIZE, 0);
    SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 0);
    SDL_GL_SetAttribute(SDL_GL_RETAINED_BACKING, 0);
    SDL_GL_SetAttribute(SDL_GL_ACCELERATED_VISUAL, 1);
    '''

    win = SDL_CreateWindow(NULL, 0, 0, width, height, win_flags)
    if not win:
        die()

    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 2);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 0);

    ctx = SDL_GL_CreateContext(win)
    assert ctx != NULL
    cdef SDL_DisplayMode mode
    SDL_GetWindowDisplayMode(win, &mode)
    return mode.w, mode.h


def resize_window(w, h):
    cdef SDL_DisplayMode mode
    SDL_GetWindowDisplayMode(win, &mode)
    mode.w = w
    mode.h = h
    SDL_SetWindowDisplayMode(win, &mode)
    SDL_GetWindowDisplayMode(win, &mode)


def set_window_title(str title):
    SDL_SetWindowTitle(win, <bytes>title)


def teardown_window():
    SDL_GL_DeleteContext(ctx)
    SDL_DestroyWindow(win)
    SDL_Quit()


def show_keyboard():
    if not SDL_IsTextInputActive():
        SDL_StartTextInput()

def hide_keyboard():
    if SDL_IsTextInputActive():
        SDL_StopTextInput()

def is_keyboard_shown():
    return SDL_IsTextInputActive()

def poll():
    cdef SDL_Event event

    if SDL_PollEvent(&event) == 0:
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
    elif event.type == SDL_WINDOWEVENT:
        if event.window.event == SDL_WINDOWEVENT_EXPOSED:
            action = ('windowexposed', )
        elif event.window.event == SDL_WINDOWEVENT_RESIZED:
            action = ('windowresized', event.window.data1, event.window.data2)
        elif event.window.event == SDL_WINDOWEVENT_MINIMIZED:
            action = ('windowminimized', )
        elif event.window.event == SDL_WINDOWEVENT_RESTORED:
            action = ('windowrestored', )
        else:
            if __debug__:
                print('receive unknown sdl event', event.type)
            pass
        return action
    elif event.type == SDL_KEYDOWN or event.type == SDL_KEYUP:
        action = 'keydown' if event.type == SDL_KEYDOWN else 'keyup'
        mod = event.key.keysym.mod
        scancode = event.key.keysym.scancode
        unicode = event.key.keysym.unicode
        key = event.key.keysym.sym
        return (action, mod, key, scancode, unicode)
    elif event.type == SDL_TEXTINPUT:
        s = PyUnicode_FromString(<char *>event.text.text)
        return ('textinput', s)
    else:
        if __debug__:
            print('receive unknown sdl event', event.type)
        pass


def flip():
    SDL_GL_SwapWindow(win)

