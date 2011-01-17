'''
Motion Event Provider
=====================

Abstract class for a implement a :class:`~kivy.input.motionevent.MotionEvent`
provider. The implementation must support the
:func:`~MotionEventProvider.start`, :func:`~MotionEventProvider.stop` and
:func:`~MotionEventProvider.update` methods.
'''

__all__ = ('MotionEventProvider', )


class MotionEventProvider(object):
    '''Base class for a provider.
    '''

    def __init__(self, device, args):
        self.device = device
        if self.__class__ == MotionEventProvider:
            raise NotImplementedError('class MotionEventProvider is abstract')

    def start(self):
        '''Start the provider. This method is automatically called when the
        application is started, and if the configuration use the current
        provider.
        '''
        pass

    def stop(self):
        '''Stop the provider
        '''
        pass

    def update(self, dispatch_fn):
        '''Update the provider, and dispatch all the new touch event though the
        `dispatch_fn` argument.
        '''
        pass

