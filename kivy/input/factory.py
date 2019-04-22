'''
Motion Event Factory
====================

Factory of :class:`~kivy.input.motionevent.MotionEvent` providers.
'''

__all__ = ('MotionEventFactory', )


class MotionEventFactory:
    '''MotionEvent factory is a class that registers all availables input
    factories. If you create a new input factory, you need to register
    it here::

        MotionEventFactory.register('myproviderid', MyInputProvider)

    '''
    __providers__ = {}

    @staticmethod
    def register(name, classname):
        '''Register a input provider in the database'''
        MotionEventFactory.__providers__[name] = classname

    @staticmethod
    def list():
        '''Get a list of all available providers'''
        return MotionEventFactory.__providers__

    @staticmethod
    def get(name):
        '''Get a provider class from the provider id'''
        if name in MotionEventFactory.__providers__:
            return MotionEventFactory.__providers__[name]
