'''
Kivy Extension Importer
~~~~~~~~~~~~~~~~~~~~~~~

Import extensions!
'''

import sys
import imp
from glob import glob
from os import listdir, mkdir, sep
from os.path import join, isdir, exists
from zipfile import ZipFile
from shutil import move

from kivy import kivy_userexts_dir, kivy_exts_dir
from kivy.logger import Logger


# The paths where extensions can be put as a .zip file by the user
EXTENSION_PATHS = [kivy_exts_dir, kivy_userexts_dir]

# def _compatibility_check(v1, v2):
#     '''Internal use only.
#     Checks compatibility between two extension versions. If you want to know
#     what we defined as 'compatible' in this context, check the documentation of
#     the load() function.
#
#     Checks if v2 is backwards compatible to v1, i.e. v2 must have the same major
#     version number and the same or a higher minor version number.
#     '''
#     maj1, min1 = v1
#     maj2, min2 = v2
#     if maj1 != maj2:
#         return False
#     if min1 < min2:
#         return False
#     return True


# XXX platform check?
def load(extname, version):
    '''Use this function to tell Kivy to load a specific version of the given
    Extension. This is different from kivy's require() in that it will always
    use the exact version you specify, even if a newer (major) version is
    available. This is because we cannot make the same backwards-compatibility
    guarantee that we make with Kivy for third-party extensions.

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
    msg = 'Extension found for' + str(extname) + ':\n\t' + str(file) + \
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
    except Exception, e:
        print "The name '%s' is not a valid extension name." % name
        return False
    return (extname, (major, minor))


def _unzip_extensions():
    '''Unzips Kivy extensions. Internal usage only; Don't use it yourself.
    Called by kivy/__init__.py
    '''
    for epath in EXTENSION_PATHS:
        if not isdir(epath):
            mkdir(epath)
            files = []
        else:
            files = listdir(epath)
        for zipfn in glob(join(epath, '*.zip')):
            # ZipFile only became a context manager in python 2.7...
            # with ZipFile(zipfn, 'r') as zipf:
            fail = is_invalid = False
            try:
                zipf = ZipFile(zipfn)
                # /path/to/MyExt-1.0.linux-x86_64.zip
                extname = zipfn.rsplit(sep)[-1][:-4]
                # MyExt-1.0.linux-x86_64
                extname = '.'.join(extname.split('.')[:-1])
                # MyExt-1.0
                extname, version = extname.split('-')
                extdir = extname + '_' + version
                is_invalid = not _is_valid_ext_name(extdir)
            except IOError:
                Logger.warn("Malformed zipfile '%s'! Skipping it." % zipfn)
                continue
            except Exception, e:
                Logger.warn("Malformed extension '%s'! Skipping it." % zipfn)
                zipf.close()
                continue

            already_unzipped = False
            if extdir in files:
                Logger.trace(("Extension '%s' has already been " % extname) + \
                              "extracted manually, just moving the zip.")
                already_unzipped = True

            members = zipf.namelist()

            def get_root_member(zipf):
                root = None
                multiple = False
                for m1 in members:
                    for m2 in members:
                        if not m2.startswith(m1):
                            break
                    else:
                        if root != None:
                            multiple = True
                        root = m1
                if not root or multiple:
                    # There either is no root or there is more than one root.
                    # We require only one root, so the extension is malformed.
                    Logger.warn("Malformed extension '%s'! Skipping it." % extname)
                    return
                # return root name without the trailing slash
                return root[:-1]

            root = get_root_member(zipf)
            if not root:
                # Skip this extension as we told the user
                continue

            if not already_unzipped:
                # Unzip the extension
                try:
                    mkdir(join(epath, extdir))
                    # I know that there is zipf.extract() and zipf.extractall(), but on
                    # OSX, Python 2.6 is the default and in that version, both methods
                    # have a bug. Fixed in 2.7 only. So use this workaround until apple
                    # upgrades its python. See http://bugs.python.org/issue4710
                    for member in members:
                        # In zipfiles, folders always end with '/' regardless of the OS
                        mempath = join(epath, extdir, member)
                        if member.endswith('/') and not exists(mempath):
                            mkdir(join(epath, extdir, member[:-1]))
                        else:
                            with open(join(epath, extdir, member), 'wb') as memberfd:
                                memberfd.write(zipf.read(member))
                except Exception, e:
                    # Catch any error, e.g. non-writable directory, etc.
                    Logger.error("Failed installing extension " + \
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


# def _setup_extension_importer():
#     '''Internal function to set up the ExtensionImporter.
#     Do not use it.
#     '''
#     sys.meta_path.append(ExtensionImporter())
# 
# 
# class ExtensionImporter(object):
#     def find_module(self, fullname, path=None):
#         Logger.trace('ExtensionImporter.find_module():', fullname, path)
# 
#         # We only want to import something that is a Kivy extension:
#         if not fullname.startswith('kivy.ext.'):
#             return None
# 
#         # XXX: Should we make sure that if extroot has already been imported, it won't
#         # try to import any kivy.ex.$extroot.* again?
#         extroot = fullname.split('.')[2]
# 
#         try:
#             Logger.trace('Trying to find', `extroot`, 'in', EXTENSION_PATHS)
#             file, pathname, desc = imp.find_module(extroot, EXTENSION_PATHS)
#         except ImportError:
#             return None
# 
#         return ExtensionLoader(extroot, file, pathname, desc)
# 
# 
# class ExtensionLoader(object):
#     def __init__(self, extroot, file, pathname, desc):
#         self.extroot = extroot
#         self.file = file
#         self.pathname = pathname
#         self.desc = desc
#         Logger.trace('Found:', '\n\t', self.file, '\n\t', self.pathname, '\n\t',
#             self.desc)
# 
#     def load_module(self, fullname):
#         Logger.trace('ExtensionImporter.load_module():', fullname)
# 
#         try:
#             mod = imp.load_module(self.extroot, self.file, self.pathname, self.desc)
#         finally:
#             if self.file:
#                 self.file.close()
# 
#         sys.modules[fullname] = mod
#         return mod

