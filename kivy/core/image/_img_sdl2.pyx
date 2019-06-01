include '../../lib/sdl2.pxi'

import io
from kivy.logger import Logger
from libc.string cimport memset
from libc.stdlib cimport malloc

cdef int _is_init = 0

cdef struct SDL_RWops:
    long (* seek) (SDL_RWops * context, long offset,int whence)
    size_t(* read) ( SDL_RWops * context, void *ptr, size_t size, size_t maxnum)
    size_t(* write) (SDL_RWops * context, void *ptr,size_t size, size_t num)
    int (* close) (SDL_RWops * context)


cdef size_t rwops_bytesio_write(SDL_RWops *context, const void *ptr, size_t size, size_t num):
    cdef char *c_string = <char *>ptr
    byteio = <object>context.hidden.unknown.data1
    byteio.write(c_string[:size * num])
    return size * num


cdef int rwops_bytesio_close(SDL_RWops *context):
    byteio = <object>context.hidden.unknown.data1
    byteio.seek(0)


cdef SDL_RWops *rwops_bridge_to_bytesio(byteio):
    # works only for write.
    cdef SDL_RWops *rwops = SDL_AllocRW()
    rwops.hidden.unknown.data1 = <void *>byteio
    rwops.seek = NULL
    rwops.read = NULL
    rwops.write = &rwops_bytesio_write
    rwops.close =&rwops_bytesio_close
    return rwops


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

def save(filename, w, h, pixelfmt, pixels, flipped, imagefmt, quality=90):
    cdef bytes c_filename = None
    cdef SDL_RWops *rwops
    if not isinstance(filename, io.BytesIO):
        c_filename = filename.encode('utf-8')
    cdef int pitch

    if pixelfmt == "rgb":
        pitch = w * 3
    elif pixelfmt == "rgba":
        pitch = w * 4
    else:
        raise Exception("IMG SDL2 supports only pixelfmt rgb and rgba")

    cdef int lng, top, bot
    cdef list rng
    if flipped:
        # if flipped upside down
        # switch bytes(array) to list
        pixels = list(pixels)
        lng = len(pixels)
        rng = list(range(0, lng, pitch))

        while len(rng):
            try:
                top = rng.pop(0)
                bot = rng.pop()
            except IndexError:
                # odd height, single line remains, no swap
                break
            temp = pixels[top:top + pitch]
            pixels[top:top + pitch] = pixels[bot:bot + pitch]
            pixels[bot:bot + pitch] = temp

        # return to bytes(array) for sdl
        pixels = bytes(bytearray(pixels))

    cdef char *c_pixels = pixels
    cdef SDL_Surface *image = NULL

    if pixelfmt == "rgba":
        image = SDL_CreateRGBSurfaceFrom(
            c_pixels, w, h, 32, pitch,
            0x00000000ff, 0x0000ff00, 0x00ff0000, 0xff000000)
    elif pixelfmt == "rgb":
        image = SDL_CreateRGBSurfaceFrom(
            c_pixels, w, h, 24, pitch,
            0x0000ff, 0x00ff00, 0xff0000, 0)

    if c_filename is not None:
        if imagefmt == "png":
            IMG_SavePNG(image, c_filename)
        elif imagefmt == "jpg":
            IMG_SaveJPG(image, c_filename, quality)
    else:
        rwops = rwops_bridge_to_bytesio(filename)
        if imagefmt == "png":
            IMG_SavePNG_RW(image, rwops, 1)
        elif imagefmt == "jpg":
            IMG_SaveJPG_RW(image, rwops, 1, quality)
        SDL_FreeRW(rwops)

    if image:
        SDL_FreeSurface(image)

# NOTE: This must be kept up to date with ImageData supported formats. If you
# add support for converting/uploading (for example) ARGB, you must ensure
# that it is returned unmodified below to avoid converting to RGB/RGBA.
#
# FIXME:
# - Some PNG48 images with binary transparency load incorrectly
# - (Some?) 8/16 bit grayscale PNGs load incorrectly (likely SDL_Image problem)
cdef load_from_surface(SDL_Surface *image):
    cdef SDL_Surface *image2 = NULL
    cdef SDL_Surface *fimage = NULL
    cdef Uint32 want_rgba = 0, want_bgra = 0, target_fmt = 0
    cdef int n = 0
    cdef bytes pixels

    if image == NULL:
        Logger.warn('ImageSDL2: load_from_surface() with NULL surface')
        return None

    # SDL 2.0.5 now has endian-agnostic 32-bit pixel formats like RGB24,
    # but we can't count on that yet (RGB24 is available since 2.0)
    if SDL_BYTEORDER == SDL_BIG_ENDIAN:
        want_rgba = SDL_PIXELFORMAT_RGBA8888
        want_bgra = SDL_PIXELFORMAT_BGRA8888
    else:
        want_rgba = SDL_PIXELFORMAT_ABGR8888
        want_bgra = SDL_PIXELFORMAT_ARGB8888

    # Output format (string) - supported by ImageData. If the surface is
    # already in a supported pixel format, no conversion is done.
    fmt = ''

    # 32-bit rgba and bgra can be used directly
    if image.format.format == want_rgba:
        fmt = 'rgba'
    elif image.format.format == want_bgra:
        fmt = 'bgra'

    # Alpha mask or colorkey must be converted to rgba
    elif image.format.Amask or SDL_GetColorKey(image, NULL) == 0:
        fmt = 'rgba'
        target_fmt = want_rgba

    # Palette with alpha is converted to rgba
    elif image.format.palette != NULL:
        for n in xrange(0, image.format.palette.ncolors):
            if image.format.palette.colors[n].a < 0xFF:
                fmt = 'rgba'
                target_fmt = want_rgba
                break

    # 24bpp RGB/BGR without colorkey can be used directly.
    elif image.format.format == SDL_PIXELFORMAT_RGB24:
        fmt = 'rgb'
    elif image.format.format == SDL_PIXELFORMAT_BGR24:
        fmt = 'bgr'

    # Everything else is converted to RGB
    if not fmt:
        fmt = 'rgb'
        target_fmt = SDL_PIXELFORMAT_RGB24

    # Convert if needed, and return a copy of the raw pixel data
    try:
        fimage = image
        if target_fmt != 0:
            with nogil:
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
