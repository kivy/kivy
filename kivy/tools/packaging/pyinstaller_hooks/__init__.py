'''
Pyinstaller hooks
=================

Module that exports pyinstaller related methods and parameters.

Hooks
-----

PyInstaller comes with a default hook for kivy that lists the indirectly
imported modules that pyinstaller would not find on its own using
:func:`get_deps_all`. :func:`hookspath` returns the path to an alternate kivy
hook, ``kivy/tools/packaging/pyinstaller_hooks/kivy-hook.py`` that does not
add these dependencies to its list of hidden imports and they have to be
explicitly included instead.

One can overwrite the default hook by providing on the command line the
``--additional-hooks-dir=HOOKSPATH`` option. Because although the default
hook will still run, the `important global variables
<https://pythonhosted.org/PyInstaller/#hook-global-variables>`_, e.g.
``excludedimports`` and ``hiddenimports`` will be overwritten by the
new hook, if set there.

Additionally, one can add a hook to be run after the default hook by
passing e.g. ``hookspath=[HOOKSPATH]`` to the ``Analysis`` class. In both
cases, ``HOOKSPATH`` is the path to a directory containing a file named
``hook-kivy.py`` that is the pyinstaller hook for kivy to be processed
after the default hook.

hiddenimports
-------------

When a module is imported indirectly, e.g. with ``__import__``, pyinstaller
won't know about it and the module has to be added through ``hiddenimports``.

``hiddenimports`` and other hook variables can be specified within a hook as
described above. Also, these variable can be passed to ``Analysis`` and their
values are then appended to the hook's values for these variables.

Most of kivy's core modules, e.g. video are imported indirectly and therefore
need to be added in hiddenimports. The default PyInstaller hook adds all the
providers. To overwrite, a modified kivy-hook similar to the default hook, such
as :func:`hookspath` that only imports the desired modules can be added. One
then uses :func:`get_deps_minimal` or :func:`get_deps_all` to get the list of
modules and adds them manually in a modified hook or passes them to
``Analysis`` in the spec file.

Hook generator
--------------

:mod:`pyinstaller_hooks` includes a tool to generate a hook which lists
all the provider modules in a list so that one can manually comment out
the providers not to be included. To use, do::

    python -m kivy.tools.packaging.pyinstaller_hooks hook filename

``filename`` is the name and path of the hook file to create. If ``filename``
is not provided the hook is printed to the terminal.
'''

import os
import sys
import pkgutil
import logging
from os.path import dirname, join
import importlib

import kivy
import kivy.deps
from kivy.factory import Factory

from os import environ
if 'KIVY_DOC' not in environ:
    from PyInstaller.compat import modname_tkinter
    from PyInstaller.utils.hooks import collect_submodules

    curdir = dirname(__file__)

    kivy_modules = [
        'xml.etree.cElementTree',
        'kivy.core.gl'
    ] + collect_submodules('kivy.graphics')
    '''List of kivy modules that are always needed as hiddenimports of
    pyinstaller.
    '''

    excludedimports = [modname_tkinter, '_tkinter', 'twisted']
    '''List of excludedimports that should always be excluded from
    pyinstaller.
    '''

    datas = [
        (kivy.kivy_data_dir,
         os.path.join('kivy_install', os.path.basename(kivy.kivy_data_dir))),
        (kivy.kivy_modules_dir,
         os.path.join('kivy_install', os.path.basename(kivy.kivy_modules_dir)))
    ]
'''List of datas to be included by pyinstaller.
'''


def runtime_hooks():
    '''Returns a list with the runtime hooks for kivy. It can be used with
    ``runtime_hooks=runtime_hooks()`` in the spec file. Pyinstaller comes
    preinstalled with this hook.
    '''
    return [join(curdir, 'pyi_rth_kivy.py')]


def hookspath():
    '''Returns a list with the directory that contains the alternate (not
    the default included with pyinstaller) pyinstaller hook for kivy,
    ``kivy/tools/packaging/pyinstaller_hooks/kivy-hook.py``. It is
    typically used with ``hookspath=hookspath()`` in the spec
    file.

    The default pyinstaller hook returns all the core providers used using
    :func:`get_deps_minimal` to add to its list of hidden imports. This
    alternate hook only included the essential modules and leaves the core
    providers to be included additionally with :func:`get_deps_minimal`
    or :func:`get_deps_all`.
    '''
    return [curdir]


def get_hooks():
    '''Returns the dict for the spec ``hookspath`` and ``runtime_hooks``
    values.
    '''
    return {'hookspath': hookspath(), 'runtime_hooks': runtime_hooks()}


def get_deps_minimal(exclude_ignored=True, **kwargs):
    '''Returns Kivy hidden modules as well as excluded modules to be used
    with ``Analysis``.

    The function takes core modules as keyword arguments and their value
    indicates which of the providers to include/exclude from the compiled app.

    The possible keyword names are ``audio, camera, clipboard, image, spelling,
    text, video, and window``. Their values can be:

        ``True``: Include current provider
            The providers imported when the core module is
            loaded on this system are added to hidden imports. This is the
            default if the keyword name is not specified.
        ``None``: Exclude
            Don't return this core module at all.
        ``A string or list of strings``: Providers to include
            Each string is the name of a provider for this module to be
            included.

    For example, ``get_deps_minimal(video=None, window=True,
    audio=['gstplayer', 'ffpyplayer'], spelling='enchant')`` will exclude all
    the video providers, will include the gstreamer and ffpyplayer providers
    for audio, will include the enchant provider for spelling, and will use the
    current default provider for ``window``.

    ``exclude_ignored``, if ``True`` (the default), if the value for a core
    library is ``None``, then if ``exclude_ignored`` is True, not only will the
    library not be included in the hiddenimports but it'll also added to the
    excluded imports to prevent it being included accidentally by pyinstaller.

    :returns:

        A dict with two keys, ``hiddenimports`` and ``excludes``. Their values
        are a list of the corresponding modules to include/exclude. This can
        be passed directly to `Analysis`` with e.g. ::

            a = Analysis(['..\\kivy\\examples\\demo\\touchtracer\\main.py'],
                        ...
                         hookspath=hookspath(),
                         runtime_hooks=[],
                         win_no_prefer_redirects=False,
                         win_private_assemblies=False,
                         cipher=block_cipher,
                         **get_deps_minimal(video=None, audio=None))
    '''
    core_mods = ['audio', 'camera', 'clipboard', 'image', 'spelling', 'text',
                 'video', 'window']
    mods = kivy_modules[:]
    excludes = excludedimports[:]

    for mod_name, val in kwargs.items():
        if mod_name not in core_mods:
            raise KeyError('{} not found in {}'.format(mod_name, core_mods))

        full_name = 'kivy.core.{}'.format(mod_name)
        if not val:
            core_mods.remove(mod_name)
            if exclude_ignored:
                excludes.extend(collect_submodules(full_name))
            continue
        if val is True:
            continue
        core_mods.remove(mod_name)

        mods.append(full_name)
        single_mod = False
        if sys.version < '3.0':
            # Mod name could potentially be any basestring subclass
            if isinstance(val, basestring):
                single_mod = True
                mods.append('kivy.core.{0}.{0}_{1}'.format(mod_name, val))
        else:
            # There is no `basestring` in Py3
            if isinstance(val, (str, bytes)):
                single_mod = True
                mods.append('kivy.core.{0}.{0}_{1}'.format(mod_name, val))
        if not single_mod:
            for v in val:
                mods.append('kivy.core.{0}.{0}_{1}'.format(mod_name, v))

    for mod_name in core_mods:  # process remaining default modules
        full_name = 'kivy.core.{}'.format(mod_name)
        mods.append(full_name)
        m = importlib.import_module(full_name)

        if mod_name == 'clipboard' and m.CutBuffer:
            mods.append(m.CutBuffer.__module__)
        if hasattr(m, mod_name.capitalize()):  # e.g. video -> Video
            val = getattr(m, mod_name.capitalize())
            if val:
                mods.append(getattr(val, '__module__'))

        if hasattr(m, 'libs_loaded') and m.libs_loaded:
            for name in m.libs_loaded:
                mods.append('kivy.core.{}.{}'.format(mod_name, name))

    mods = sorted(set(mods))

    if exclude_ignored and not any('gstplayer' in m for m in mods):
        excludes.append('kivy.lib.gstplayer')
    return {'hiddenimports': mods, 'excludes': excludes}


def get_deps_all():
    '''Similar to :func:`get_deps_minimal`, but this returns all the
    kivy modules that can indirectly imported. Which includes all
    the possible kivy providers.

    This can be used to get a list of all the possible providers
    which can then manually be included/excluded by commenting out elements
    in the list instead of passing on all the items. See module description.

    :returns:

        A dict with two keys, ``hiddenimports`` and ``excludes``. Their values
        are a list of the corresponding modules to include/exclude. This can
        be passed directly to `Analysis`` with e.g. ::

            a = Analysis(['..\\kivy\\examples\\demo\\touchtracer\\main.py'],
                        ...
                         **get_deps_all())
    '''
    return {
        'hiddenimports': sorted(set(kivy_modules +
                                    collect_submodules('kivy.core'))),
        'excludes': []}


def get_factory_modules():
    '''Returns a list of all the modules registered in the kivy factory.
    '''
    mods = [x.get('module', None) for x in Factory.classes.values()]
    return [m for m in mods if m]


def add_dep_paths():
    '''Should be called by the hook. It adds the paths with the binary
    dependencies to the system path so that pyinstaller can find the binaries
    during its crawling stage.
    '''
    paths = []
    for importer, modname, ispkg in pkgutil.iter_modules(kivy.deps.__path__):
        if not ispkg:
            continue
        try:
            mod = importer.find_module(modname).load_module(modname)
        except ImportError as e:
            logging.warn("deps: Error importing dependency: {}".format(str(e)))
            continue

        if hasattr(mod, 'dep_bins'):
            paths.extend(mod.dep_bins)
    sys.path.extend(paths)
