'''
Touch Factory: Factory of touch providers.
'''

__all__ = ('TouchFactory', )

class TouchFactory:
    '''Touch factory is a class who register all availables input factories.
    If you create a new input factory, don't forget to register it ::

        TouchFactory.register('myproviderid', MyInputProvider)

    '''
    __providers__ = {}

    @staticmethod
    def register(name, classname):
        '''Register a input provider in the database'''
        TouchFactory.__providers__[name] = classname

    @staticmethod
    def list():
        '''Get a list of all providers availables'''
        return TouchFactory.__providers__

    @staticmethod
    def get(name):
        '''Get a provider class from provider id'''
        if name in TouchFactory.__providers__:
            return TouchFactory.__providers__[name]
        return None
