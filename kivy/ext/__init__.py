'''
Extension Support
=================

Sometimes your application requires functionality that is beyond the scope of
what Kivy can deliver. In those cases it is necessary to resort to external
software libraries. Given the richness of the Python ecosystem, there is already
a great number of software libraries that you can simply import and use right
away.

For some third-party libraries, it's not as easy as that though. Some libraries
require special *wrappers* to be written for them in order to be compatible with
Kivy.
Some libraries might even need to be patched so that they can be used (e.g. if
they open their own OpenGL context to draw in and don't support proper offscreen
rendering). On those occasions it is often possible to patch the library in
question and to provide a Python wrapper around it that is compatible with Kivy.
Sticking with this example, you can't just use the wrapper with a 'normal'
installation of the library because the patch would be missing.

That is where Kivy extensions come in handy. A Kivy extension represents a
single third-party library that is provided in a way so that it can simply be
downloaded as a single file, put in a special directory and then offers the
functionality of the wrapped library to Kivy applications.
These extensions will not pollute the global Python environment (as they might
be unusable on their own after potential patches have been applied) because they
reside in special directories for Kivy that are not accessed by Python by
default.

Kivy extensions are provided as ``*.kex`` files. They are really just zip files,
but you must not unzip them yourself. Kivy will do that for you as soon as it's
appropriate to do so.

.. warning::

    Again, do not try to unzip ``*.kex`` files on your own. While unzipping will
    work, Kivy will not be able to load the extension and will simply ignore it.

With Kivy's extension system, your application can use specially packaged
third-party libraries in a backwards compatible way (by specifying the version
that you require) even if the actual third-party library does not guarantee
backwards-compatibility. There will be no breakage if newer versions are
installed (as a properly suited old version will still be used). For more
information about that behaviour, consider the documentation of the
:func:`~kivy.ext.load` function.

If you want to provide an extension on your own, there is a helper script that
sets up the initial extension folder structure that Kivy requires for
extensions. It can be found at kivy/tools/extensions/make-kivyext.py
'''

import imp
from glob import glob
from os import listdir, mkdir, sep, environ
from os.path import join, isdir, exists, dirname
from zipfile import ZipFile
from shutil import move

from kivy.logger import Logger

if not 'KIVY_DOC' in environ:
    from kivy import kivy_userexts_dir, kivy_exts_dir

    # The paths where extensions can be put as a .zip file by the user
    EXTENSION_PATHS = [kivy_exts_dir, kivy_userexts_dir]

NEED_UNZIP = True


def load(extname, version):
    # XXX platform check?
    '''Use this function to tell Kivy to load a specific version of the given
    Extension. This is different from kivy's require() in that it will always
    use the exact same major version you specify even if a newer (major)
    version is available. This is because we cannot make the same
    backwards-compatibility guarantee that we make with Kivy for third-party
    extensions. You will still get fixes and optimizations that don't break
    backwards compatibility via minor version upgrades of the extension.

    The function will then return the loaded module as a Python module object
    and you can bind it to a name of your choosing. This prevents clashes with
    modules with the same name that might be installed in a system directory.

    Usage example for this function::

        from kivy.ext import load
        myextension = load('myextension', (2, 1))
        # You can now use myextension as if you had done ``import myextension``,
        # but with the added benefit of using the proper version.

    :Parameters:
        `extname`: str
            The exact name of the extension that you want to use.
        `version`: two-tuple of ints
            A tuple of the form (major, minor), where major and minor are ints
            that specify the major and minor version number for the extension,
            e.g. (1, 2) would be akin to 1.2. It is important to note that
            between minor versions, backwards compatibility is guaranteed, but
            between major versions it is not. I.e. if you change your extension
            in a backwards incompatible way, increase the major version number
            (and reset the minor to 0). If you just do a bug fix or add an
            optional, backwards-compatible feature, you can just increase the
            minor version number. If the application then requires version (1,
            2), every version starting with that version number will be ok and
            by default the latest version will be choosen.
            The two ints major and minor can both be in range(0, infinity).
    '''
    #
    global NEED_UNZIP
    if NEED_UNZIP:
        unzip_extensions()
        NEED_UNZIP = False

    # Find the one path that best satisfies the specified criteria, i.e. same
    # extension name, same major version number, maximum available minor version
    # number but at least the same as the specified minor version number.
    majmatch = extname + '_' + str(version[0]) + '.*'
    best = None
    bestpath = None
    globs = []
    for epath in EXTENSION_PATHS:
        globs.extend(glob(join(epath, majmatch)))
    for p in globs:
        # minmatch
        cur = int(p.rsplit('.')[-1])
        if best is None or cur > best:
            best = cur
            bestpath = p
    if best >= version[1]:
        searchpath = [bestpath]
    else:
        # Didn't find a matching extension
        raise ImportError("No extension found that satisfies your criteria: " +
                          "('%s', %s)" % (extname, version))

    file, pathname, desc = imp.find_module(extname, searchpath)
    msg = 'Extension found for ' + repr(extname) + ':\n\t' + str(file) + \
          '\n\t' + str(pathname) + '\n\t' + str(desc)
    Logger.debug(msg)

    try:
        mod = imp.load_module(extname, file, pathname, desc)
    finally:
        if file:
            file.close()

    return mod


def _is_valid_ext_name(name):
    try:
        extname, version = name.split('_')
        major, minor = version.split('.')
        major, minor = int(major), int(minor)
    except:
        print("The name '%s' is not a valid extension name." % name)
        return False
    return (extname, (major, minor))


def unzip_extensions():
    '''Unzips Kivy extensions. Internal usage only: don't use it yourself unless
    you know what you're doing and really want to trigger installation of new
    extensions.

    For your file to be recognized as an extension, it has to fulfil a few
    requirements:

     * We require that the file has the ``*.kex`` extension to make the
       distinction between a Kivy extension and an ordinary zip file clear.

     * We require that the ``*.kex`` extension files be put into any of the
       directories listed in EXTENSION_PATHS which is normally
       ~/.kivy/extensions and extensions/ inside kivy's base directory. We do
       not look for extensions on sys.path or elsewhere in the system.

     * We require that the Kivy extension is zipped in a way so that Python's
       zipfile module can extract it properly.

     * We require that the extension internally obeys the common Kivy extension
       format, which looks like this::

            |-- myextension/
                |-- __init__.py
                |-- data/

       The ``__init__.py`` file is the main entrypoint to the extension. All
       names that should be usable when the extension is loaded need to be
       exported (i.e. made available) in the namespace of that file.

       How the extension accesses the code of the library that it wraps (be it
       pure Python or binary code) is up to the extension. For example there
       could be another Python module adjacent to the ``__init__.py`` file from
       which the ``__init__.py`` file imports the usable names that it wants to
       expose.

     * We require that the version of the extension be specified in the
       ``setup.py`` file that is created by the Kivy extension wizard and that
       the version specification format as explained in :func:`~kivy.ext.load`
       be used.
    '''
    Logger.debug('Searching for new extension in %s' % EXTENSION_PATHS)

    for epath in EXTENSION_PATHS:
        if not isdir(epath):
            try:
                mkdir(epath)
            except OSError:
                continue
            files = []
        else:
            files = listdir(epath)
        for zipfn in glob(join(epath, '*.kex')):
            # ZipFile only became a context manager in python 2.7...
            # with ZipFile(zipfn, 'r') as zipf:
            # fail = is_invalid = False
            try:
                zipf = ZipFile(zipfn)
                # /path/to/MyExt-1.0.linux-x86_64.zip
                # /path/to/MyExt-1.0.macos-10.6-x86_64.zip
                extname = zipfn.rsplit(sep)[-1][:-4]
                # MyExt-1.0.linux-x86_64
                # MyExt-1.0.macosx-10.6-x86_64
                t = extname.split('-')
                extname = t[0]
                version = '-'.join(t[1:])
                version = '.'.join(version.split('.')[:2])

                extdir = extname + '_' + version

                # is_invalid = not _is_valid_ext_name(extdir)
            except IOError:
                Logger.warn("Malformed zipfile '%s'! Skipping it." % zipfn)
                continue
            except Exception as e:
                Logger.warn("Malformed extension '%s'! Skipping it." % zipfn)
                zipf.close()
                continue

            already_unzipped = False
            if extdir in files:
                Logger.trace(("Extension '%s' has already been " % extname) +
                              "extracted manually, just moving the zip.")
                already_unzipped = True

            # Filter the namelist of zipfile to take only the members that start
            # with the extension name (MyExt/...)
            members = [x for x in zipf.namelist()
                       if x.startswith(extname + '/')]

            if not already_unzipped:
                # Unzip the extension
                try:
                    cache_directories = []
                    mkdir(join(epath, extdir))
                    # I know that there is zipf.extract() and zipf.extractall(),
                    # but on OSX, Python 2.6 is the default and in that version,
                    # both methods have a bug. Fixed in 2.7 only. So use this
                    # workaround until apple upgrades its python. See
                    # http://bugs.python.org/issue4710
                    for member in members:
                        # In zipfiles, folders always end with '/' regardless
                        # of the OS
                        mempath = join(epath, extdir, member)
                        directory = dirname(mempath)
                        if not directory in cache_directories:
                            cache_directories.append(directory)
                            if not exists(directory):
                                mkdir(join(epath, extdir, directory))
                        with open(join(epath, extdir, member), 'wb') as fd:
                            fd.write(zipf.read(member))
                except Exception as e:
                    # Catch any error, e.g. non-writable directory, etc.
                    Logger.error("Failed installing extension " +
                                 "'%s' %s." % (extname, e))
                    return
                finally:
                    zipf.close()
                Logger.info("Installed extension '%s'." % extname)

            # Move the zip out of the way so that it won't be installed again
            # The user can just delete it, but we'll keep it around in case the
            # user needs it again.
            consumed_dir = join(epath, '_consumed_zips')
            if not isdir(consumed_dir):
                mkdir(consumed_dir)
            move(zipfn, consumed_dir)
