#
# Kivy - Cross-platform UI framework
# https://kivy.org/
#

import sys
build_examples = False
if "--build_examples" in sys.argv:
    build_examples = True
    sys.argv.remove("--build_examples")

from kivy.utils import pi_version
from copy import deepcopy
import os
from os.path import join, dirname, sep, exists, basename, isdir
from os import walk, environ, makedirs
from distutils.command.build_ext import build_ext
from distutils.version import LooseVersion
from distutils.sysconfig import get_python_inc
from collections import OrderedDict
from time import sleep
from sysconfig import get_paths
from pathlib import Path
import logging
from setuptools import setup, Extension, find_packages


if sys.version_info[0] == 2:
    logging.critical(
        'Unsupported Python version detected!: Kivy 2.0.0 and higher does not '
        'support Python 2. Please upgrade to Python 3, or downgrade Kivy to '
        '1.11.1 - the last Kivy release that still supports Python 2.')


def ver_equal(self, other):
    return self.version == other


# fix error with py3's LooseVersion comparisons
LooseVersion.__eq__ = ver_equal


def get_description():
    with open(join(dirname(__file__), 'README.md'), 'rb') as fileh:
        return fileh.read().decode("utf8").replace('\r\n', '\n')


def getoutput(cmd, env=None):
    import subprocess
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, env=env)
    p.wait()
    if p.returncode:  # if not returncode == 0
        print('WARNING: A problem occurred while running {0} (code {1})\n'
              .format(cmd, p.returncode))
        stderr_content = p.stderr.read()
        if stderr_content:
            print('{0}\n'.format(stderr_content))
        return ""
    return p.stdout.read()


def pkgconfig(*packages, **kw):
    flag_map = {'-I': 'include_dirs', '-L': 'library_dirs', '-l': 'libraries'}
    lenviron = None
    pconfig = join(sys.prefix, 'libs', 'pkgconfig')

    if isdir(pconfig):
        lenviron = environ.copy()
        lenviron['PKG_CONFIG_PATH'] = '{};{}'.format(
            environ.get('PKG_CONFIG_PATH', ''), pconfig)
    cmd = 'pkg-config --libs --cflags {}'.format(' '.join(packages))
    results = getoutput(cmd, lenviron).split()
    for token in results:
        ext = token[:2].decode('utf-8')
        flag = flag_map.get(ext)
        if not flag:
            continue
        kw.setdefault(flag, []).append(token[2:].decode('utf-8'))
    return kw


def get_isolated_env_paths():
    try:
        # sdl2_dev is installed before setup.py is run, when installing from
        # source due to pyproject.toml. However, it is installed to a
        # pip isolated env, which we need to add to compiler
        import kivy_deps.sdl2_dev as sdl2_dev
    except ImportError:
        return [], []

    root = os.path.abspath(join(sdl2_dev.__path__[0], '../../../..'))
    includes = [join(root, 'Include')] if isdir(join(root, 'Include')) else []
    libs = [join(root, 'libs')] if isdir(join(root, 'libs')) else []
    return includes, libs


# -----------------------------------------------------------------------------
# Determine on which platform we are

build_examples = build_examples or \
    os.environ.get('KIVY_BUILD_EXAMPLES', '0') == '1'

platform = sys.platform

# Detect Python for android project (http://github.com/kivy/python-for-android)
ndkplatform = environ.get('NDKPLATFORM')
if ndkplatform is not None and environ.get('LIBLINK'):
    platform = 'android'
kivy_ios_root = environ.get('KIVYIOSROOT', None)
if kivy_ios_root is not None:
    platform = 'ios'
# proprietary broadcom video core drivers
if exists('/opt/vc/include/bcm_host.h'):
    used_pi_version = pi_version
    # Force detected Raspberry Pi version for cross-builds, if needed
    if 'KIVY_RPI_VERSION' in environ:
        used_pi_version = int(environ['KIVY_RPI_VERSION'])
    # The proprietary broadcom video core drivers are not available on the
    # Raspberry Pi 4
    if (used_pi_version or 4) < 4:
        platform = 'rpi'
# use mesa video core drivers
if environ.get('VIDEOCOREMESA', None) == '1':
    platform = 'vc'
mali_paths = (
    '/usr/lib/arm-linux-gnueabihf/libMali.so',
    '/usr/lib/arm-linux-gnueabihf/mali-egl/libmali.so',
    '/usr/local/mali-egl/libmali.so')
if any((exists(path) for path in mali_paths)):
    platform = 'mali'

# Needed when cross-compiling
if environ.get('KIVY_CROSS_PLATFORM'):
    platform = environ.get('KIVY_CROSS_PLATFORM')

# -----------------------------------------------------------------------------
# Detect options
#
c_options = OrderedDict()
c_options['use_rpi'] = platform == 'rpi'
c_options['use_egl'] = False
c_options['use_opengl_es2'] = None
c_options['use_opengl_mock'] = environ.get('READTHEDOCS', None) == 'True'
c_options['use_sdl2'] = None
c_options['use_pangoft2'] = None
c_options['use_ios'] = False
c_options['use_android'] = False
c_options['use_mesagl'] = False
c_options['use_x11'] = False
c_options['use_wayland'] = False
c_options['use_gstreamer'] = None
c_options['use_avfoundation'] = platform in ['darwin', 'ios']
c_options['use_osx_frameworks'] = platform == 'darwin'
c_options['debug_gl'] = False

# Set the alpha size, this will be 0 on the Raspberry Pi and 8 on all other
# platforms, so SDL2 works without X11
c_options['kivy_sdl_gl_alpha_size'] = 8 if pi_version is None else 0

# now check if environ is changing the default values
for key in list(c_options.keys()):
    ukey = key.upper()
    if ukey in environ:
        # kivy_sdl_gl_alpha_size should be an integer, the rest are booleans
        value = int(environ[ukey])
        if key != 'kivy_sdl_gl_alpha_size':
            value = bool(value)
        print('Environ change {0} -> {1}'.format(key, value))
        c_options[key] = value

use_embed_signature = environ.get('USE_EMBEDSIGNATURE', '0') == '1'
use_embed_signature = use_embed_signature or bool(
    platform not in ('ios', 'android'))

# -----------------------------------------------------------------------------
# We want to be able to install kivy as a wheel without a dependency
# on cython, but we also want to use cython where possible as a setup
# time dependency through `pyproject.toml` if building from source.

# There are issues with using cython at all on some platforms;
# exclude them from using or declaring cython.

# This determines whether Cython specific functionality may be used.
can_use_cython = True

if platform in ('ios', 'android'):
    # NEVER use or declare cython on these platforms
    print('Not using cython on %s' % platform)
    can_use_cython = False


# -----------------------------------------------------------------------------
# Setup classes

# the build path where kivy is being compiled
src_path = build_path = dirname(__file__)
print("Current directory is: {}".format(os.getcwd()))
print("Source and initial build directory is: {}".format(src_path))

# __version__ is imported by exec, but help linter not complain
__version__ = None
with open(join(src_path, 'kivy', '_version.py'), encoding="utf-8") as f:
    exec(f.read())


class KivyBuildExt(build_ext, object):

    def __new__(cls, *a, **kw):
        # Note how this class is declared as a subclass of distutils
        # build_ext as the Cython version may not be available in the
        # environment it is initially started in. However, if Cython
        # can be used, setuptools will bring Cython into the environment
        # thus its version of build_ext will become available.
        # The reason why this is done as a __new__ rather than through a
        # factory function is because there are distutils functions that check
        # the values provided by cmdclass with issublcass, and so it would
        # result in an exception.
        # The following essentially supply a dynamically generated subclass
        # that mix in the cython version of build_ext so that the
        # functionality provided will also be executed.
        if can_use_cython:
            from Cython.Distutils import build_ext as cython_build_ext
            build_ext_cls = type(
                'KivyBuildExt', (KivyBuildExt, cython_build_ext), {})
            return super(KivyBuildExt, cls).__new__(build_ext_cls)
        else:
            return super(KivyBuildExt, cls).__new__(cls)

    def finalize_options(self):
        retval = super(KivyBuildExt, self).finalize_options()

        # Build the extensions in parallel if the options has not been set
        if hasattr(self, 'parallel') and self.parallel is None:
            # Use a maximum of 4 cores. If cpu_count returns None, then parallel
            # build will be disabled
            self.parallel = min(4, os.cpu_count() or 0)
            if self.parallel:
                print('Building extensions in parallel using {} cores'.format(
                    self.parallel))

        global build_path
        if (self.build_lib is not None and exists(self.build_lib) and
                not self.inplace):
            build_path = self.build_lib
            print("Updated build directory to: {}".format(build_path))

        return retval

    def build_extensions(self):
        # build files
        config_h_fn = ('include', 'config.h')
        config_pxi_fn = ('include', 'config.pxi')
        config_py_fn = ('setupconfig.py', )

        # generate headers
        config_h = '// Autogenerated file for Kivy C configuration\n'
        config_h += '#define __PY3 1\n'
        config_pxi = '# Autogenerated file for Kivy Cython configuration\n'
        config_pxi += 'DEF PY3 = 1\n'
        config_py = '# Autogenerated file for Kivy configuration\n'
        config_py += 'PY3 = 1\n'
        config_py += 'CYTHON_MIN = {0}\nCYTHON_MAX = {1}\n'.format(
            repr(MIN_CYTHON_STRING), repr(MAX_CYTHON_STRING))
        config_py += 'CYTHON_BAD = {0}\n'.format(repr(', '.join(map(
            str, CYTHON_UNSUPPORTED))))

        # generate content
        print('Build configuration is:')
        for opt, value in c_options.items():
            # kivy_sdl_gl_alpha_size is already an integer
            if opt != 'kivy_sdl_gl_alpha_size':
                value = int(bool(value))
            print(' * {0} = {1}'.format(opt, value))
            opt = opt.upper()
            config_h += '#define __{0} {1}\n'.format(opt, value)
            config_pxi += 'DEF {0} = {1}\n'.format(opt, value)
            config_py += '{0} = {1}\n'.format(opt, value)
        debug = bool(self.debug)
        print(' * debug = {0}'.format(debug))

        config_pxi += 'DEF DEBUG = {0}\n'.format(debug)
        config_py += 'DEBUG = {0}\n'.format(debug)
        config_pxi += 'DEF PLATFORM = "{0}"\n'.format(platform)
        config_py += 'PLATFORM = "{0}"\n'.format(platform)
        for fn, content in (
                (config_h_fn, config_h), (config_pxi_fn, config_pxi),
                (config_py_fn, config_py)):
            build_fn = expand(build_path, *fn)
            if self.update_if_changed(build_fn, content):
                print('Updated {}'.format(build_fn))
            src_fn = expand(src_path, *fn)
            if src_fn != build_fn and self.update_if_changed(src_fn, content):
                print('Updated {}'.format(src_fn))

        c = self.compiler.compiler_type
        print('Detected compiler is {}'.format(c))
        if c != 'msvc':
            for e in self.extensions:
                e.extra_link_args += ['-lm']

        super(KivyBuildExt, self).build_extensions()

    def update_if_changed(self, fn, content):
        need_update = True
        if exists(fn):
            with open(fn) as fd:
                need_update = fd.read() != content
        if need_update:
            directory_name = dirname(fn)
            if not exists(directory_name):
                makedirs(directory_name)
            with open(fn, 'w') as fd:
                fd.write(content)
        return need_update


def _check_and_fix_sdl2_mixer(f_path):
    # Between SDL_mixer 2.0.1 and 2.0.4, the included frameworks changed
    # smpeg2 have been replaced with mpg123, but there is no need to fix.
    smpeg2_path = ("{}/Versions/A/Frameworks/smpeg2.framework"
                   "/Versions/A/smpeg2").format(f_path)
    if not exists(smpeg2_path):
        return

    print("Check if SDL2_mixer smpeg2 have an @executable_path")
    rpath_from = ("@executable_path/../Frameworks/SDL2.framework"
                  "/Versions/A/SDL2")
    rpath_to = "@rpath/../../../../SDL2.framework/Versions/A/SDL2"
    output = getoutput(("otool -L '{}'").format(smpeg2_path)).decode('utf-8')
    if "@executable_path" not in output:
        return

    print("WARNING: Your SDL2_mixer version is invalid")
    print("WARNING: The smpeg2 framework embedded in SDL2_mixer contains a")
    print("WARNING: reference to @executable_path that will fail the")
    print("WARNING: execution of your application.")
    print("WARNING: We are going to change:")
    print("WARNING: from: {}".format(rpath_from))
    print("WARNING: to: {}".format(rpath_to))
    getoutput("install_name_tool -change {} {} {}".format(
        rpath_from, rpath_to, smpeg2_path))

    output = getoutput(("otool -L '{}'").format(smpeg2_path))
    if b"@executable_path" not in output:
        print("WARNING: Change successfully applied!")
        print("WARNING: You'll never see this message again.")
    else:
        print("WARNING: Unable to apply the changes, sorry.")


# -----------------------------------------------------------------------------
print("Python path is:\n{}\n".format('\n'.join(sys.path)))
# extract version (simulate doc generation, kivy will be not imported)
environ['KIVY_DOC_INCLUDE'] = '1'
import kivy

# Cython check
# on python-for-android and kivy-ios, cython usage is external
from kivy.tools.packaging.cython_cfg import get_cython_versions, get_cython_msg
CYTHON_REQUIRES_STRING, MIN_CYTHON_STRING, MAX_CYTHON_STRING, \
    CYTHON_UNSUPPORTED = get_cython_versions()
cython_min_msg, cython_max_msg, cython_unsupported_msg = get_cython_msg()

if can_use_cython:
    import Cython
    print('\nFound Cython at', Cython.__file__)

    cy_version_str = Cython.__version__
    cy_ver = LooseVersion(cy_version_str)
    print('Detected supported Cython version {}'.format(cy_version_str))

    if cy_ver < LooseVersion(MIN_CYTHON_STRING):
        print(cython_min_msg)
    elif cy_ver in CYTHON_UNSUPPORTED:
        print(cython_unsupported_msg)
    elif cy_ver > LooseVersion(MAX_CYTHON_STRING):
        print(cython_max_msg)
    sleep(1)

# extra build commands go in the cmdclass dict {'command-name': CommandClass}
# see tools.packaging.{platform}.build.py for custom build commands for
# portable packages. Also e.g. we use build_ext command from cython if its
# installed for c extensions.
from kivy.tools.packaging.factory import FactoryBuild
cmdclass = {
    'build_factory': FactoryBuild,
    'build_ext': KivyBuildExt}

try:
    # add build rules for portable packages to cmdclass
    if platform == 'win32':
        from kivy.tools.packaging.win32.build import WindowsPortableBuild
        cmdclass['build_portable'] = WindowsPortableBuild
    elif platform == 'darwin':
        from kivy.tools.packaging.osx.build import OSXPortableBuild
        cmdclass['build_portable'] = OSXPortableBuild
except ImportError:
    print('User distribution detected, avoid portable command.')

# Detect which opengl version headers to use
if platform in ('android', 'darwin', 'ios', 'rpi', 'mali', 'vc'):
    c_options['use_opengl_es2'] = True
elif c_options['use_opengl_es2'] is None:
    c_options['use_opengl_es2'] = \
        environ.get('KIVY_GRAPHICS', '').lower() == 'gles'

print('Using this graphics system: {}'.format(
    ['OpenGL', 'OpenGL ES 2'][int(c_options['use_opengl_es2'] or False)]))

# check if we are in a kivy-ios build
if platform == 'ios':
    print('Kivy-IOS project environment detect, use it.')
    print('Kivy-IOS project located at {0}'.format(kivy_ios_root))
    c_options['use_ios'] = True
    c_options['use_sdl2'] = True

elif platform == 'android':
    c_options['use_android'] = True

# detect gstreamer, only on desktop
# works if we forced the options or in autodetection
if platform not in ('ios', 'android') and (c_options['use_gstreamer']
                                           in (None, True)):
    gstreamer_valid = False
    if c_options['use_osx_frameworks'] and platform == 'darwin':
        # check the existence of frameworks
        f_path = '/Library/Frameworks/GStreamer.framework'
        if not exists(f_path):
            c_options['use_gstreamer'] = False
            print('GStreamer framework not found, fallback on pkg-config')
        else:
            print('GStreamer framework found')
            gstreamer_valid = True
            c_options['use_gstreamer'] = True
            gst_flags = {
                'extra_link_args': [
                    '-F/Library/Frameworks',
                    '-Xlinker', '-rpath',
                    '-Xlinker', '/Library/Frameworks',
                    '-Xlinker', '-headerpad',
                    '-Xlinker', '190',
                    '-framework', 'GStreamer'],
                'include_dirs': [join(f_path, 'Headers')]}
    elif platform == 'win32':
        gst_flags = pkgconfig('gstreamer-1.0')
        if 'libraries' in gst_flags:
            print('GStreamer found via pkg-config')
            gstreamer_valid = True
            c_options['use_gstreamer'] = True
        else:
            _includes = get_isolated_env_paths()[0] + [get_paths()['include']]
            for include_dir in _includes:
                if exists(join(include_dir, 'gst', 'gst.h')):
                    print('GStreamer found via gst.h')
                    gstreamer_valid = True
                    c_options['use_gstreamer'] = True
                    gst_flags = {
                        'libraries':
                            ['gstreamer-1.0', 'glib-2.0', 'gobject-2.0']}
                    break

    if not gstreamer_valid:
        # use pkg-config approach instead
        gst_flags = pkgconfig('gstreamer-1.0')
        if 'libraries' in gst_flags:
            print('GStreamer found via pkg-config')
            c_options['use_gstreamer'] = True


# detect SDL2, only on desktop and iOS, or android if explicitly enabled
# works if we forced the options or in autodetection
sdl2_flags = {}
if platform == 'win32' and c_options['use_sdl2'] is None:
    c_options['use_sdl2'] = True

if c_options['use_sdl2'] or (
        platform not in ('android',) and c_options['use_sdl2'] is None):

    sdl2_valid = False
    if c_options['use_osx_frameworks'] and platform == 'darwin':
        # check the existence of frameworks
        sdl2_frameworks_search_path = environ.get(
            "KIVY_SDL2_FRAMEWORKS_SEARCH_PATH", "/Library/Frameworks"
        )
        sdl2_valid = True
        sdl2_flags = {
            'extra_link_args': [
                '-F{}'.format(sdl2_frameworks_search_path),
                '-Xlinker', '-rpath',
                '-Xlinker', sdl2_frameworks_search_path,
                '-Xlinker', '-headerpad',
                '-Xlinker', '190'],
            'include_dirs': [],
            'extra_compile_args': ['-F{}'.format(sdl2_frameworks_search_path)]
        }
        for name in ('SDL2', 'SDL2_ttf', 'SDL2_image', 'SDL2_mixer'):
            f_path = '{}/{}.framework'.format(sdl2_frameworks_search_path, name)
            if not exists(f_path):
                print('Missing framework {}'.format(f_path))
                sdl2_valid = False
                continue
            sdl2_flags['extra_link_args'] += ['-framework', name]
            sdl2_flags['include_dirs'] += [join(f_path, 'Headers')]
            print('Found sdl2 frameworks: {}'.format(f_path))
            if name == 'SDL2_mixer':
                _check_and_fix_sdl2_mixer(f_path)

        if not sdl2_valid:
            c_options['use_sdl2'] = False
            print('SDL2 frameworks not found, fallback on pkg-config')
        else:
            c_options['use_sdl2'] = True
            print('Activate SDL2 compilation')

    if not sdl2_valid and platform != "ios":
        # use pkg-config approach instead
        sdl2_flags = pkgconfig('sdl2', 'SDL2_ttf', 'SDL2_image', 'SDL2_mixer')
        if 'libraries' in sdl2_flags:
            print('SDL2 found via pkg-config')
            c_options['use_sdl2'] = True


# -----------------------------------------------------------------------------
# declare flags

def expand(root, *args):
    return join(root, 'kivy', *args)


class CythonExtension(Extension):

    def __init__(self, *args, **kwargs):
        Extension.__init__(self, *args, **kwargs)
        self.cython_directives = {
            'c_string_encoding': 'utf-8',
            'profile': 'USE_PROFILE' in environ,
            'embedsignature': use_embed_signature,
            'language_level': 3,
            'unraisable_tracebacks': True,
        }
        # XXX with pip, setuptools is imported before distutils, and change
        # our pyx to c, then, cythonize doesn't happen. So force again our
        # sources
        self.sources = args[1]


def merge(d1, *args):
    d1 = deepcopy(d1)
    for d2 in args:
        for key, value in d2.items():
            value = deepcopy(value)
            if key in d1:
                d1[key].extend(value)
            else:
                d1[key] = value
    return d1


def determine_base_flags():
    includes, libs = get_isolated_env_paths()

    flags = {
        'libraries': [],
        'include_dirs': [join(src_path, 'kivy', 'include')] + includes,
        'library_dirs': [] + libs,
        'extra_link_args': [],
        'extra_compile_args': []}
    if c_options['use_ios']:
        sysroot = environ.get('IOSSDKROOT', environ.get('SDKROOT'))
        if not sysroot:
            raise Exception('IOSSDKROOT is not set')
        flags['include_dirs'] += [sysroot]
        flags['extra_compile_args'] += ['-isysroot', sysroot]
        flags['extra_link_args'] += ['-isysroot', sysroot]
    elif platform.startswith('freebsd'):
        flags['include_dirs'] += [join(
            environ.get('LOCALBASE', '/usr/local'), 'include')]
        flags['library_dirs'] += [join(
            environ.get('LOCALBASE', '/usr/local'), 'lib')]
    elif platform == 'darwin' and c_options['use_osx_frameworks']:
        v = os.uname()
        if v[2] >= '13.0.0':
            if 'SDKROOT' in environ:
                sysroot = join(environ['SDKROOT'], 'System/Library/Frameworks')
            else:
                # use xcode-select to search on the right Xcode path
                # XXX use the best SDK available instead of a specific one
                import platform as _platform
                xcode_dev = getoutput('xcode-select -p').splitlines()[0]
                sdk_mac_ver = '.'.join(_platform.mac_ver()[0].split('.')[:2])
                print('Xcode detected at {}, and using OS X{} sdk'.format(
                    xcode_dev, sdk_mac_ver))
                sysroot = join(
                    xcode_dev.decode('utf-8'),
                    'Platforms/MacOSX.platform/Developer/SDKs',
                    'MacOSX{}.sdk'.format(sdk_mac_ver),
                    'System/Library/Frameworks')
        else:
            sysroot = ('/System/Library/Frameworks/'
                       'ApplicationServices.framework/Frameworks')
        flags['extra_compile_args'] += ['-F%s' % sysroot]
        flags['extra_link_args'] += ['-F%s' % sysroot]
    elif platform == 'win32':
        flags['include_dirs'] += [get_python_inc(prefix=sys.prefix)]
        flags['library_dirs'] += [join(sys.prefix, "libs")]
    return flags


def determine_gl_flags():
    kivy_graphics_include = join(src_path, 'kivy', 'include')
    flags = {'include_dirs': [kivy_graphics_include], 'libraries': []}
    base_flags = {'include_dirs': [kivy_graphics_include], 'libraries': []}
    cross_sysroot = environ.get('KIVY_CROSS_SYSROOT')

    if c_options['use_opengl_mock']:
        return flags, base_flags
    if platform == 'win32':
        flags['libraries'] = ['opengl32', 'glew32']
    elif platform == 'ios':
        flags['libraries'] = ['GLESv2']
        flags['extra_link_args'] = ['-framework', 'OpenGLES']
    elif platform == 'darwin':
        flags['extra_link_args'] = ['-framework', 'OpenGL']
    elif platform.startswith('freebsd'):
        flags['libraries'] = ['GL']
    elif platform.startswith('openbsd'):
        flags['include_dirs'] = ['/usr/X11R6/include']
        flags['library_dirs'] = ['/usr/X11R6/lib']
        flags['libraries'] = ['GL']
    elif platform == 'android':
        flags['include_dirs'] = [join(ndkplatform, 'usr', 'include')]
        flags['library_dirs'] = [join(ndkplatform, 'usr', 'lib')]
        flags['libraries'] = ['GLESv2']
    elif platform == 'rpi':

        if not cross_sysroot:
            flags['include_dirs'] = [
                '/opt/vc/include',
                '/opt/vc/include/interface/vcos/pthreads',
                '/opt/vc/include/interface/vmcs_host/linux']
            flags['library_dirs'] = ['/opt/vc/lib']
            brcm_lib_files = (
                '/opt/vc/lib/libbrcmEGL.so',
                '/opt/vc/lib/libbrcmGLESv2.so')

        else:
            print("KIVY_CROSS_SYSROOT: " + cross_sysroot)
            flags['include_dirs'] = [
                cross_sysroot + '/usr/include',
                cross_sysroot + '/usr/include/interface/vcos/pthreads',
                cross_sysroot + '/usr/include/interface/vmcs_host/linux']
            flags['library_dirs'] = [cross_sysroot + '/usr/lib']
            brcm_lib_files = (
                cross_sysroot + '/usr/lib/libbrcmEGL.so',
                cross_sysroot + '/usr/lib/libbrcmGLESv2.so')

        if all((exists(lib) for lib in brcm_lib_files)):
            print('Found brcmEGL and brcmGLES library files '
                  'for rpi platform at ' + dirname(brcm_lib_files[0]))
            gl_libs = ['brcmEGL', 'brcmGLESv2']
        else:
            print(
                'Failed to find brcmEGL and brcmGLESv2 library files '
                'for rpi platform, falling back to EGL and GLESv2.')
            gl_libs = ['EGL', 'GLESv2']
        flags['libraries'] = ['bcm_host'] + gl_libs
    elif platform in ['mali', 'vc']:
        flags['include_dirs'] = ['/usr/include/']
        flags['library_dirs'] = ['/usr/lib/arm-linux-gnueabihf']
        flags['libraries'] = ['GLESv2']
        c_options['use_x11'] = True
        c_options['use_egl'] = True
    else:
        flags['libraries'] = ['GL']
    return flags, base_flags


def determine_sdl2():
    flags = {}
    if not c_options['use_sdl2']:
        return flags

    sdl2_path = environ.get('KIVY_SDL2_PATH', None)

    if sdl2_flags and not sdl2_path and platform == 'darwin':
        return sdl2_flags

    includes, _ = get_isolated_env_paths()

    # no pkgconfig info, or we want to use a specific sdl2 path, so perform
    # manual configuration
    flags['libraries'] = ['SDL2', 'SDL2_ttf', 'SDL2_image', 'SDL2_mixer']
    split_chr = ';' if platform == 'win32' else ':'
    sdl2_paths = sdl2_path.split(split_chr) if sdl2_path else []

    if not sdl2_paths:
        sdl2_paths = []
        for include in includes + [join(sys.prefix, 'include')]:
            sdl_inc = join(include, 'SDL2')
            if isdir(sdl_inc):
                sdl2_paths.append(sdl_inc)
        sdl2_paths.extend(['/usr/local/include/SDL2', '/usr/include/SDL2'])

    flags['include_dirs'] = sdl2_paths
    flags['extra_link_args'] = []
    flags['extra_compile_args'] = []
    flags['library_dirs'] = (
        sdl2_paths if sdl2_paths else
        ['/usr/local/lib/'])

    if sdl2_flags:
        flags = merge(flags, sdl2_flags)

    # ensure headers for all the SDL2 and sub libraries are available
    libs_to_check = ['SDL', 'SDL_mixer', 'SDL_ttf', 'SDL_image']
    can_compile = True
    for lib in libs_to_check:
        found = False
        for d in flags['include_dirs']:
            fn = join(d, '{}.h'.format(lib))
            if exists(fn):
                found = True
                print('SDL2: found {} header at {}'.format(lib, fn))
                break

        if not found:
            print('SDL2: missing sub library {}'.format(lib))
            can_compile = False

    if not can_compile:
        c_options['use_sdl2'] = False
        return {}

    return flags


base_flags = determine_base_flags()
gl_flags, gl_flags_base = determine_gl_flags()

# -----------------------------------------------------------------------------
# sources to compile
# all the dependencies have been found manually with:
# grep -inr -E '(cimport|include)' kivy/graphics/context_instructions.{pxd,pyx}
graphics_dependencies = {
    'buffer.pyx': ['common.pxi'],
    'context.pxd': ['instructions.pxd', 'texture.pxd', 'vbo.pxd', 'cgl.pxd'],
    'cgl.pxd': ['common.pxi', 'config.pxi', 'gl_redirect.h'],
    'compiler.pxd': ['instructions.pxd'],
    'compiler.pyx': ['context_instructions.pxd'],
    'cgl.pyx': ['cgl.pxd'],
    'cgl_mock.pyx': ['cgl.pxd'],
    'cgl_sdl2.pyx': ['cgl.pxd'],
    'cgl_gl.pyx': ['cgl.pxd'],
    'cgl_glew.pyx': ['cgl.pxd'],
    'context_instructions.pxd': [
        'transformation.pxd', 'instructions.pxd', 'texture.pxd'],
    'fbo.pxd': ['cgl.pxd', 'instructions.pxd', 'texture.pxd'],
    'fbo.pyx': [
        'config.pxi', 'opcodes.pxi', 'transformation.pxd', 'context.pxd'],
    'gl_instructions.pyx': [
        'config.pxi', 'opcodes.pxi', 'cgl.pxd', 'instructions.pxd'],
    'instructions.pxd': [
        'vbo.pxd', 'context_instructions.pxd', 'compiler.pxd', 'shader.pxd',
        'texture.pxd', '../_event.pxd'],
    'instructions.pyx': [
        'config.pxi', 'opcodes.pxi', 'cgl.pxd',
        'context.pxd', 'common.pxi', 'vertex.pxd', 'transformation.pxd'],
    'opengl.pyx': [
        'config.pxi', 'common.pxi', 'cgl.pxd', 'gl_redirect.h'],
    'opengl_utils.pyx': [
        'opengl_utils_def.pxi', 'cgl.pxd', ],
    'shader.pxd': ['cgl.pxd', 'transformation.pxd', 'vertex.pxd'],
    'shader.pyx': [
        'config.pxi', 'common.pxi', 'cgl.pxd',
        'vertex.pxd', 'transformation.pxd', 'context.pxd',
        'gl_debug_logger.pxi'],
    'stencil_instructions.pxd': ['instructions.pxd'],
    'stencil_instructions.pyx': [
        'config.pxi', 'opcodes.pxi', 'cgl.pxd',
        'gl_debug_logger.pxi'],
    'scissor_instructions.pyx': [
        'config.pxi', 'opcodes.pxi', 'cgl.pxd'],
    'svg.pyx': ['config.pxi', 'common.pxi', 'texture.pxd', 'instructions.pxd',
                'vertex_instructions.pxd', 'tesselator.pxd'],
    'texture.pxd': ['cgl.pxd'],
    'texture.pyx': [
        'config.pxi', 'common.pxi', 'opengl_utils_def.pxi', 'context.pxd',
        'cgl.pxd', 'opengl_utils.pxd',
        'img_tools.pxi', 'gl_debug_logger.pxi'],
    'vbo.pxd': ['buffer.pxd', 'cgl.pxd', 'vertex.pxd'],
    'vbo.pyx': [
        'config.pxi', 'common.pxi', 'context.pxd',
        'instructions.pxd', 'shader.pxd', 'gl_debug_logger.pxi'],
    'vertex.pxd': ['cgl.pxd'],
    'vertex.pyx': ['config.pxi', 'common.pxi'],
    'vertex_instructions.pyx': [
        'config.pxi', 'common.pxi', 'vbo.pxd', 'vertex.pxd',
        'instructions.pxd', 'vertex_instructions.pxd',
        'cgl.pxd', 'texture.pxd', 'vertex_instructions_line.pxi'],
    'vertex_instructions_line.pxi': ['stencil_instructions.pxd']}

sources = {
    '_event.pyx': merge(base_flags, {'depends': ['properties.pxd']}),
    '_clock.pyx': {},
    'weakproxy.pyx': {},
    'properties.pyx': merge(
        base_flags, {'depends': ['_event.pxd', '_metrics.pxd']}),
    '_metrics.pyx': merge(base_flags, {'depends': ['_event.pxd']}),
    'graphics/buffer.pyx': merge(base_flags, gl_flags_base),
    'graphics/context.pyx': merge(base_flags, gl_flags_base),
    'graphics/compiler.pyx': merge(base_flags, gl_flags_base),
    'graphics/context_instructions.pyx': merge(base_flags, gl_flags_base),
    'graphics/fbo.pyx': merge(base_flags, gl_flags_base),
    'graphics/gl_instructions.pyx': merge(base_flags, gl_flags_base),
    'graphics/instructions.pyx': merge(base_flags, gl_flags_base),
    'graphics/opengl.pyx': merge(base_flags, gl_flags_base),
    'graphics/opengl_utils.pyx': merge(base_flags, gl_flags_base),
    'graphics/shader.pyx': merge(base_flags, gl_flags_base),
    'graphics/stencil_instructions.pyx': merge(base_flags, gl_flags_base),
    'graphics/scissor_instructions.pyx': merge(base_flags, gl_flags_base),
    'graphics/texture.pyx': merge(base_flags, gl_flags_base),
    'graphics/transformation.pyx': merge(base_flags, gl_flags_base),
    'graphics/vbo.pyx': merge(base_flags, gl_flags_base),
    'graphics/vertex.pyx': merge(base_flags, gl_flags_base),
    'graphics/vertex_instructions.pyx': merge(base_flags, gl_flags_base),
    'graphics/cgl.pyx': merge(base_flags, gl_flags_base),
    'graphics/cgl_backend/cgl_mock.pyx': merge(base_flags, gl_flags_base),
    'graphics/cgl_backend/cgl_gl.pyx': merge(base_flags, gl_flags),
    'graphics/cgl_backend/cgl_glew.pyx': merge(base_flags, gl_flags),
    'graphics/cgl_backend/cgl_sdl2.pyx': merge(base_flags, gl_flags_base),
    'graphics/cgl_backend/cgl_debug.pyx': merge(base_flags, gl_flags_base),
    'core/text/text_layout.pyx': base_flags,
    'core/window/window_info.pyx': base_flags,
    'graphics/tesselator.pyx': merge(base_flags, {
        'include_dirs': ['kivy/lib/libtess2/Include'],
        'c_depends': [
            'lib/libtess2/Source/bucketalloc.c',
            'lib/libtess2/Source/dict.c',
            'lib/libtess2/Source/geom.c',
            'lib/libtess2/Source/mesh.c',
            'lib/libtess2/Source/priorityq.c',
            'lib/libtess2/Source/sweep.c',
            'lib/libtess2/Source/tess.c'
        ]
    }),
    'graphics/svg.pyx': merge(base_flags, gl_flags_base)
}

if c_options["use_sdl2"]:
    sdl2_flags = determine_sdl2()

if c_options['use_sdl2'] and sdl2_flags:
    sources['graphics/cgl_backend/cgl_sdl2.pyx'] = merge(
        sources['graphics/cgl_backend/cgl_sdl2.pyx'], sdl2_flags)
    sdl2_depends = {'depends': ['lib/sdl2.pxi']}
    for source_file in ('core/window/_window_sdl2.pyx',
                        'core/image/_img_sdl2.pyx',
                        'core/text/_text_sdl2.pyx',
                        'core/audio/audio_sdl2.pyx',
                        'core/clipboard/_clipboard_sdl2.pyx'):
        sources[source_file] = merge(
            base_flags, sdl2_flags, sdl2_depends)

if c_options['use_pangoft2'] in (None, True) and platform not in (
                                      'android', 'ios', 'win32'):
    pango_flags = pkgconfig('pangoft2')
    if pango_flags and 'libraries' in pango_flags:
        print('Pango: pangoft2 found via pkg-config')
        c_options['use_pangoft2'] = True
        pango_depends = {'depends': [
            'lib/pango/pangoft2.pxi',
            'lib/pango/pangoft2.h']}
        sources['core/text/_text_pango.pyx'] = merge(
                base_flags, pango_flags, pango_depends)
        print(sources['core/text/_text_pango.pyx'])

if platform in ('darwin', 'ios'):
    # activate ImageIO provider for our core image
    if platform == 'ios':
        osx_flags = {'extra_link_args': [
            '-framework', 'Foundation',
            '-framework', 'UIKit',
            '-framework', 'AudioToolbox',
            '-framework', 'CoreGraphics',
            '-framework', 'QuartzCore',
            '-framework', 'ImageIO',
            '-framework', 'Accelerate']}
    else:
        osx_flags = {'extra_link_args': [
            '-framework', 'ApplicationServices']}
    sources['core/image/img_imageio.pyx'] = merge(
        base_flags, osx_flags)

if c_options['use_avfoundation']:
    import platform as _platform
    mac_ver = [int(x) for x in _platform.mac_ver()[0].split('.')[:2]]
    if mac_ver >= [10, 7] or platform == 'ios':
        osx_flags = {
            'extra_link_args': ['-framework', 'AVFoundation'],
            'extra_compile_args': ['-ObjC++'],
            'depends': ['core/camera/camera_avfoundation_implem.m']}
        sources['core/camera/camera_avfoundation.pyx'] = merge(
            base_flags, osx_flags)
    else:
        print('AVFoundation cannot be used, OSX >= 10.7 is required')

if c_options['use_rpi']:
    sources['lib/vidcore_lite/egl.pyx'] = merge(
        base_flags, gl_flags)
    sources['lib/vidcore_lite/bcm.pyx'] = merge(
        base_flags, gl_flags)

if c_options['use_x11']:
    libs = ['Xrender', 'X11']
    if c_options['use_egl']:
        libs += ['EGL']
    else:
        libs += ['GL']
    sources['core/window/window_x11.pyx'] = merge(
        base_flags, gl_flags, {
            # FIXME add an option to depend on them but not compile them
            # cause keytab is included in core, and core is included in
            # window_x11
            #
            # 'depends': [
            #    'core/window/window_x11_keytab.c',
            #    'core/window/window_x11_core.c'],
            'libraries': libs})

if c_options['use_gstreamer']:
    sources['lib/gstplayer/_gstplayer.pyx'] = merge(
        base_flags, gst_flags, {
            'depends': ['lib/gstplayer/_gstplayer.h']})

# -----------------------------------------------------------------------------
# extension modules


def get_dependencies(name, deps=None):
    if deps is None:
        deps = []
    for dep in graphics_dependencies.get(name, []):
        if dep not in deps:
            deps.append(dep)
            get_dependencies(dep, deps)
    return deps


def resolve_dependencies(fn, depends):
    fn = basename(fn)
    deps = []
    get_dependencies(fn, deps)
    get_dependencies(fn.replace('.pyx', '.pxd'), deps)

    deps_final = []
    paths_to_test = ['graphics', 'include']
    for dep in deps:
        found = False
        for path in paths_to_test:
            filename = expand(src_path, path, dep)
            if exists(filename):
                deps_final.append(filename)
                found = True
                break
        if not found:
            print('ERROR: Dependency for {} not resolved: {}'.format(
                fn, dep
            ))

    return deps_final


def get_extensions_from_sources(sources):
    ext_modules = []
    if environ.get('KIVY_FAKE_BUILDEXT'):
        print('Fake build_ext asked, will generate only .h/.c')
        return ext_modules
    for pyx, flags in sources.items():
        is_graphics = pyx.startswith('graphics')
        pyx_path = expand(src_path, pyx)
        depends = [expand(src_path, x) for x in flags.pop('depends', [])]
        c_depends = [expand(src_path, x) for x in flags.pop('c_depends', [])]
        if not can_use_cython:
            # can't use cython, so use the .c files instead.
            pyx_path = '%s.c' % pyx_path[:-4]
        if is_graphics:
            depends = resolve_dependencies(pyx_path, depends)
        f_depends = [x for x in depends if x.rsplit('.', 1)[-1] in (
            'c', 'cpp', 'm')]
        module_name = '.'.join(['kivy'] + pyx[:-4].split('/'))
        flags_clean = {'depends': depends}
        for key, value in flags.items():
            if len(value):
                flags_clean[key] = value
        ext_modules.append(CythonExtension(
            module_name, [pyx_path] + f_depends + c_depends, **flags_clean))
    return ext_modules


ext_modules = get_extensions_from_sources(sources)


# -----------------------------------------------------------------------------
# automatically detect data files
split_examples = int(environ.get('KIVY_SPLIT_EXAMPLES', '0'))
data_file_prefix = 'share/kivy-'
examples = {}
examples_allowed_ext = ('readme', 'py', 'wav', 'png', 'jpg', 'svg', 'json',
                        'avi', 'gif', 'txt', 'ttf', 'obj', 'mtl', 'kv', 'mpg',
                        'glsl', 'zip')
for root, subFolders, files in walk('examples'):
    for fn in files:
        ext = fn.split('.')[-1].lower()
        if ext not in examples_allowed_ext:
            continue
        filename = join(root, fn)
        directory = '%s%s' % (data_file_prefix, dirname(filename))
        if directory not in examples:
            examples[directory] = []
        examples[directory].append(filename)

binary_deps = []
binary_deps_path = join(src_path, 'kivy', 'binary_deps')
if isdir(binary_deps_path):
    for root, dirnames, filenames in walk(binary_deps_path):
        for fname in filenames:
            binary_deps.append(
                join(root.replace(binary_deps_path, 'binary_deps'), fname))


def glob_paths(*patterns, excludes=('.pyc', )):
    files = []
    base = Path(join(src_path, 'kivy'))

    for pat in patterns:
        for f in base.glob(pat):
            if f.suffix in excludes:
                continue
            files.append(str(f.relative_to(base)))
    return files


# -----------------------------------------------------------------------------
# setup !
if not build_examples:
    setup(
        name='Kivy',
        version=__version__,
        author='Kivy Team and other contributors',
        author_email='kivy-dev@googlegroups.com',
        url='http://kivy.org',
        project_urls={
            'Source': 'https://github.com/kivy/kivy',
        },
        license='MIT',
        description=(
            'A software library for rapid development of '
            'hardware-accelerated multitouch applications.'),
        long_description=get_description(),
        long_description_content_type='text/markdown',
        ext_modules=ext_modules,
        cmdclass=cmdclass,
        packages=find_packages(include=['kivy*']),
        package_dir={'kivy': 'kivy'},
        package_data={
            'kivy':
                glob_paths('*.pxd', '*.pxi') +
                glob_paths('**/*.pxd', '**/*.pxi') +
                glob_paths('data/**/*.*') +
                glob_paths('include/**/*.*') +
                glob_paths('tools/**/*.*', excludes=('.pyc', '.enc')) +
                glob_paths('graphics/**/*.h') +
                glob_paths('tests/**/*.*') +
                [
                    'setupconfig.py',
                ] + binary_deps
        },
        data_files=[] if split_examples else list(examples.items()),
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: MacOS X',
            'Environment :: Win32 (MS Windows)',
            'Environment :: X11 Applications',
            'Intended Audience :: Developers',
            'Intended Audience :: End Users/Desktop',
            'Intended Audience :: Information Technology',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: MIT License',
            'Natural Language :: English',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX :: BSD :: FreeBSD',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Topic :: Artistic Software',
            'Topic :: Games/Entertainment',
            'Topic :: Multimedia :: Graphics :: 3D Rendering',
            'Topic :: Multimedia :: Graphics :: Capture :: Digital Camera',
            'Topic :: Multimedia :: Graphics :: Presentation',
            'Topic :: Multimedia :: Graphics :: Viewers',
            'Topic :: Multimedia :: Sound/Audio :: Players :: MP3',
            'Topic :: Multimedia :: Video :: Display',
            'Topic :: Scientific/Engineering :: Human Machine Interfaces',
            'Topic :: Scientific/Engineering :: Visualization',
            ('Topic :: Software Development :: Libraries :: '
             'Application Frameworks'),
            'Topic :: Software Development :: User Interfaces'])
else:
    setup(
        name='Kivy-examples',
        version=__version__,
        author='Kivy Team and other contributors',
        author_email='kivy-dev@googlegroups.com',
        url='http://kivy.org',
        license='MIT',
        description=('Kivy examples.'),
        long_description_content_type='text/markdown',
        long_description=get_description(),
        data_files=list(examples.items()))
