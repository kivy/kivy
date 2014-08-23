'''
ImageIO OSX framework
=====================

Image loader implementation based on CoreGraphics OSX framework.

.. todo::

    clean all unused definitions
    handle all errors cases
    add documentation

'''

__all__ = ('ImageLoaderImageIO', )

from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageData, ImageLoader

from array import array
from libcpp cimport bool
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy

ctypedef unsigned long size_t
ctypedef signed long CFIndex

cdef unsigned int kCFStringEncodingUTF8 = 0x08000100

cdef extern from "stdlib.h":
    void* calloc(size_t, size_t)

cdef extern from "CoreGraphics/CGDataProvider.h":
    ctypedef void *CFDataRef
    unsigned char *CFDataGetBytePtr(CFDataRef)

    ctypedef struct CGPoint:
        float x
        float y

    ctypedef struct CGSize:
        float width
        float height

    ctypedef struct CGRect:
        CGPoint origin
        CGSize size

    CGRect CGRectMake(float, float, float, float)

cdef extern from "CoreFoundation/CFBase.h":
    ctypedef void *CFAllocatorRef
    ctypedef void *CFStringRef
    ctypedef void *CFURLRef
    ctypedef void *CFTypeRef
    CFStringRef CFStringCreateWithCString(CFAllocatorRef alloc, char *cStr,
            int encoding)

    void CFRelease(CFTypeRef cf)

cdef extern from "CoreFoundation/CFURL.h":
    ctypedef void *CFURLRef
    ctypedef int CFURLPathStyle
    int kCFURLPOSIXPathStyle
    CFURLRef CFURLCreateFromFileSystemRepresentation(
            CFAllocatorRef, unsigned char *, CFIndex, bool)
    CFURLRef CFURLCreateWithFileSystemPath(CFAllocatorRef allocator,
            CFStringRef filePath, CFURLPathStyle pathStyle, int isDirectory)

cdef extern from "CoreFoundation/CFDictionary.h":
    ctypedef void *CFDictionaryRef

cdef extern from "CoreGraphics/CGImage.h":
    ctypedef void *CGImageRef
    void CGImageRelease(CGImageRef image)
    size_t CGImageGetWidth(CGImageRef)
    size_t CGImageGetHeight(CGImageRef)
    int kCGImageAlphaNoneSkipLast
    int kCGImageAlphaNoneSkipFirst
    int kCGImageAlphaFirst
    int kCGImageAlphaLast
    int kCGImageAlphaPremultipliedLast
    int kCGImageAlphaPremultipliedFirst
    int kCGBitmapByteOrder32Host

cdef extern from "CoreGraphics/CGColorSpace.h": 
    ctypedef void *CGColorSpaceRef
    CGColorSpaceRef CGColorSpaceCreateDeviceRGB()
    void CGColorSpaceRelease(CGColorSpaceRef cs)

cdef extern from "CoreGraphics/CGAffineTransform.h":
    ctypedef void *CGAffineTransform
    CGAffineTransform CGAffineTransformMake(float a, float b, float c, float d, float tx, float ty)

cdef extern from "CoreGraphics/CGContext.h": 
    ctypedef void *CGContextRef
    void CGContextRelease(CGContextRef c)
    void CGContextDrawImage(CGContextRef, CGRect, CGImageRef)
    int kCGBlendModeCopy
    int kCGBlendModeNormal
    void CGContextSetBlendMode(CGContextRef, int)
    void CGContextConcatCTM(CGContextRef fc, CGAffineTransform matrix)

cdef extern from "CoreGraphics/CGBitmapContext.h":
    CGImageRef CGBitmapContextCreateImage(CGColorSpaceRef)
    CGContextRef CGBitmapContextCreate(
       void *data, size_t width, size_t height, size_t bitsPerComponent,
       size_t bytesPerRow, CGColorSpaceRef colorspace, unsigned int bitmapInfo)

cdef extern from "ImageIO/CGImageSource.h":
    ctypedef void *CGImageSourceRef
    CGImageSourceRef CGImageSourceCreateWithURL(
            CFURLRef, CFDictionaryRef)
    CGImageRef CGImageSourceCreateImageAtIndex(
            CGImageSourceRef, size_t, CFDictionaryRef)

cdef extern from "ImageIO/CGImageDestination.h":
    ctypedef void *CGImageDestinationRef
    CGImageDestinationRef CGImageDestinationCreateWithURL(
        CFURLRef, CFStringRef, size_t, CFDictionaryRef)
    void CGImageDestinationAddImage(CGImageDestinationRef idst,
        CGImageRef image, CFDictionaryRef properties)
    int CGImageDestinationFinalize(CGImageDestinationRef idst)

cdef extern from "Accelerate/Accelerate.h":
    ctypedef struct vImage_Buffer:
        void *data
        int width
        int height
        size_t rowBytes

    int vImagePermuteChannels_ARGB8888(
            vImage_Buffer *src, vImage_Buffer *dst, unsigned char *permuteMap,
            int flags)


def load_image_data(bytes _url):
    # load an image from the _url with CoreGraphics, and output an RGBA string.
    cdef CFURLRef url
    url = CFURLCreateFromFileSystemRepresentation(NULL, <bytes> _url, len(_url), 0)
    cdef CGImageSourceRef myImageSourceRef = CGImageSourceCreateWithURL(url, NULL)
    if not myImageSourceRef:
        CFRelease(url)
        raise ValueError('No image to load at %r' % _url)
    cdef CGImageRef myImageRef = CGImageSourceCreateImageAtIndex (myImageSourceRef, 0, NULL)
    cdef size_t width = CGImageGetWidth(myImageRef)
    cdef size_t height = CGImageGetHeight(myImageRef)
    cdef CGRect rect = CGRectMake(0, 0, width, height)
    cdef CGColorSpaceRef space = CGColorSpaceCreateDeviceRGB()
    cdef vImage_Buffer src
    cdef vImage_Buffer dest
    dest.height = src.height = height
    dest.width = src.width = width
    dest.rowBytes = src.rowBytes = width * 4
    src.data = calloc(width * 4, height)
    dest.data = calloc(width * 4, height)


    # endianness:  kCGBitmapByteOrder32Little = (2 << 12)
    # (2 << 12) | kCGImageAlphaPremultipliedLast)
    cdef CGContextRef myBitmapContext = CGBitmapContextCreate(
            src.data, width, height, 8, width * 4, space,
            kCGBitmapByteOrder32Host | kCGImageAlphaNoneSkipFirst)

    CGContextSetBlendMode(myBitmapContext, kCGBlendModeCopy)
    CGContextDrawImage(myBitmapContext, rect, myImageRef)

    # convert to RGBA using Accelerate framework
    cdef unsigned char *pmap = [2, 1, 0, 3]
    vImagePermuteChannels_ARGB8888(&src, &dest, pmap, 0)

    # get a python string
    r_data = (<char *>dest.data)[:width * height * 4]

    # release everything
    CFRelease(url)
    CGImageRelease(<CGImageRef>myImageSourceRef)
    CFRelease(myImageRef)
    CGContextRelease(myBitmapContext)
    CGColorSpaceRelease(space)
    free(src.data)
    free(dest.data)

    return (width, height, 'rgba', r_data)

def save_image_rgba(filename, width, height, data, flipped):
    # compatibility, could be removed i guess
    save_image(filename, width, height, 'rgba', data, flipped)

def save_image(filename, width, height, fmt, data, flipped):
    # save a RGBA string into filename using CoreGraphics

    # FIXME only png output are accepted.
    # the day we want to support another output format, we need to adapt the
    # ctype variable: "public.png" is not a name, but a domain that represent
    # the type of the output file. So we need to map the extension of the
    # filename into a CoreGraphics image domain type.

    fileformat = 'public.png'
    if filename.endswith('.png'):
        fileformat = 'public.png'
    if filename.endswith('.jpg') or filename.endswith('.jpeg'):
        fileformat = 'public.jpeg'

    cdef char *source = NULL
    if type(data) is array:
        data = data.tostring()
    source = <bytes>data[:len(data)]

    cdef int fmt_length = 3
    if fmt == 'rgba':
        fmt_length = 4
    cdef char *pixels = <char *>malloc(int(width * height * fmt_length))
    memcpy(pixels, <void *>source, int(width * height * fmt_length))

    cdef CGColorSpaceRef colorSpace = CGColorSpaceCreateDeviceRGB()
    cdef CGContextRef bitmapContext = CGBitmapContextCreate(
        pixels, width, height,
        8, # bitsPerComponent
        fmt_length * width, # bytesPerRow
        colorSpace,
        kCGImageAlphaNoneSkipLast)

    cdef CGImageRef cgImage = CGBitmapContextCreateImage(bitmapContext)
    cdef char *cfilename = <char *><bytes>filename

    cdef CFStringRef sfilename = CFStringCreateWithCString(NULL,
            cfilename, kCFStringEncodingUTF8)
    cdef CFURLRef url = CFURLCreateWithFileSystemPath(NULL,
            sfilename, kCFURLPOSIXPathStyle, 0)
    cdef CFStringRef ctype = CFStringCreateWithCString(NULL,
            fileformat, kCFStringEncodingUTF8)

    cdef CGImageDestinationRef dest = CGImageDestinationCreateWithURL(url,
            ctype, 1, NULL)

    # copy the image into a transformed context
    cdef CGContextRef flippedContext
    cdef CGImageRef newImageRef

    if flipped:
        flippedContext = CGBitmapContextCreate(
                                    NULL, width, height,
                                    8, # bitsPerComponent
                                    fmt_length * width, # bytesPerRow
                                    colorSpace,
                                    kCGImageAlphaNoneSkipLast)

        CGContextConcatCTM(flippedContext, CGAffineTransformMake(1.0, 0.0, 
                                                                0.0, -1.0, 
                                                                0.0, height))

        CGContextDrawImage(flippedContext, 
                            CGRectMake(0, 0, width, height), 
                            cgImage)

        newImageRef = CGBitmapContextCreateImage(flippedContext)
        CGImageDestinationAddImage(dest, newImageRef, NULL)
        CGImageDestinationFinalize(dest)
        CFRelease(newImageRef)
        CFRelease(flippedContext)
    else:
        CGImageDestinationAddImage(dest, cgImage, NULL)
        CGImageDestinationFinalize(dest)
            
    #Release everything
    CFRelease(cgImage)
    CFRelease(bitmapContext)
    CFRelease(colorSpace)
    free(pixels)

class ImageLoaderImageIO(ImageLoaderBase):
    '''Image loader based on ImageIO MacOSX Framework
    '''

    @staticmethod
    def extensions():
        # FIXME check which one are available on osx
        return ('bmp', 'bufr', 'cur', 'dcx', 'fits', 'fl', 'fpx', 'gbr',
                'gd', 'gif', 'grib', 'hdf5', 'ico', 'im', 'imt', 'iptc',
                'jpeg', 'jpg', 'jpe', 'mcidas', 'mic', 'mpeg', 'msp',
                'pcd', 'pcx', 'pixar', 'png', 'ppm', 'psd', 'sgi',
                'spider', 'tga', 'tiff', 'wal', 'wmf', 'xbm', 'xpm',
                'xv')

    def load(self, filename):
        # FIXME: if the filename is unicode, the loader is failing.
        ret = load_image_data(str(filename))
        if ret is None:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise Exception('Unable to load image')
        w, h, imgtype, data = ret
        return [ImageData(w, h, imgtype, data, source=filename)]

    @staticmethod
    def can_save():
        return True

    @staticmethod
    def save(filename, width, height, fmt, pixels, flipped=False):
        save_image(filename, width, height, fmt, pixels, flipped)
        return True

# register
ImageLoader.register(ImageLoaderImageIO)

