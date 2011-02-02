'''
Motion Event Factory
====================

Factory of :class:`~kivy.input.motionevent.MotionEvent` providers.
'''

__all__ = ('MotionEventFactory', )


class MotionEventFactory:
    '''MotionEvent factory is a class who register all availables input
    factories.  If you create a new input factory, don't forget to register it
    ::

        MotionEventFactory.register('myproviderid', MyInputProvider)

    '''
    __providers__ = {}

    @staticmethod
    def register(name, classname):
        '''Register a input provider in the database'''
        MotionEventFactory.__providers__[name] = classname

    @staticmethod
    def list():
        '''Get a list of all providers availables'''
        return MotionEventFactory.__providers__

    @staticmethod
    def get(name):
        '''Get a provider class from provider id'''
        if name in MotionEventFactory.__providers__:
            return MotionEventFactory.__providers__[name]
        return None
