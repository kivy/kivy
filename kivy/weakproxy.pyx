"""
Weak Proxy
==========

In order to allow garbage collection, the weak proxy provides
`weak references <https://en.wikipedia.org/wiki/Weak_reference>`_ to objects.
It effectively enhances the
`weakref.proxy <https://docs.python.org/2/library/weakref.html#weakref.proxy>`_
by adding comparison support.
"""

include "include/config.pxi"
import weakref
import operator


cdef class WeakProxy(object):
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

    @property
    def __class__(self):
        return self.__ref__().__class__

    def __dir__(self):
        r = self.__ref()
        if not r:
            return []
        return dir(r)

    def __reversed__(self):
        return reversed(self.__ref__())

    def __round__(self):
        return round(self.__ref__())

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

    if not PY3:
        def __bool__(self):
            return bool(self.__ref__())

    def __add__(self, other):
        return self.__ref__() + other

    def __sub__(self, other):
        return self.__ref__() - other

    def __mul__(self, other):
        return self.__ref__() * other

    def __div__(self, other):
        return operator.div(self.__ref__(), other)

    def __truediv__(self, other):
        return operator.truediv(self.__ref__(), other)

    def __floordiv__(self, other):
        return self.__ref__() // other

    def __mod__(self, other):
        return self.__ref__() % other

    def __divmod__(self, other):
        return divmod(self.__ref__(), other)

    def __pow__(self, other, modulo):
        return pow(self.__ref__(), other, modulo)

    def __lshift__(self, other):
        return self.__ref__() << other

    def __rshift__(self, other):
        return self.__ref__() >> other

    def __and__(self, other):
        return self.__ref__() & other

    def __xor__(self, other):
        return self.__ref__() ^ other

    def __or__(self, other):
        return self.__ref__() | other

    def __radd__(self, other):
        return other + self.__ref__()

    def __rsub__(self, other):
        return other - self.__ref__()

    def __rmul__(self, other):
        return other * self.__ref__()

    def __rdiv__(self, other):
        return operator.div(other, self.__ref__())

    def __rtruediv__(self, other):
        return operator.truediv(other, self.__ref__())

    def __rfloordiv__(self, other):
        return other // self.__ref__()

    def __rmod__(self, other):
        return other % self.__ref__()

    def __rdivmod__(self, other):
        return divmod(other, self.__ref__())

    def __rpow__(self, other, modulo):
        return pow(other, self.__ref__(), modulo)

    def __rlshift__(self, other):
        return other << self.__ref__()

    def __rrshift__(self, other):
        return other >> self.__ref__()

    def __rand__(self, other):
        return other & self.__ref__()

    def __rxor__(self, other):
        return other ^ self.__ref__()

    def __ror__(self, other):
        return other | self.__ref__()

    def __iadd__(self, other):
        r = self.__ref__()
        r += other
        self.__ref = weakref.ref(r)
        return self

    def __isub__(self, other):
        r = self.__ref__()
        r -= other
        self.__ref = weakref.ref(r)
        return self

    def __imul__(self, other):
        r = self.__ref__()
        r *= other
        self.__ref = weakref.ref(r)
        return self

    def __idiv__(self, other):
        r = operator.idiv(self.__ref__(), other)
        self.__ref = weakref.ref(r)
        return self

    def __itruediv__(self, other):
        r = operator.itruediv(self.__ref__(), other)
        self.__ref = weakref.ref(r)
        return self

    def __ifloordiv__(self, other):
        r = self.__ref__()
        r //= other
        self.__ref = weakref.ref(r)
        return self

    def __imod__(self, other):
        r = self.__ref__()
        r %= other
        self.__ref = weakref.ref(r)
        return self

    def __ipow__(self, other):
        r = self.__ref__()
        r **= other
        self.__ref = weakref.ref(r)
        return self

    def __ilshift__(self, other):
        r = self.__ref__()
        r <<= other
        self.__ref = weakref.ref(r)
        return self

    def __irshift__(self, other):
        r = self.__ref__()
        r >>= other
        self.__ref = weakref.ref(r)
        return self

    def __iand__(self, other):
        r = self.__ref__()
        r &= other
        self.__ref = weakref.ref(r)
        return self

    def __ixor__(self, other):
        r = self.__ref__()
        r ^= other
        self.__ref = weakref.ref(r)
        return self

    def __ior__(self, other):
        r = self.__ref__()
        r |= other
        self.__ref = weakref.ref(r)
        return self

    def __neg__(self):
        return -self.__ref__()

    def __pos__(self):
        return +self.__ref__()

    def __abs__(self):
        return abs(self.__ref__())

    def __invert__(self):
        return ~self.__ref__()

    def __int__(self):
        return int(self.__ref__())

    def __long__(self):
        return long(self.__ref__())

    def __float__(self):
        return float(self.__ref__())

    def __oct__(self):
        return oct(self.__ref__())

    def __hex__(self):
        return hex(self.__ref__())

    def __index__(self):
        return operator.index(self.__ref__())

    def __len__(self):
        return len(self.__ref__())

    def __contains__(self, value):
        return value in self.__ref__()

    def __getitem__(self, key):
        return self.__ref__()[key]

    def __setitem__(self, key, value):
        self.__ref__()[key] = value

    def __delitem__(self, key):
        del self.__ref__()[key]

    def __enter__(self):
        return self.__ref__().__enter__()

    def __exit__(self, *args, **kwargs):
        return self.__ref__().__exit__(*args, **kwargs)

    def __iter__(self):
        return iter(self.__ref__())

    def __bytes__(self):
        return bytes(self.__ref())

    def __str__(self):
        return str(self.__ref())

    def __unicode__(self):
        return unicode(self.__ref())

    def __repr__(self):
        return '<WeakProxy to {!r}>'.format(self.__ref())

