'''
Context
=======

Kivy have few "global" instance that is used directly by many piece of the
framework: `Cache`, `Builder`, `Clock`.

'''

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


_contexts = {}
_default_context = None
_context_stack = []

class Context(dict):
    def __init__(self, init=False):
        dict.__init__(self)
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
        context = _context_stack.pop(-1)
        for name, instance in context.items():
            object.__setattr__(_contexts[name]['proxy'], '_obj', instance)


def register_context(name, cls, *args, **kwargs):
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
    return _context_stack[-1]

_default_context = Context(init=False)
