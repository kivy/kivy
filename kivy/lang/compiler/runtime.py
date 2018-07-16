import os
import inspect
import functools
import os.path
import importlib.machinery

_graphics_callback_linked_list = None

_kvc_cache = {}

assert set(functools.WRAPPER_ASSIGNMENTS) == {
    '__module__', '__name__', '__qualname__', '__doc__', '__annotations__'}


def add_graphics_callback(item, largs):
    # it's already on the list
    if item[1] is not None:
        return

    global _graphics_callback_linked_list
    if _graphics_callback_linked_list is None:
        _graphics_callback_linked_list = item
        item[1] = largs
        item[2] = StopIteration
    else:
        item[1] = largs
        item[2] = _graphics_callback_linked_list
        _graphics_callback_linked_list = item


def process_graphics_callbacks():
    global _graphics_callback_linked_list
    next_args = _graphics_callback_linked_list
    if next_args is None:
        return

    _graphics_callback_linked_list = None

    while next_args is not StopIteration:
        # reset things first in case its somehow rescheduled by the callback
        args = next_args
        f, largs, next_args = next_args
        args[1] = args[2] = None
        f(*largs)


def load_kvc_from_file(func, target_func_name, flags=''):
    func_filname = inspect.getfile(func)
    func_name = func.__qualname__
    key = func_filname, func_name, flags

    if key in _kvc_cache:
        return _kvc_cache[key]

    head, tail = os.path.split(func_filname)
    fname_root, _ = os.path.splitext(tail)

    kv_dir = os.path.join(head, '__kvcache__')
    flags = '-{}'.format(flags) if flags else ''
    kv_fname = os.path.join(kv_dir, '{}-{}{}.kvc'.format(fname_root, func_name, flags))

    if not os.path.exists(kv_fname) or os.stat(func_filname).st_mtime >= os.stat(kv_fname).st_mtime:
        return None, None

    loader = importlib.machinery.SourceFileLoader('__kv{}'.format(len(_kvc_cache)), kv_fname)
    mod = loader.load_module()
    f = getattr(mod, target_func_name)

    for attr in functools.WRAPPER_ASSIGNMENTS:
        try:
            value = getattr(func, attr)
        except AttributeError:
            pass
        else:
            setattr(f, attr, value)

    _kvc_cache[key] = mod, f
    return _kvc_cache[key]


def save_kvc_to_file(func, src_code, flags=''):
    func_filname = inspect.getfile(func)
    head, tail = os.path.split(func_filname)
    fname_root, _ = os.path.splitext(tail)

    kv_dir = os.path.join(head, '__kvcache__')
    flags = '-{}'.format(flags) if flags else ''
    func_name = func.__qualname__
    kv_fname = os.path.join(kv_dir, '{}-{}{}.kvc'.format(fname_root, func_name, flags))

    if not os.path.exists(kv_dir):
        os.mkdir(kv_dir)

    with open(kv_fname, 'w') as fh:
        fh.write(src_code)
