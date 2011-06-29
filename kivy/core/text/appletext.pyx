cdef extern from "ApplicationServices/ApplicationServices.h":
    ctypedef struct CGSize:
        float width
        float height


cdef extern from "appletext.h":
    CGSize getStringExtents(char *_string, char *_font, int size)


cdef char* toCharPtr(string):
    bstring = string.encode('UTF-8')
    return <char*> bstring


def get_extents(string, font, size):
    size = getStringExtents(toCharPtr(string), toCharPtr(u"Helvetica"), size)
    return size['width'], size['height']

