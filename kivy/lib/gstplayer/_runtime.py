'''
Finding the GStreamer runtime for :mod:`kivy.lib.gstplayer`.

Pure Python, so the lookup can be tested without GStreamer. The order is:

* ``KIVY_GSTREAMER_ROOT``, when set: a GStreamer prefix (or the directory
  holding the libraries themselves).
* Linux: the normal shared-library search (``libgstreamer-1.0.so.0`` from
  the distro).
* Windows: the official ``gstreamer-libs`` wheel, then the official
  installer (its ``GSTREAMER_1_0_ROOT_*`` variable), then ``PATH``.

This is an internal module.
'''

import os
import sys
from collections import namedtuple
from glob import glob
from os.path import dirname, isdir, isfile, join

__all__ = ('Runtime', 'find_runtime', 'prepare_environment')

Runtime = namedtuple('Runtime', 'directory source environment dll_dirs')
Runtime.__doc__ = '''Where GStreamer will be loaded from.

``directory`` holds libgstreamer, or is None for the platform's normal
search. ``environment`` is a mapping of variables to set before
initialization, ``dll_dirs`` the Windows DLL directories to register.'''

WINDOWS_CORE = ('gstreamer-1.0-0.dll', 'libgstreamer-1.0-0.dll')
LINUX_CORE = 'libgstreamer-1.0.so.0'

# Variables of the wheel's environment that GStreamer and GLib read.
# GIO_EXTRA_MODULES carries the TLS backend (gioopenssl): without it every
# https:// URI fails with "Internal data stream error".
WHEEL_VARIABLES = (
    'PATH', 'GST_PLUGIN_PATH_1_0', 'GST_PLUGIN_SYSTEM_PATH_1_0',
    'GST_PLUGIN_SCANNER_1_0', 'GST_REGISTRY_1_0', 'GIO_EXTRA_MODULES',
    'XDG_DATA_DIRS', 'XDG_CONFIG_DIRS')

# Single-path variables: never prepended to a value the user already set.
SINGLE_PATH_VARIABLES = ('GST_REGISTRY_1_0', 'GST_PLUGIN_SCANNER_1_0')

INSTALLER_VARIABLES = (
    'GSTREAMER_1_0_ROOT_MSVC_X86_64', 'GSTREAMER_1_0_ROOT_X86_64',
    'GSTREAMER_1_0_ROOT_MINGW_X86_64')

_dll_handles = []


def _windows_has_core(d):
    return any(isfile(join(d, name)) for name in WINDOWS_CORE)


def _root_candidates(root, platform):
    if platform == 'win32':
        return [join(root, 'bin'), root]
    dirs = [root, join(root, 'lib'), join(root, 'lib64')]
    dirs += sorted(glob(join(root, 'lib', '*-linux-*')))
    return dirs


def _from_root(root, platform):
    has_core = _windows_has_core if platform == 'win32' else \
        (lambda d: isfile(join(d, LINUX_CORE)))
    for d in _root_candidates(root, platform):
        if has_core(d):
            return d
    return None


def _from_wheel():
    try:
        import gstreamer_libs
    except ImportError:
        return None
    d = join(dirname(gstreamer_libs.__file__), 'bin')
    if not _windows_has_core(d):
        return None
    try:
        env, dll_dirs = gstreamer_libs.gstreamer_env()
    except Exception:
        # gstreamer-plugins missing: libraries without plugins can't play
        # anything, so this isn't a usable runtime.
        return None
    env = {k: env[k] for k in WHEEL_VARIABLES if k in env}
    if sys.prefix == sys.base_prefix:
        # Outside a venv the wheels use one registry file in %TEMP% per
        # Python version, shared by every app: two bundled apps (or two
        # installs) would keep invalidating each other's plugin scan. Use a
        # file per GStreamer installation instead.
        env['GST_REGISTRY_1_0'] = registry_path(d)
    return Runtime(d, 'gstreamer-libs wheel', env,
                   [p for p in dll_dirs.split(os.pathsep) if p])


def registry_path(gst_dir):
    '''A GStreamer registry file for the installation in `gst_dir`, under
    Kivy's home directory (or the temporary directory without one).'''
    import hashlib
    import sysconfig
    import tempfile
    try:
        from kivy import kivy_home_dir
    except ImportError:
        kivy_home_dir = None
    base = kivy_home_dir or tempfile.gettempdir()
    key = hashlib.sha1(
        os.path.normcase(os.path.abspath(gst_dir)).encode('utf-8')
    ).hexdigest()[:12]
    return os.path.join(base, 'gstreamer', 'registry-{}-{}.bin'.format(
        sysconfig.get_platform(), key))


def find_runtime(environ=None, platform=None):
    '''Return the :class:`Runtime` to load. Never raises: when nothing is
    found the loader reports the missing library.'''
    environ = os.environ if environ is None else environ
    platform = sys.platform if platform is None else platform
    root = environ.get('KIVY_GSTREAMER_ROOT')
    if root:
        d = _from_root(root, platform)
        source = 'KIVY_GSTREAMER_ROOT={}'.format(root)
        if d is None:
            return Runtime(root, source, {}, [])
        return Runtime(d, source, {}, [d] if platform == 'win32' else [])
    if platform != 'win32':
        return Runtime(None, 'system', {}, [])

    found = _from_wheel()
    if found is not None:
        return found
    for var in INSTALLER_VARIABLES:
        r = environ.get(var)
        if r and _windows_has_core(join(r, 'bin')):
            d = join(r, 'bin')
            return Runtime(d, '{}={}'.format(var, r), {}, [d])
    for d in environ.get('PATH', '').split(os.pathsep):
        if d and isdir(d) and _windows_has_core(d):
            return Runtime(d, 'PATH', {}, [d])
    return Runtime(None, 'not found', {}, [])


def merged_environment(runtime, environ):
    '''The variables to change in `environ` before ``gst_init``: the
    runtime's own environment, minus single-path values the user set.'''
    out = {}
    for key, value in runtime.environment.items():
        if key in SINGLE_PATH_VARIABLES and environ.get(key):
            continue
        if environ.get(key) != value:
            out[key] = value
    if runtime.dll_dirs and sys.platform == 'win32':
        # Plugins are loaded by GLib with the normal search, which reads
        # PATH, not the directories registered with os.add_dll_directory.
        path = out.get('PATH', environ.get('PATH', ''))
        parts = path.split(os.pathsep) if path else []
        missing = [d for d in runtime.dll_dirs
                   if os.path.normcase(d) not in
                   {os.path.normcase(p) for p in parts}]
        if missing:
            out['PATH'] = os.pathsep.join(missing + parts)
    return out


def prepare_environment(runtime):
    '''Register DLL directories and set GStreamer's variables. Must run
    before the libraries are opened.'''
    if sys.platform == 'win32':
        for d in runtime.dll_dirs:
            if isdir(d):
                try:
                    _dll_handles.append(os.add_dll_directory(d))
                except OSError:
                    pass
    os.environ.update(merged_environment(runtime, os.environ))
