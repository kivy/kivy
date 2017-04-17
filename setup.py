#
# Kivy - Cross-platform UI framework
# https://kivy.org/
#
from __future__ import print_function

import sys
build_examples = False
if "--build_examples" in sys.argv:
    build_examples = True
    sys.argv.remove("--build_examples")

from copy import deepcopy
import os
from os.path import join, dirname, sep, exists, basename, isdir
from os import walk, environ
from distutils.version import LooseVersion
from distutils.sysconfig import get_python_inc
from collections import OrderedDict
from time import sleep
from subprocess import check_output, CalledProcessError
from datetime import datetime

if environ.get('KIVY_USE_SETUPTOOLS'):
    from setuptools import setup, Extension
    print('Using setuptools')
else:
    from distutils.core import setup
    from distutils.extension import Extension
    print('Using distutils')


PY3 = sys.version > '3'

if PY3:  # fix error with py3's LooseVersion comparisons
    def ver_equal(self, other):
        return self.version == other

    LooseVersion.__eq__ = ver_equal


def get_version(filename='kivy/version.py'):
    VERSION = kivy.__version__
    DATE = datetime.utcnow().strftime('%Y%m%d')
    try:
        GIT_REVISION = check_output(
            ['git', 'rev-parse', 'HEAD']
        ).strip().decode('ascii')
    except CalledProcessError:
        GIT_REVISION = "Unknown"

    cnt = (
        "# THIS FILE IS GENERATED FROM KIVY SETUP.PY\n"
        "__version__ = '%(version)s'\n"
        "__hash__ = '%(hash)s'\n"
        "__date__ = '%(date)s'\n"
    )

    with open(filename, 'w') as f:
        f.write(cnt % {
            'version': VERSION,
            'hash': GIT_REVISION,
            'date': DATE
        })
    return VERSION


MIN_CYTHON_STRING = '0.23'
MIN_CYTHON_VERSION = LooseVersion(MIN_CYTHON_STRING)
MAX_CYTHON_STRING = '0.23'
MAX_CYTHON_VERSION = LooseVersion(MAX_CYTHON_STRING)
CYTHON_UNSUPPORTED = ()


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


# -----------------------------------------------------------------------------
# Determine on which platform we are

platform = sys.platform

# Detect 32/64bit for OSX (http://stackoverflow.com/a/1405971/798575)
if sys.platform == 'darwin':
    if sys.maxsize > 2 ** 32:
        osx_arch = 'x86_64'
    else:
        osx_arch = 'i386'

# Detect Python for android project (http://github.com/kivy/python-for-android)
ndkplatform = environ.get('NDKPLATFORM')
if ndkplatform is not None and environ.get('LIBLINK'):
    platform = 'android'
kivy_ios_root = environ.get('KIVYIOSROOT', None)
if kivy_ios_root is not None:
    platform = 'ios'
if exists('/opt/vc/include/bcm_host.h'):
    platform = 'rpi'
if exists('/usr/lib/arm-linux-gnueabihf/libMali.so'):
    platform = 'mali'

# -----------------------------------------------------------------------------
# Detect options
#
c_options = OrderedDict()
c_options['use_rpi'] = platform == 'rpi'
c_options['use_mali'] = platform == 'mali'
c_options['use_egl'] = False
c_options['use_opengl_es2'] = None
c_options['use_opengl_mock'] = environ.get('READTHEDOCS', None) == 'True'
c_options['use_sdl2'] = None
c_options['use_ios'] = False
c_options['use_mesagl'] = False
c_options['use_x11'] = False
c_options['use_gstreamer'] = None
c_options['use_avfoundation'] = platform == 'darwin'
c_options['use_osx_frameworks'] = platform == 'darwin'
c_options['debug_gl'] = False

# now check if environ is changing the default values
for key in list(c_options.keys()):
    ukey = key.upper()
    if ukey in environ:
        value = bool(int(environ[ukey]))
        print('Environ change {0} -> {1}'.format(key, value))
        c_options[key] = value


# -----------------------------------------------------------------------------
# Cython check
# on python-for-android and kivy-ios, cython usage is external

cython_unsupported_append = '''

  Please note that the following versions of Cython are not supported
  at all: {}
'''.format(', '.join(map(str, CYTHON_UNSUPPORTED)))

cython_min = '''\
  This version of Cython is not compatible with Kivy. Please upgrade to
  at least version {0}, preferably the newest supported version {1}.

  If your platform provides a Cython package, make sure you have upgraded
  to the newest version. If the newest version available is still too low,
  please remove it and install the newest supported Cython via pip:

    pip install -I Cython=={1}{2}\
'''.format(MIN_CYTHON_STRING, MAX_CYTHON_STRING,
           cython_unsupported_append if CYTHON_UNSUPPORTED else '')

cython_max = '''\
  This version of Cython is untested with Kivy. While this version may
  work perfectly fine, it is possible that you may experience issues. If
  you do have issues, please downgrade to a supported version. It is
  best to use the newest supported version, {1}, but the minimum
  supported version is {0}.

  If your platform provides a Cython package, check if you can downgrade
  to a supported version. Otherwise, uninstall the platform package and
  install Cython via pip:

    pip install -I Cython=={1}{2}\
'''.format(MIN_CYTHON_STRING, MAX_CYTHON_STRING,
           cython_unsupported_append if CYTHON_UNSUPPORTED else '')

cython_unsupported = '''\
  This version of Cython suffers from known bugs and is unsupported.
  Please install the newest supported version, {1}, if possible, but
  the minimum supported version is {0}.

  If your platform provides a Cython package, check if you can install
  a supported version. Otherwise, uninstall the platform package and
  install Cython via pip:

    pip install -I Cython=={1}{2}\
'''.format(MIN_CYTHON_STRING, MAX_CYTHON_STRING,
           cython_unsupported_append)

have_cython = False
skip_cython = False
if platform in ('ios', 'android'):
    print('\nCython check avoided.')
    skip_cython = True
else:
    try:
        # check for cython
        from Cython.Distutils import build_ext
        have_cython = True
        import Cython
        cy_version_str = Cython.__version__
        cy_ver = LooseVersion(cy_version_str)
        print('\nDetected Cython version {}'.format(cy_version_str))
        if cy_ver < MIN_CYTHON_VERSION:
            print(cython_min)
            raise ImportError('Incompatible Cython Version')
        if cy_ver in CYTHON_UNSUPPORTED:
            print(cython_unsupported)
            raise ImportError('Incompatible Cython Version')
        if cy_ver > MAX_CYTHON_VERSION:
            print(cython_max)
            sleep(1)
    except ImportError:
        print("\nCython is missing, it's required for compiling kivy !\n\n")
        raise

if not have_cython:
    from distutils.command.build_ext import build_ext

# -----------------------------------------------------------------------------
# Setup classes

# the build path where kivy is being compiled
src_path = build_path = dirname(__file__)


class KivyBuildExt(build_ext):

    def finalize_options(self):
        retval = build_ext.finalize_options(self)
        global build_path
        if (self.build_lib is not None and exists(self.build_lib) and
                not self.inplace):
            build_path = self.build_lib
        return retval

    def build_extensions(self):
        # build files
        config_h_fn = ('include', 'config.h')
        config_pxi_fn = ('include', 'config.pxi')
        config_py_fn = ('setupconfig.py', )

        # generate headers
        config_h = '// Autogenerated file for Kivy C configuration\n'
        config_h += '#define __PY3 {0}\n'.format(int(PY3))
        config_pxi = '# Autogenerated file for Kivy Cython configuration\n'
        config_pxi += 'DEF PY3 = {0}\n'.format(int(PY3))
        config_py = '# Autogenerated file for Kivy configuration\n'
        config_py += 'PY3 = {0}\n'.format(int(PY3))
        config_py += 'CYTHON_MIN = {0}\nCYTHON_MAX = {1}\n'.format(
            repr(MIN_CYTHON_STRING), repr(MAX_CYTHON_STRING))
        config_py += 'CYTHON_BAD = {0}\n'.format(repr(', '.join(map(
            str, CYTHON_UNSUPPORTED))))

        # generate content
        print('Build configuration is:')
        for opt, value in c_options.items():
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

        build_ext.build_extensions(self)

    def update_if_changed(self, fn, content):
        need_update = True
        if exists(fn):
            with open(fn) as fd:
                need_update = fd.read() != content
        if need_update:
            with open(fn, 'w') as fd:
                fd.write(content)
        return need_update


def _check_and_fix_sdl2_mixer(f_path):
    print("Check if SDL2_mixer smpeg2 have an @executable_path")
    rpath_from = ("@executable_path/../Frameworks/SDL2.framework"
                  "/Versions/A/SDL2")
    rpath_to = "@rpath/../../../../SDL2.framework/Versions/A/SDL2"
    smpeg2_path = ("{}/Versions/A/Frameworks/smpeg2.framework"
                   "/Versions/A/smpeg2").format(f_path)
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
# extract version (simulate doc generation, kivy will be not imported)
environ['KIVY_DOC_INCLUDE'] = '1'
import kivy

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
if platform in ('android', 'darwin', 'ios', 'rpi', 'mali'):
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

elif platform == 'darwin':
    if c_options['use_osx_frameworks']:
        if osx_arch == "i386":
            print("Warning: building with frameworks fail on i386")
        else:
            print("OSX framework used, force to x86_64 only")
            environ["ARCHFLAGS"] = environ.get("ARCHFLAGS", "-arch x86_64")
            print("OSX ARCHFLAGS are: {}".format(environ["ARCHFLAGS"]))

# detect gstreamer, only on desktop
# works if we forced the options or in autodetection
if platform not in ('ios', 'android') and (c_options['use_gstreamer']
                                           in (None, True)):
    if c_options['use_osx_frameworks'] and platform == 'darwin':
        # check the existence of frameworks
        f_path = '/Library/Frameworks/GStreamer.framework'
        if not exists(f_path):
            c_options['use_gstreamer'] = False
            print('Missing GStreamer framework {}'.format(f_path))
        else:
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

    else:
        # use pkg-config approach instead
        gst_flags = pkgconfig('gstreamer-1.0')
        if 'libraries' in gst_flags:
            c_options['use_gstreamer'] = True


# detect SDL2, only on desktop and iOS, or android if explicitly enabled
# works if we forced the options or in autodetection
sdl2_flags = {}
if c_options['use_sdl2'] or (
        platform not in ('android',) and c_options['use_sdl2'] is None):

    if c_options['use_osx_frameworks'] and platform == 'darwin':
        # check the existence of frameworks
        sdl2_valid = True
        sdl2_flags = {
            'extra_link_args': [
                '-F/Library/Frameworks',
                '-Xlinker', '-rpath',
                '-Xlinker', '/Library/Frameworks',
                '-Xlinker', '-headerpad',
                '-Xlinker', '190'],
            'include_dirs': [],
            'extra_compile_args': ['-F/Library/Frameworks']
        }
        for name in ('SDL2', 'SDL2_ttf', 'SDL2_image', 'SDL2_mixer'):
            f_path = '/Library/Frameworks/{}.framework'.format(name)
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
            print('Deactivate SDL2 compilation due to missing frameworks')
        else:
            c_options['use_sdl2'] = True
            print('Activate SDL2 compilation')

    elif platform != "ios":
        # use pkg-config approach instead
        sdl2_flags = pkgconfig('sdl2', 'SDL2_ttf', 'SDL2_image', 'SDL2_mixer')
        if 'libraries' in sdl2_flags:
            c_options['use_sdl2'] = True


# -----------------------------------------------------------------------------
# declare flags


def get_modulename_from_file(filename):
    filename = filename.replace(sep, '/')
    pyx = '.'.join(filename.split('.')[:-1])
    pyxl = pyx.split('/')
    while pyxl[0] != 'kivy':
        pyxl.pop(0)
    if pyxl[1] == 'kivy':
        pyxl.pop(0)
    return '.'.join(pyxl)


def expand(root, *args):
    return join(root, 'kivy', *args)


class CythonExtension(Extension):

    def __init__(self, *args, **kwargs):
        Extension.__init__(self, *args, **kwargs)
        self.cython_directives = {
            'c_string_encoding': 'utf-8',
            'profile': 'USE_PROFILE' in environ,
            'embedsignature': 'USE_EMBEDSIGNATURE' in environ}
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
    flags = {
        'libraries': [],
        'include_dirs': [join(src_path, 'kivy', 'include')],
        'library_dirs': [],
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
    elif platform == 'darwin':
        v = os.uname()
        if v[2] >= '13.0.0':
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
    if c_options['use_opengl_mock']:
        return flags, base_flags
    if platform == 'win32':
        flags['libraries'] = ['opengl32', 'glew32']
    elif platform == 'ios':
        flags['libraries'] = ['GLESv2']
        flags['extra_link_args'] = ['-framework', 'OpenGLES']
    elif platform == 'darwin':
        flags['extra_link_args'] = ['-framework', 'OpenGL', '-arch', osx_arch]
        flags['extra_compile_args'] = ['-arch', osx_arch]
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
        flags['include_dirs'] = [
            '/opt/vc/include',
            '/opt/vc/include/interface/vcos/pthreads',
            '/opt/vc/include/interface/vmcs_host/linux']
        flags['library_dirs'] = ['/opt/vc/lib']
        flags['libraries'] = ['bcm_host', 'EGL', 'GLESv2']
    elif platform == 'mali':
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

    # no pkgconfig info, or we want to use a specific sdl2 path, so perform
    # manual configuration
    flags['libraries'] = ['SDL2', 'SDL2_ttf', 'SDL2_image', 'SDL2_mixer']
    split_chr = ';' if platform == 'win32' else ':'
    sdl2_paths = sdl2_path.split(split_chr) if sdl2_path else []

    if not sdl2_paths:
        sdl_inc = join(sys.prefix, 'include', 'SDL2')
        if isdir(sdl_inc):
            sdl2_paths = [sdl_inc]
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
    'gl_redirect.h': ['common_subset.h', 'gl_mock.h'],
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
    'properties.pyx': merge(base_flags, {'depends': ['_event.pxd']}),
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
    if mac_ver >= [10, 7]:
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
    return [expand(src_path, 'graphics', x) for x in deps]


def get_extensions_from_sources(sources):
    ext_modules = []
    if environ.get('KIVY_FAKE_BUILDEXT'):
        print('Fake build_ext asked, will generate only .h/.c')
        return ext_modules
    for pyx, flags in sources.items():
        is_graphics = pyx.startswith('graphics')
        pyx = expand(src_path, pyx)
        depends = [expand(src_path, x) for x in flags.pop('depends', [])]
        c_depends = [expand(src_path, x) for x in flags.pop('c_depends', [])]
        if not have_cython:
            pyx = '%s.c' % pyx[:-4]
        if is_graphics:
            depends = resolve_dependencies(pyx, depends)
        f_depends = [x for x in depends if x.rsplit('.', 1)[-1] in (
            'c', 'cpp', 'm')]
        module_name = get_modulename_from_file(pyx)
        flags_clean = {'depends': depends}
        for key, value in flags.items():
            if len(value):
                flags_clean[key] = value
        ext_modules.append(CythonExtension(
            module_name, [pyx] + f_depends + c_depends, **flags_clean))
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

# -----------------------------------------------------------------------------
# setup !
if not build_examples:
    setup(
        name='Kivy',
        version=get_version(),
        author='Kivy Team and other contributors',
        author_email='kivy-dev@googlegroups.com',
        url='http://kivy.org',
        license='MIT',
        description=(
            'A software library for rapid development of '
            'hardware-accelerated multitouch applications.'),
        ext_modules=ext_modules,
        cmdclass=cmdclass,
        packages=[
            'kivy',
            'kivy.adapters',
            'kivy.core',
            'kivy.core.audio',
            'kivy.core.camera',
            'kivy.core.clipboard',
            'kivy.core.image',
            'kivy.core.gl',
            'kivy.core.spelling',
            'kivy.core.text',
            'kivy.core.video',
            'kivy.core.window',
            'kivy.deps',
            'kivy.effects',
            'kivy.graphics',
            'kivy.graphics.cgl_backend',
            'kivy.garden',
            'kivy.input',
            'kivy.input.postproc',
            'kivy.input.providers',
            'kivy.lang',
            'kivy.lib',
            'kivy.lib.osc',
            'kivy.lib.gstplayer',
            'kivy.lib.vidcore_lite',
            'kivy.modules',
            'kivy.network',
            'kivy.storage',
            'kivy.tests',
            'kivy.tools',
            'kivy.tools.packaging',
            'kivy.tools.packaging.pyinstaller_hooks',
            'kivy.tools.highlight',
            'kivy.extras',
            'kivy.uix',
            'kivy.uix.behaviors',
            'kivy.uix.recycleview',
        ],
        package_dir={'kivy': 'kivy'},
        package_data={'kivy': [
            '*.pxd',
            '*.pxi',
            'core/text/*.pxd',
            'core/text/*.pxi',
            'graphics/*.pxd',
            'graphics/*.pxi',
            'graphics/*.h',
            'include/*',
            'lib/vidcore_lite/*.pxd',
            'lib/vidcore_lite/*.pxi',
            'data/*.kv',
            'data/*.json',
            'data/fonts/*.ttf',
            'data/images/*.png',
            'data/images/*.jpg',
            'data/images/*.gif',
            'data/images/*.atlas',
            'data/keyboards/*.json',
            'data/logo/*.png',
            'data/glsl/*.png',
            'data/glsl/*.vs',
            'data/glsl/*.fs',
            'tests/*.zip',
            'tests/*.kv',
            'tests/*.png',
            'tests/*.ttf',
            'tests/*.ogg',
            'tools/highlight/*.vim',
            'tools/highlight/*.el',
            'tools/packaging/README.txt',
            'tools/packaging/win32/kivy.bat',
            'tools/packaging/win32/kivyenv.sh',
            'tools/packaging/win32/README.txt',
            'tools/packaging/osx/Info.plist',
            'tools/packaging/osx/InfoPlist.strings',
            'tools/gles_compat/*.h',
            'tools/packaging/osx/kivy.sh'] + binary_deps},
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
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
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
            'Topic :: Software Development :: User Interfaces'],
        dependency_links=[
            'https://github.com/kivy-garden/garden/archive/master.zip'],
        install_requires=['Kivy-Garden>=0.1.4', 'docutils', 'pygments'],
        setup_requires=[
            'cython>=' + MIN_CYTHON_STRING
        ] if not skip_cython else [])
else:
    setup(
        name='Kivy-examples',
        version=get_version(),
        author='Kivy Team and other contributors',
        author_email='kivy-dev@googlegroups.com',
        url='http://kivy.org',
        license='MIT',
        description=('Kivy examples.'),
        data_files=list(examples.items()))
