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

    cdef SDL_Surface *image = SDL_CreateRGBSurfaceFrom(<void *>pixels, w, h, 32, pitch, 0x00000000ff, 0x0000ff00, 0x00ff0000, 0xff000000)

    IMG_SavePNG(image, c_filename)
    SDL_FreeSurface(image)

def load(filename):
    cdef bytes c_filename = filename.encode('utf-8')
    cdef SDL_Surface *image = IMG_Load(c_filename)
    cdef SDL_Surface *image2 = NULL
    cdef SDL_Surface *fimage = NULL
    cdef SDL_PixelFormat pf
    cdef bytes pixels

    try:
        if image == NULL:
            #print 'UNABLE TO LOAD O_o?'
            return None

        fmt = ''
        if image.format.BytesPerPixel == 3:
            fmt = 'rgb'
        elif image.format.BytesPerPixel == 4:
            fmt = 'rgba'

        # FIXME the format might be 3 or 4, but it doesn't mean it's rgb/rgba.
        # It could be argb, bgra etc. it needs to be detected correctly. I guess
        # we could even let the original pass, bgra / argb support exists in
        # some opengl card.

        if fmt not in ('rgb', 'rgba'):
            #print 'origin image format'
            #print '  format', image.format.format
            #print '  bytesperpixel', image.format.BytesPerPixel
            #print '  bitsperpixel', image.format.BitsPerPixel

            memset(&pf, 0, sizeof(pf))
            pf.BitsPerPixel = 8
            pf.Rmask = 0xff
            pf.Gmask = 0xff00
            pf.Bmask = 0xff0000
            if fmt == 'rgb':
                pf.format = SDL_PIXELFORMAT_RGB888
                pf.BytesPerPixel = 3
            else:
                pf.format = SDL_PIXELFORMAT_RGBA8888
                pf.BytesPerPixel = 4
                pf.Amask = 0xff000000

            image2 = SDL_ConvertSurface(image, &pf, 0)
            if image2 == NULL:
                #print 'UNABLE TO CONVERT O_o?'
                return None

            fimage = image2
        else:
            if (image.format.Rshift > image.format.Bshift):
                memset(&pf, 0, sizeof(pf))
                pf.BitsPerPixel = 32
                pf.Rmask = 0x000000FF
                pf.Gmask = 0x0000FF00
                pf.Bmask = 0x00FF0000
                pf.Amask = 0xFF000000
                image2 = SDL_ConvertSurface(image, &pf, 0)
                fimage = image2
            else:
                fimage = image

        pixels = (<char *>fimage.pixels)[:fimage.pitch * fimage.h]
        return (fimage.w, fimage.h, fmt, pixels, fimage.pitch)

    finally:
        if image:
            SDL_FreeSurface(image)
        if image2:
            SDL_FreeSurface(image2)
