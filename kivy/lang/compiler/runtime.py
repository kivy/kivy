'''
Kv Compiler Runtime Functions
==============================

Exports functions used by the compiled code at runtime.
'''

import sys
import os
import inspect
import functools
import os.path
import importlib.machinery

__all__ = (
    'clear_kvc_cache', 'get_kvc_filename', 'load_kvc_from_file',
    'save_kvc_to_file', 'add_graphics_callback', 'process_graphics_callbacks')

_graphics_callback_linked_list = None

_kvc_cache = {}

_kvc_path = os.environ.get('KIVY_KVC_PATH', None)
if _kvc_path is not None:
    _kvc_path = os.path.abspath(_kvc_path)
_kvc_freeze = bool(int(os.environ.get('KIVY_KVC_FREEZE', 0)))

# check all the attrs of the compiled function that need to be set to match the
# original function's values. If the sets are not equal, it means we may need
# to set more values if python changed
assert set(functools.WRAPPER_ASSIGNMENTS) == {
    '__module__', '__name__', '__qualname__', '__doc__', '__annotations__'}


def clear_kvc_cache():
    '''Clears the cache that stores all the compiled functions that has been
    imported.
    '''
    _kvc_cache.clear()


def add_graphics_callback(item, largs):
    '''
    Add the item to be added to the linked list of canvas instructions to be
    executed with all the canvas instructions by
    :func:`process_graphics_callbacks`. If it's already scheduled, it is not
    added again.

    This is a internal function, with non-public API.

    :param item: The item scheduled.
    :param largs: The largs of the first time the callback was scheduled. It
        gets forwarded to the callback when executed.
    '''
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
    '''
    Process all the canvas callbacks that has been scheduled by
    :func:`add_graphics_callback`.

    This is a internal function, with non-public API.
    '''
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


def get_kvc_filename(func, flags=''):
    '''Returns the `kvc` file associated with the function. Specifically,
    it's the filename where the function's compiled kv code is stored.

    The file may not exist, if it has not been compiled yet.'''
    func_name = func.__qualname__
    flags = '-{}'.format(flags) if flags else ''
    mod_name = inspect.getmodule(func).__name__

    # generated filename is mod_name-func_qualname-flags.kvc
    kv_fname = '{}-{}{}.kvc'.format(mod_name, func_name, flags)

    if not _kvc_path:
        # generated filename is py_filename-func_qualname-flags.kvc
        func_filname = inspect.getfile(func)
        kv_dir = os.path.join(os.path.dirname(func_filname), '__kvcache__')
        kv_path = os.path.join(kv_dir, kv_fname)
    else:
        kv_path = os.path.join(_kvc_path, kv_fname)

    return kv_path


def get_cache_kvc_filenames():
    return [mod.__file__ for mod, _ in _kvc_cache.values()]


def load_kvc_from_file(
        func, target_func_name=None, flags='', compile_flags=()):
    '''
    Loads the compiled kv function from the kvc file associated with the
    function.

    This is a internal function, with non-public API.

    :param func: The original function, whose compiled code should be loaded.
    :param target_func_name: The name of the function as stored in the kvc
        file.
        Typically, it's the function's name.
    :param flags: Any arch flags used when saving the kvc file. This is stored
        in the kvc filename.
    :param compile_flags: Any compiler flags used when compiling the kvc file.
        These are stored within the compiled code, not in the filename.
    :return: The compiled function object.
    '''
    if target_func_name is None:
        target_func_name = func.__name__
    mod_name = inspect.getmodule(func).__name__
    func_name = func.__qualname__
    compile_flags_s = repr(compile_flags)
    key = mod_name, func_name, flags, compile_flags_s

    if key in _kvc_cache:
        return _kvc_cache[key]

    # any and all os.xxx are super slow, so fallback on last resort
    kv_fname = get_kvc_filename(func, flags)

    if not os.path.exists(kv_fname):
        if _kvc_freeze:
            raise ValueError(
                'Could not find compiled file, {}, for function {}, yet '
                'KIVY_KVC_FREEZE was set so we cannot generate a compiled '
                'file'.format(kv_fname, func))
        return None, None
    elif not _kvc_freeze and os.stat(
            inspect.getfile(func)).st_mtime >= os.stat(kv_fname).st_mtime:
        # if frozen, we don't care about file ages
        return None, None

    mod_name = '__kv{}'.format(len(_kvc_cache))
    loader = importlib.machinery.SourceFileLoader(mod_name, kv_fname)
    mod = loader.load_module()
    if compile_flags_s != mod.__kv_kvc_compile_flags:
        del sys.modules[mod_name]

        if _kvc_freeze:
            raise ValueError(
                'Compiled file, {}, for function {}, does not match flags yet '
                'KIVY_KVC_FREEZE was set so we cannot generate a new compiled '
                'file ({} != {})'.format(
                    kv_fname, func, compile_flags_s,
                    mod.__kv_kvc_compile_flags))
        return None, None
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


def save_kvc_to_file(func, src_code, flags='', compile_flags=()):
    '''
    Saves the compiled source code generated from the function to a kvc file.

    This is a internal function, with non-public API.

    :param func: The function object from which the compiled code was
        generated.
    :param src_code: The compiled source code as string.
    :param flags: Any arch flags used when saving the kvc file. This is stored
        in the kvc filename.
    :param compile_flags: Any compiler flags used when compiling the kvc file.
        These are stored within the compiled code, not in the filename.
    '''
    kv_fname = get_kvc_filename(func, flags)
    head = os.path.dirname(kv_fname)

    if not os.path.exists(head):
        os.mkdir(head)

    with open(kv_fname, 'w') as fh:
        fh.write('__kv_kvc_compile_flags = {}\n\n'.format(
            repr(repr(compile_flags))))
        fh.write(src_code)
