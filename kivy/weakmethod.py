'''
Weak Method
===========

:class:`WeakMethod` is used in Clock class to prevent the clock from taking
memory if the object is deleted. Check examples/core/clock_method.py for more
information.

This WeakMethod class is taken from the recipe
http://code.activestate.com/recipes/81253/, based on the nicodemus version.
(thanks to him !)
'''

import weakref
import sys

if sys.version > '3':

    class WeakMethod:
        '''Implementation of weakref for function and bounded method.
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
            original function if refers just to a function or unbound
            method.
            Returns None if the original object doesn't exist
            '''
            if self.proxy:
                return getattr(self.proxy, self.method_name)
            return self.method

        def is_dead(self):
            '''Returns True if the referenced callable was a bound method and
            the instance no longer exists. Otherwise, return False.
            '''
            return self.proxy is not None and not bool(dir(self.proxy))

        def __repr__(self):
            return '<WeakMethod proxy={} method={} method_name={}>'.format(
                    self.proxy, self.method, self.method_name)

else:

    import new

    class WeakMethod(object):
        '''Implementation of weakref for function and bounded method.
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
            original function if refers just to a function or unbound
            method.
            Returns None if the original object doesn't exist
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
                return type(self) is type(other) and self() == other()
            except:
                return False

        def __ne__(self, other):
            return not self == other

