from libcpp cimport bool

ctypedef unsigned long size_t
ctypedef signed long CFIndex


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
    bool CGImageGetAlphaInfo(CGImageRef)
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

    cdef CGImageRef myImageRef
    myImageRef = CGImageSourceCreateImageAtIndex (myImageSourceRef, 0, NULL)

    cdef bool hasAlpha = CGImageGetAlphaInfo(myImageRef) != kCGImageAlphaNone

    cdef CFDataRef data
    data = CGDataProviderCopyData(CGImageGetDataProvider(myImageRef))
    return <bytes> CFDataGetBytePtr(data)

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
