from array import array
from libcpp cimport bool

ctypedef unsigned long size_t
ctypedef signed long CFIndex


cdef extern from "stdlib.h":
    void* calloc(size_t, size_t)


cdef extern from "Python.h":
    object PyString_FromStringAndSize(char *s, Py_ssize_t len)


cdef extern from "ApplicationServices/ApplicationServices.h":
    ctypedef void *CFDataRef
    # XXX
    # char or int?
    unsigned char * CFDataGetBytePtr(CFDataRef)
    ctypedef void *CGDataProviderRef
    CFDataRef CGDataProviderCopyData(CGDataProviderRef)
    ctypedef void *CGImageRef
    CGDataProviderRef CGImageGetDataProvider(CGImageRef)
    # guessing these, because of no wifi:
    size_t CGImageGetWidth(CGImageRef)
    size_t CGImageGetHeight(CGImageRef)
    size_t CGImageGetBitsPerPixel(CGImageRef)
    int CGImageGetAlphaInfo(CGImageRef)
    int kCGImageAlphaNone
    int kCGImageAlphaNoneSkipLast
    int kCGImageAlphaNoneSkipFirst
    int kCGImageAlphaFirst
    int kCGImageAlphaLast
    int kCGImageAlphaPremultipliedLast
    int kCGImageAlphaPremultipliedFirst
    int kCGBitmapByteOrder32Host

    ctypedef void *CGColorSpaceRef
    CGColorSpaceRef CGImageGetColorSpace(CGImageRef image)


    CGColorSpaceRef CGColorSpaceCreateDeviceRGB()

    ctypedef void *CGContextRef

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

    CGContextRef CGBitmapContextCreate(
       void *data,
       size_t width,
       size_t height,
       size_t bitsPerComponent,
       size_t bytesPerRow,
       CGColorSpaceRef colorspace,
       unsigned int bitmapInfo
    )

    #void CGContextSetBlendMode (CGContextRef, int)
    void CGContextDrawImage(CGContextRef, CGRect, CGImageRef)

    int kCGBlendModeCopy
    void CGContextSetBlendMode(CGContextRef, int)


cdef extern from "CoreFoundation/CFBase.h":
    ctypedef void *CFAllocatorRef


#cdef extern from "CoreFoundation/CFData.h":

#cdef extern from "CoreGraphics/CGDataProvider.h":
#cdef extern from "QuartzCore/QuartzCore.h":


cdef extern from "CoreFoundation/CFURL.h":
    ctypedef void *CFURLRef
    # Not in the snippet, but I deem necessary:
    #
    # CFURLRef CFURLCreateFromFileSystemRepresentation (
    #    CFAllocatorRef allocator,
    #    const UInt8 *buffer,
    #    CFIndex bufLen,
    #    Boolean isDirectory
    # );
    CFURLRef CFURLCreateFromFileSystemRepresentation(CFAllocatorRef,
                                                     unsigned char *,
                                                     CFIndex,
                                                     # XXX CORRECT?
                                                     bool)


cdef extern from "CoreFoundation/CFDictionary.h":
    ctypedef void *CFDictionaryRef


#cdef extern from "CoreGraphics/CGImage.h":
#cdef extern from "QuartzCore/QuartzCore.h":

#cdef extern from "ImageIO/CGImageSource.h":
cdef extern from "QuartzCore/QuartzCore.h":
    ctypedef void *CGImageSourceRef
    CGImageSourceRef CGImageSourceCreateWithURL(CFURLRef,
                                                CFDictionaryRef)
    CGImageRef CGImageSourceCreateImageAtIndex(CGImageSourceRef,
                                               size_t, CFDictionaryRef)


def load_raw_image_data(bytes _url):
    raise RuntimeError("wrong function")
    cdef CFURLRef url
    url = CFURLCreateFromFileSystemRepresentation(NULL, <bytes> _url, len(_url), 0)

    cdef CGImageSourceRef myImageSourceRef
    # or maybe: UIImage* uiImage = [UIImage imageWithContentsOfFile:fullPath];
    # see iphone3d book
    myImageSourceRef = CGImageSourceCreateWithURL(url, NULL)
    if myImageSourceRef == NULL:
        print 'myImageSourceRef is NULL'
        return None

    cdef CGImageRef myImageRef
    myImageRef = CGImageSourceCreateImageAtIndex(myImageSourceRef, 0, NULL)
    if myImageRef == NULL:
        print 'myImageRef is NULL'
        return None

    cdef int width = CGImageGetWidth(myImageRef)
    cdef int height = CGImageGetHeight(myImageRef)
    cdef int alphainfo = CGImageGetAlphaInfo(myImageRef)
    #cdef int hasAlpha = alphainfo not in (kCGImageAlphaNone,
    #                                      kCGImageAlphaNoneSkipLast,
    #                                      kCGImageAlphaNoneSkipFirst)
    cdef int bits = CGImageGetBitsPerPixel(myImageRef)
    print 'bits:', bits, '=='*80

    typesize = 4
    imgtype = 'rgba'
    if alphainfo == kCGImageAlphaNoneSkipFirst:
        imgtype = 'argb'
        typesize = 4
        raise RuntimeError("fork")
    elif alphainfo == kCGImageAlphaNoneSkipLast:
        imgtype = 'rgba'
        typesize = 4

    # correctly detect the image type !!!
    #imgtype = 'rgb'
    #typesize = 3
    #if hasAlpha > 0:
    #    imgtype = 'rgba'
    #    typesize = 4

    cdef CFDataRef data
    data = CGDataProviderCopyData(CGImageGetDataProvider(myImageRef))

    r_data = PyString_FromStringAndSize(<char *>CFDataGetBytePtr(data),
                                        width * height * typesize)

    # XXX clean image object

    return (width, height, imgtype, r_data)


def load_image_data(bytes _url):
    cdef CFURLRef url
    url = CFURLCreateFromFileSystemRepresentation(NULL, <bytes> _url, len(_url), 0)

    cdef CGImageSourceRef myImageSourceRef = CGImageSourceCreateWithURL(url, NULL)
    cdef CGImageRef myImageRef = CGImageSourceCreateImageAtIndex (myImageSourceRef, 0, NULL)

    cdef size_t width = CGImageGetWidth(myImageRef)
    cdef size_t height = CGImageGetHeight(myImageRef)
    cdef CGRect rect = CGRectMake(0, 0, width, height)
    cdef void * myData = calloc(width * 4, height)
    cdef CGColorSpaceRef space = CGColorSpaceCreateDeviceRGB()
    cdef CGContextRef myBitmapContext = CGBitmapContextCreate(myData,
                                                         width, height, 8,
                                                         width*4, space,
                                                         # endianness:  kCGBitmapByteOrder32Little = (2 << 12)
                                                         #(2 << 12) | kCGImageAlphaPremultipliedLast)
                                                         kCGBitmapByteOrder32Host
                                                         |
                                                         # XXX first or last? in
                                                         # the docs they use
                                                         # first
                                                         kCGImageAlphaNoneSkipFirst)
    CGContextSetBlendMode(myBitmapContext, kCGBlendModeCopy)
    CGContextDrawImage(myBitmapContext, rect, myImageRef)
    #CGContextRelease(myBitmapContext)

    r_data = PyString_FromStringAndSize(<char *> myData, width * height * 4)

    # XXX
    # kivy doesn't like to process 'bgra' data. we swap manually to 'rgba'.
    # would be better to fix this in texture.pyx
    a = array('b', r_data)
    a[0::4], a[2::4] = a[2::4], a[0::4]
    r_data = a.tostring()
    imgtype = 'rgba'

    return (width, height, imgtype, r_data)


#
# bool hasAlpha = CGImageGetAlphaInfo(cgImage) != kCGImageAlphaNone; CGColorSpaceRef colorSpace = CGImageGetColorSpace(cgImage); switch (CGColorSpaceGetModel(colorSpace)) {
# case kCGColorSpaceModelMonochrome: description.Format =
# hasAlpha ? TextureFormatGrayAlpha : TextureFormatGray; break;
# case kCGColorSpaceModelRGB: description.Format =
# Texture Formats and Types
# |    189
# }
# hasAlpha ? TextureFormatRgba : TextureFormatRgb; break;
# default: assert(!"Unsupported color space."); break;
# } description.BitsPerComponent = CGImageGetBitsPerComponent(cgImage);
# return description;
#
#

