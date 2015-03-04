import weakref
import operator

cdef class WidgetProxy(object):
    '''Replacement for weakref.proxy to support comparisons
    '''
    cdef public object __ref

    def __init__(self, obj, destructor=None):
        self.__ref = weakref.ref(obj, destructor)

    def __ref__(self):
        r = self.__ref()
        if r is None:
            raise ReferenceError('weakly-referenced object no longer exists')
        return r

    def __getattr__(self, name):
        return getattr(self.__ref__(), name)

    def __setattr__(self, name, value):
        setattr(self.__ref__(), name, value)

    def __delattr__(self, name):
        delattr(self.__ref__(), name)

    property __class__:
        def __get__(self):
            return self.__ref__().__class__

    def __dir__(self):
        return dir(self.__ref__())

    def __hash__(self):
        return hash(self.__ref__())

    def __richcmp__(self, other, op):
        r = self.__ref__()
        if op == 0:
            return r < other
        elif op == 1:
            return r <= other
        elif op == 2:
            return r == other
        elif op == 3:
            return r != other
        elif op == 4:
            return r > other
        elif op == 5:
            return r >= other

    def __nonzero__(self):
        return bool(self.__ref__())

    def __bool__(self):
        return bool(self.__ref__())

    def __index__(self):
        return operator.index(self.__ref__())

    def __bytes__(self):
        return bytes(self.__ref__())

    def __str__(self):
        return str(self.__ref__())

    def __unicode__(self):
        return unicode(self.__ref__())

    def __repr__(self):
        return b'<WeakProxy to {!r}>'.format(self.__ref__())

