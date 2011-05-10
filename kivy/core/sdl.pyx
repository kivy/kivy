__all__ = ('sdl_init', 'sdl_quit')


cdef extern from "SDL.h":
    ctypedef void *SDL_Window
    ctypedef void *SDL_GLContext
    ctypedef void *SDL_Surface

    ctypedef struct SDL_Event:
        unsigned int type

    int SDL_Init(unsigned int)
    void SDL_Quit()

    SDL_Window *SDL_CreateWindow(char*, int, int, int, int, unsigned int)
    void SDL_DestroyWindow(SDL_Window*)

    int SDL_GL_SetSwapInterval(int)
    int SDL_Flip(SDL_Surface*)
    SDL_Surface *SDL_GetWindowSurface(SDL_Window*)
    SDL_GLContext SDL_GL_CreateContext(SDL_Window*)
    void SDL_GL_DeleteContext(SDL_GLContext)

    int SDL_PollEvent(SDL_Event*)


cdef int SDL_WINDOW_OPENGL = 0x00000002
cdef int SDL_INIT_VIDEO = 0x00000020
cdef int SDL_WINDOW_SHOWN = 0x00000004
cdef int SDL_QUIT = 0x100


#cdef int SDL_INIT_TIMER		= 0x00000001
#cdef int SDL_INIT_AUDIO		= 0x00000010
#cdef int SDL_INIT_JOYSTICK	= 0x00000200
#cdef int SDL_INIT_NOPARACHUTE	= 0x00100000
#cdef int SDL_INIT_EVENTTHREAD	= 0x01000000
#cdef int SDL_INIT_EVERYTHING	= 0x0000FFFF


cdef SDL_Window *win = NULL
cdef SDL_GLContext ctx = NULL
cdef SDL_Surface *surface = NULL


def setup_window(width, height):
    global win, ctx, surface

    if SDL_Init(SDL_INIT_VIDEO) < 0:
        raise RuntimeError("Unable to initialize SDL video")

    win = SDL_CreateWindow(NULL, 0, 0, width, height,
                           SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN)
    if not win:
        raise RuntimeError("Unable to create SDL window")

    ctx = SDL_GL_CreateContext(win)

    # XXX?
    SDL_GL_SetSwapInterval(1)

    surface = SDL_GetWindowSurface(win)




def teardown_window():
    SDL_GL_DeleteContext(ctx)
    SDL_DestroyWindow(win)
    SDL_Quit()


def poll():
    cdef SDL_Event event
    SDL_PollEvent(&event)
    if event.type != SDL_QUIT:
        return True


def flip():
    SDL_Flip(surface)

