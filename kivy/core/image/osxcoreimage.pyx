from array import array
from libcpp cimport bool

ctypedef unsigned long size_t
ctypedef signed long CFIndex


cdef extern from "stdlib.h":
    void* calloc(size_t, size_t)
    size_t strlen(char *s)


cdef extern from "Python.h":
    object PyString_FromStringAndSize(char *s, Py_ssize_t len)


cdef extern from "ApplicationServices/ApplicationServices.h":
    ctypedef void *CFDictionaryRef
    ctypedef void *CGContextRef
    ctypedef void *CFStringRef

    ctypedef void *CFAttributedStringRef
    ctypedef void *CTLineRef
    CFStringRef kCTFontAttributeName
    CFStringRef kCTForegroundColorAttributeName

    CFAttributedStringRef CFAttributedStringCreate (
       void*,
       CFStringRef,
       CFDictionaryRef
    )

    CTLineRef CTLineCreateWithAttributedString(CFAttributedStringRef)
    void CGContextSetTextPosition(CGContextRef, float, float)

    ctypedef void *CGImageRef
    ctypedef void *CGColorRef
    ctypedef void *CGColorSpaceRef
    CGColorSpaceRef CGImageGetColorSpace(CGImageRef image)
    CGColorSpaceRef CGColorSpaceCreateDeviceRGB()

    CGColorRef CGColorCreate(CGColorSpaceRef, float*)

    ctypedef struct CGPoint:
       float x
       float y

    ctypedef enum CGTextDrawingMode:
        kCGTextFill,
        kCGTextStroke,
        kCGTextFillStroke,
        kCGTextInvisible,
        kCGTextFillClip,
        kCGTextStrokeClip,
        kCGTextFillStrokeClip,
        kCGTextClip

    ctypedef enum CGTextEncoding:
        kCGEncodingFontSpecific,
        kCGEncodingMacRoman

    CGPoint CGContextGetTextPosition(CGContextRef)
    void CGContextSetTextDrawingMode(CGContextRef, CGTextDrawingMode)
    void CGContextShowText(CGContextRef, char*, size_t)
    void CGContextShowTextAtPoint(CGContextRef, float, float, char*, size_t)
    void CGContextSelectFont(CGContextRef, char*, float, CGTextEncoding)
    cdef CGTextEncoding kCGEncodingMacRoman
    void CGContextSetRGBFillColor(CGContextRef, float, float, float, float)
    void CGContextSetRGBStrokeColor(CGContextRef, float, float, float, float)
    void * CGBitmapContextGetData(CGContextRef)
    size_t CGBitmapContextGetHeight(CGContextRef)
    size_t CGBitmapContextGetWidth(CGContextRef)

    ctypedef void *CFTypeRef
    ctypedef void *CFDataRef
    # XXX
    # char or int?
    unsigned char * CFDataGetBytePtr(CFDataRef)
    ctypedef void *CGDataProviderRef
    CFDataRef CGDataProviderCopyData(CGDataProviderRef)
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



    void CGContextTranslateCTM(CGContextRef, float, float)
    void CGContextScaleCTM (CGContextRef, float, float)

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

    void CGContextDrawImage(CGContextRef, CGRect, CGImageRef)

    int kCGBlendModeCopy
    void CGContextSetBlendMode(CGContextRef, int)


    ctypedef void *CFAllocatorRef

    ctypedef signed long CFIndex

    CFStringRef CFStringCreateWithCString (
       CFAllocatorRef,
       char*,
       CFIndex
    )

    ctypedef void *CTFontRef
    CTFontRef CTFontCreateWithName(CFStringRef, float, void*)

    void CTLineDraw(CTLineRef, CGContextRef)

    ctypedef void *CFURLRef
    CFURLRef CFURLCreateFromFileSystemRepresentation(CFAllocatorRef,
                                                     unsigned char *,
                                                     CFIndex,
                                                     # XXX CORRECT?
                                                     bool)

    ctypedef struct CFDictionaryKeyCallBacks:
        pass

    ctypedef struct CFDictionaryValueCallBacks:
        pass

    CFDictionaryRef CFDictionaryCreate (
       CFAllocatorRef,
       void**,
       void**,
       CFIndex,
       CFDictionaryKeyCallBacks*,
       CFDictionaryValueCallBacks*
    )

    ctypedef CFDictionaryKeyCallBacks kCFTypeDictionaryKeyCallBacks
    ctypedef CFDictionaryValueCallBacks kCFTypeDictionaryValueCallBacks
    void CGContextSetAllowsAntialiasing(CGContextRef, bool)
    void CGContextSetShouldAntialias(CGContextRef, bool)
    void CGContextSetAllowsFontSmoothing(CGContextRef, bool)
    void CGContextSetShouldSmoothFonts(CGContextRef, bool)

    void CGContextSetInterpolationQuality(CGContextRef c, int)
    void CGContextClearRect(CGContextRef, CGRect)


cdef extern from "QuartzCore/QuartzCore.h":
    ctypedef void *CGImageSourceRef
    CGImageSourceRef CGImageSourceCreateWithURL(CFURLRef,
                                                CFDictionaryRef)
    CGImageRef CGImageSourceCreateImageAtIndex(CGImageSourceRef,
                                               size_t, CFDictionaryRef)


def load_image_data(bytes _url):
    cdef CFURLRef url
    url = CFURLCreateFromFileSystemRepresentation(NULL, <bytes> _url, len(_url), 0)

    cdef CGImageSourceRef myImageSourceRef = CGImageSourceCreateWithURL(url, NULL)
    cdef CGImageRef myImageRef = CGImageSourceCreateImageAtIndex (myImageSourceRef, 0, NULL)

    cdef size_t width = CGImageGetWidth(myImageRef)
    cdef size_t height = CGImageGetHeight(myImageRef)
    cdef CGRect rect = CGRectMake(0, 0, width, height)
    cdef CGColorSpaceRef space = CGColorSpaceCreateDeviceRGB()
    cdef CGContextRef ctx = _create_context(width, height)

    # This is necessary as the image would be vertically flipped otherwise
    CGContextTranslateCTM(ctx, 0, height)
    CGContextScaleCTM(ctx, 1, -1)

#    CGContextSetBlendMode(ctx, kCGBlendModeCopy)
    CGContextDrawImage(ctx, rect, myImageRef)
#    CGContextRelease(ctx)

    r_data = PyString_FromStringAndSize(<char *> CGBitmapContextGetData(ctx),
                                        width * height * 4)

    # XXX
    # kivy doesn't like to process 'bgra' data. we swap manually to 'rgba'.
    # would be better to fix this in texture.pyx
    a = array('b', r_data)
    a[0::4], a[2::4] = a[2::4], a[0::4]
    r_data = a.tostring()
    imgtype = 'rgba'

    return (width, height, imgtype, r_data)


cdef char* toCharPtr(string):
    bstring = string.encode('UTF-8')
    return <char*> bstring


cdef class Label:

    cdef CGContextRef ctx
    cdef bytes font
    cdef int pointsize

    def __init__(self, int w, int h, bytes font, int pointsize):
        self.ctx = _create_context(w, h)
        self.font = <bytes> font
        self.pointsize = pointsize

    def draw_at_pos(self, txt, x, y):
        CGContextSelectFont(self.ctx, self.font, self.pointsize,
            kCGEncodingMacRoman)
        CGContextSetTextDrawingMode(self.ctx, kCGTextFill)

        CGContextSetRGBFillColor(self.ctx, 1, 1, 1, 1)
#        cdef char* text = toCharPtr(unicode(txt))
        CGContextShowTextAtPoint(self.ctx, x, y, txt, len(txt))

    def get_image_data(self):
        cdef void *data = CGBitmapContextGetData(self.ctx)
        cdef int w = CGBitmapContextGetWidth(self.ctx)
        cdef int h = CGBitmapContextGetHeight(self.ctx)
#        CGContextRelease(self.ctx)

        r_data = PyString_FromStringAndSize(<char *> data, w * h * 4)

        # XXX
        # kivy doesn't like to process 'bgra' data. we swap manually to 'rgba'.
        # would be better to fix this in texture.pyx
        a = array('b', r_data)
        a[0::4], a[2::4] = a[2::4], a[0::4]
        r_data = a.tostring()
        imgtype = 'rgba'

        return (w, h, imgtype, r_data)


cdef CGContextRef _create_context(int w, int h):
    cdef CGRect rect = CGRectMake(0., 0., w, h)
    cdef void *data = calloc(w * 4, h)
    cdef CGColorSpaceRef space = CGColorSpaceCreateDeviceRGB()
    cdef CGContextRef ctx = CGBitmapContextCreate(data, w, h, 8, w*4, space,
                        kCGBitmapByteOrder32Host |
                        kCGImageAlphaPremultipliedFirst)

    CGContextClearRect(ctx, CGRectMake(0, 0, w, h))
    CGContextSetBlendMode(ctx, kCGBlendModeCopy)
    CGContextSetAllowsAntialiasing(ctx, True)
    CGContextSetAllowsFontSmoothing(ctx, True)
    CGContextSetShouldSmoothFonts(ctx, True)
    CGContextSetShouldAntialias(ctx, True)
    CGContextSetInterpolationQuality(ctx, 3)
    return ctx
