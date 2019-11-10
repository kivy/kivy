'''
Weak Method
===========

The :class:`WeakMethod` is used by the :class:`~kivy.clock.Clock` class to
allow references to a bound method that permits the associated object to
be garbage collected. Please refer to
`examples/core/clock_method.py` for more information.

This WeakMethod class is taken from the recipe
http://code.activestate.com/recipes/81253/, based on the nicodemus version.
Many thanks nicodemus!
'''

import weakref
import sys

if sys.version > '3':

    class WeakMethod:
        '''Implementation of a
        `weakref <http://en.wikipedia.org/wiki/Weak_reference>`_
        for functions and bound methods.
        '''
        def __init__(self, method):
            self.method = None
            self.method_name = None
            try:
                if method.__self__ is not None:
                    self.method_name = method.__func__.__name__
                    self.proxy = weakref.proxy(method.__self__)
                else:
                    self.method = method
                    self.proxy = None
            except AttributeError:
                self.method = method
                self.proxy = None

        def __call__(self):
            '''Return a new bound-method like the original, or the
            original function if it was just a function or unbound
            method.
            Returns None if the original object doesn't exist.
            '''
            try:
                if self.proxy:
                    return getattr(self.proxy, self.method_name)
            except ReferenceError:
                pass
            return self.method

        def is_dead(self):
            '''Returns True if the referenced callable was a bound method and
            the instance no longer exists. Otherwise, return False.
            '''
            try:
                return self.proxy is not None and not bool(dir(self.proxy))
            except ReferenceError:
                return True

        def __eq__(self, other):
            try:
                if type(self) is not type(other):
                    return False
                s = self()
                return s is not None and s == other()
            except:
                return False

        def __repr__(self):
            return '<WeakMethod proxy={} method={} method_name={}>'.format(
                   self.proxy, self.method, self.method_name)

else:

    import new

    class WeakMethod(object):
        '''Implementation of a
        `weakref <http://en.wikipedia.org/wiki/Weak_reference>`_
        for functions and bound methods.
        '''

        def __init__(self, method):
            try:
                if method.__self__ is not None:
                    # bound method
                    self._obj = weakref.ref(method.im_self)
                else:
                    # unbound method
                    self._obj = None
                self._func = method.im_func
                self._class = method.im_class
            except AttributeError:
                # not a method
                self._obj = None
                self._func = method
                self._class = None

        def __call__(self):
            '''Return a new bound-method like the original, or the
            original function if it was just a function or unbound
            method.
            Returns None if the original object doesn't exist.
            '''
            if self.is_dead():
                return None
            if self._obj is not None:
                return new.instancemethod(self._func, self._obj(), self._class)
            else:
                # we don't have an instance: return just the function
                return self._func

        def is_dead(self):
            '''Returns True if the referenced callable was a bound method and
            the instance no longer exists. Otherwise, return False.
            '''
            return self._obj is not None and self._obj() is None

        def __eq__(self, other):
            try:
                if type(self) is not type(other):
                    return False
                s = self()
                return s is not None and s == other()
            except:
                return False

        def __ne__(self, other):
            return not self == other
