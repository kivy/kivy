include '../../lib/sdl2.pxi'


from kivy.logger import Logger
from libc.string cimport memset
from libc.stdlib cimport malloc

cdef int _is_init = 0

def init():
    global _is_init
    if _is_init:
        return

    cdef int ret
    for flags in (IMG_INIT_JPG, IMG_INIT_PNG, IMG_INIT_TIF, IMG_INIT_WEBP):
        ret = IMG_Init(flags)
        if ret & flags != flags:
            # FIXME replace flags by a good string
            Logger.error(
                'ImageSDL2: Failed to init required {} support'.format(flags))
            Logger.error('ImageSDL2: {}'.format(IMG_GetError()))

    _is_init = 1

def save(filename, w, h, fmt, pixels, flipped):
    # this only saves in png for now.
    cdef bytes c_filename = filename.encode('utf-8')
    cdef int pitch
    pitch = w * 4
    cdef char *c_pixels = pixels

    if flipped:
        Logger.warn(
            'ImageSDL2: saving flipped textures not supported; image will be flipped')
    cdef SDL_Surface *image = SDL_CreateRGBSurfaceFrom(c_pixels, w, h, 32, pitch, 0x00000000ff, 0x0000ff00, 0x00ff0000, 0xff000000)

    IMG_SavePNG(image, c_filename)
    SDL_FreeSurface(image)


cdef load_from_surface(SDL_Surface *image):
    cdef SDL_Surface *image2 = NULL
    cdef SDL_Surface *fimage = NULL
    cdef int want_rgba = 0, target_fmt = 0, n = 0
    cdef bytes pixels

    if image == NULL:
        Logger.warn('ImageSDL2: load_from_surface() with NULL surface')
        return None

    # SDL 2.0.5 now has endian-agnostic 32-bit pixel formats like RGB24,
    # but we can't count on that yet (RGB24 is available since 2.0)
    if SDL_BYTEORDER == SDL_BIG_ENDIAN:
        want_rgba = SDL_PIXELFORMAT_RGBA8888
    else:
        want_rgba = SDL_PIXELFORMAT_ABGR8888

    # Determine if we need pixel format conversion
    if image.format.format == want_rgba:
        fmt = 'rgba'
    elif image.format.format == SDL_PIXELFORMAT_RGB24:
        fmt = 'rgb'
    elif image.format.Amask:
        fmt = 'rgba'
        target_fmt = want_rgba
    elif image.format.palette != NULL:
        # We want RGB24 here, and rgba only if the palette has alpha
        fmt = 'rgba'
        target_fmt = want_rgba
# FIXME: ... but this breaks compile, "SDL_Color has no member unused"
#        for n in xrange(0, image.format.palette.ncolors):
#            if image.format.palette.colors[n].a < 0xFF:
#                fmt = 'rgba'
#                target_fmt = want_rgba
#                break
    else:
        fmt = 'rgb'
        target_fmt = SDL_PIXELFORMAT_RGB24

    # Convert if needed, and return a copy of the raw pixel data
    try:
        fimage = image
        if target_fmt != 0:
            image2 = SDL_ConvertSurfaceFormat(image, target_fmt, 0)
            if image2 == NULL:
                Logger.warn('ImageSDL2: error converting {} to {}: {}'.format(
                        SDL_GetPixelFormatName(image.format.format), 
                        SDL_GetPixelFormatName(target_fmt), 
                        SDL_GetError()))
                return None
            else:
                fimage = image2

        pixels = (<char *>fimage.pixels)[:fimage.pitch * fimage.h]
        return (fimage.w, fimage.h, fmt, pixels, fimage.pitch)
    finally:
        if image2:
            SDL_FreeSurface(image2)


def load_from_filename(filename):
    cdef bytes c_filename = filename.encode('utf-8')
    cdef SDL_Surface *image = IMG_Load(c_filename)
    if image == NULL:
        return
    try:
        return load_from_surface(image)
    finally:
        if image:
            SDL_FreeSurface(image)

def load_from_memory(bytes data):
    cdef SDL_RWops *rw = NULL
    cdef SDL_Surface *image = NULL
    cdef char *c_data = data

    rw = SDL_RWFromMem(c_data, len(data))
    if rw == NULL:
        return

    image = IMG_Load_RW(rw, 0)
    if image == NULL:
        return

    try:
        return load_from_surface(image)
    finally:
        if image:
            SDL_FreeSurface(image)
        if rw:
            SDL_FreeRW(rw)
