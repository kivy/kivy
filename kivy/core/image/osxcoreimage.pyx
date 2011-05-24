from libcpp cimport bool

ctypedef unsigned long size_t
ctypedef signed long CFIndex

cdef extern from "Python.h":
    object PyString_FromStringAndSize(char *s, Py_ssize_t len)


cdef extern from "CoreFoundation/CFBase.h":
    ctypedef void *CFAllocatorRef


cdef extern from "CoreFoundation/CFData.h":
    ctypedef void *CFDataRef
    # XXX
    # char or int?
    unsigned char * CFDataGetBytePtr(CFDataRef)

cdef extern from "CoreGraphics/CGDataProvider.h":
    ctypedef void *CGDataProviderRef
    CFDataRef CGDataProviderCopyData(CGDataProviderRef)


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


cdef extern from "CoreGraphics/CGImage.h":
    ctypedef void *CGImageRef
    CGDataProviderRef CGImageGetDataProvider(CGImageRef)
    # guessing these, because of no wifi:
    int CGImageGetWidth(CGImageRef)
    int CGImageGetHeight(CGImageRef)
    int CGImageGetAlphaInfo(CGImageRef)
    int kCGImageAlphaNone


cdef extern from "ImageIO/CGImageSource.h":
    ctypedef void *CGImageSourceRef
    CGImageSourceRef CGImageSourceCreateWithURL(CFURLRef,
                                                CFDictionaryRef)
    CGImageRef CGImageSourceCreateImageAtIndex(CGImageSourceRef,
                                               size_t, CFDictionaryRef)


def load_raw_image_data(bytes _url):
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
    myImageRef = CGImageSourceCreateImageAtIndex (myImageSourceRef, 0, NULL)
    if myImageRef == NULL:
        print 'myImageRef is NULL'
        return None

    cdef int width = CGImageGetWidth(myImageRef)
    cdef int height = CGImageGetHeight(myImageRef)
    cdef int hasAlpha = CGImageGetAlphaInfo(myImageRef) != kCGImageAlphaNone

    # correctly detect the image type !!!
    imgtype = 'rgb'
    typesize = 3
    if hasAlpha > 0:
        imgtype = 'rgba'
        typesize = 4

    cdef CFDataRef data
    data = CGDataProviderCopyData(CGImageGetDataProvider(myImageRef))

    r_data = PyString_FromStringAndSize(<char *>CFDataGetBytePtr(data),
                    width * height * typesize)

    # XXX clean image object

    print 'Image:', _url, width, height, imgtype
    return (width, height, imgtype, r_data)

#
# bool hasAlpha = CGImageGetAlphaInfo(cgImage) != kCGImageAlphaNone; CGColorSpaceRef colorSpace = CGImageGetColorSpace(cgImage); switch (CGColorSpaceGetModel(colorSpace)) {
# case kCGColorSpaceModelMonochrome: description.Format =
# hasAlpha ? TextureFormatGrayAlpha : TextureFormatGray; break;
# case kCGColorSpaceModelRGB: description.Format =
# Texture Formats and Types
# |	189
# }
# hasAlpha ? TextureFormatRgba : TextureFormatRgb; break;
# default: assert(!"Unsupported color space."); break;
# } description.BitsPerComponent = CGImageGetBitsPerComponent(cgImage);
# return description;
#
#
