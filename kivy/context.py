'''
Context
=======

.. versionadded:: 1.8.0

.. warning::

    This is experimental and subject to change as long as this warning notice
    is present.

Kivy have few "global" instances that is used directly by many piece of the
framework: `Cache`, `Builder`, `Clock`.

TODO: document this module.

'''

__all__ = ('Context', 'ProxyContext', 'register_context', 'get_current_context')

_contexts = {}
_default_context = None
_context_stack = []


class ProxyContext(object):

    __slots__ = ['_obj']

    def __init__(self, obj):
        object.__init__(self)
        object.__setattr__(self, '_obj', obj)

    def __getattribute__(self, name):
        return getattr(object.__getattribute__(self, '_obj'), name)

    def __delattr__(self, name):
        delattr(object.__getattribute__(self, '_obj'), name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, '_obj'), name, value)

    def __bool__(self):
        return bool(object.__getattribute__(self, '_obj'))

    def __str__(self):
        return str(object.__getattribute__(self, '_obj'))

    def __repr__(self):
        return repr(object.__getattribute__(self, '_obj'))


class Context(dict):

    def __init__(self, init=False):
        dict.__init__(self)
        self.sandbox = None
        if not init:
            return

        for name in _contexts:
            context = _contexts[name]
            instance = context['cls'](*context['args'], **context['kwargs'])
            self[name] = instance

    def push(self):
        _context_stack.append(self)
        for name, instance in self.items():
            object.__setattr__(_contexts[name]['proxy'], '_obj', instance)

    def pop(self):
        # After poping context from stack. Update proxy's _obj with
        # instances in current context
        _context_stack.pop(-1)
        for name, instance in get_current_context().items():
            object.__setattr__(_contexts[name]['proxy'], '_obj', instance)


def register_context(name, cls, *args, **kwargs):
    '''Register a new context
    '''
    instance = cls(*args, **kwargs)
    proxy = ProxyContext(instance)
    _contexts[name] = {
        'cls': cls,
        'args': args,
        'kwargs': kwargs,
        'proxy': proxy}
    _default_context[name] = instance
    return proxy

    
def get_current_context():
    '''Return the current context
    '''
    if not _context_stack:
        return _default_context
    return _context_stack[-1]

_default_context = Context(init=False)
