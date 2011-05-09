__all__ = ('sdl_init', 'sdl_quit')

cdef extern from "SDL.h":
    int SDL_Init(unsigned int flags)
    void SDL_Quit()

cdef int SDL_INIT_TIMER		= 0x00000001
cdef int SDL_INIT_AUDIO		= 0x00000010
cdef int SDL_INIT_VIDEO		= 0x00000020
cdef int SDL_INIT_JOYSTICK	= 0x00000200
cdef int SDL_INIT_NOPARACHUTE	= 0x00100000
cdef int SDL_INIT_EVENTTHREAD	= 0x01000000
cdef int SDL_INIT_EVERYTHING	= 0x0000FFFF

def sdl_init():
    SDL_Init(SDL_INIT_VIDEO|SDL_INIT_AUDIO)

def sdl_quit():
    SDL_Quit()
