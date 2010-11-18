import sys
import os
import shutil
from distutils.core import setup
from distutils.extension import Extension

#check for numpy, which is absolutely required!
try:
    import numpy
except:
    print '#' * 80
    print 'Kivy require numpy now. Please install it before running Kivy setup'
    print '#' * 80
    sys.exit(1)




# extract version (simulate doc generation, kivy will be not imported)
import kivy

# extra build commands go in the cmdclass dict {'command-name': CommandClass}
# see tools.packaging.{platform}.build.py for custom build commands for portable packages
# also e.g. we use build_ext command from cython if its installed for c extensions
cmdclass = {}

# add build rules for portable packages to cmdclass
if sys.platform == 'win32':
    from kivy.tools.packaging.win32.build import WindowsPortableBuild
    cmdclass['build_portable'] = WindowsPortableBuild
elif sys.platform == 'darwin':
   from kivy.tools.packaging.osx.build import OSXPortableBuild
   cmdclass['build_portable'] = OSXPortableBuild

from kivy.tools.packaging.factory import FactoryBuild
cmdclass['build_factory'] = FactoryBuild


# extension modules
ext_modules = []

#accelerated matrix transformation module written in C for numpy
ext_modules.append( Extension(
    'kivy.c_ext._transformations',
    ['kivy/c_ext/transformations.c'],
    include_dirs=[numpy.get_include()])
)

#check for cython
try:
    have_cython = True
    from Cython.Distutils import build_ext
except:
    have_cython = False

# create .c for every module in c_ext
if 'sdist' in sys.argv and have_cython:
    from glob import glob
    from Cython.Compiler.Main import compile
    print 'Generating C files...',
    files = glob(os.path.join(os.path.dirname(__file__), 'kivy', 'c_ext', '*.pyx'))
    compile(files)
    print 'Done !'

#add cython core extension modules if cython is available
if have_cython:
    cmdclass['build_ext'] = build_ext
    libraries = []
    include_dirs = []
    extra_link_args = []
    if sys.platform == 'win32':
        libraries.append('opengl32')
    elif sys.platform == 'darwin':
        '''
        # On OSX, gl.h is not in GL/gl.h but OpenGL/gl.h. Cython has no
        # such thing as #ifdef, hence we just copy the file here.
        source = '/System/Library/Frameworks/OpenGL.framework/Versions/A/Headers/gl.h'
        incl = 'build/include/'
        dest = os.path.join(incl, 'GL/')
        try:
            os.makedirs(dest)
        except OSError:
            # Already exists, so don't care
            pass
        shutil.copy(source, dest)
        include_dirs = [incl]
        '''
        # On OSX, it's not -lGL, but -framework OpenGL...
        extra_link_args = ['-framework', 'OpenGL']
    elif sys.platform.startswith('freebsd'):
        include_dirs += ['/usr/local/include']
        extra_link_args += ['-L', '/usr/local/lib']
    else:
        libraries.append('GL')

    # simple extensions
    for x in ('event', 'properties'):
        ext_modules.append(Extension(
            'kivy.c_ext.%s' % x, ['kivy/c_ext/%s.pyx' % x]
        ))

    # opengl aware modules
    for x in (
        'opengl',
        'buffer',
        'shader',
        'texture',
        'vbo',
        'vertex',
        #'canvas',
        #'context',
        'instructions',
        'context_instructions',
        'vertex_instructions',
        'compiler',

    ):
        ext_modules.append(Extension(
            'kivy.c_ext.graphics.%s'%x, ['kivy/c_ext/graphics/%s.pyx' % x],
            libraries=libraries,
            include_dirs=include_dirs,
            extra_link_args=extra_link_args
        ))


    #poly2try extension
    ext_modules.append(Extension('kivy.c_ext.p2t', [
     'kivy/c_ext/poly2tri/src/p2t.pyx',
     'kivy/c_ext/poly2tri/poly2tri/common/shapes.cc',
     'kivy/c_ext/poly2tri/poly2tri/sweep/advancing_front.cc',
     'kivy/c_ext/poly2tri/poly2tri/sweep/cdt.cc',
     'kivy/c_ext/poly2tri/poly2tri/sweep/sweep.cc',
     'kivy/c_ext/poly2tri/poly2tri/sweep/sweep_context.cc'
    ], language="c++"))


#setup datafiles to be included in the disytibution, liek examples...
#extracts all examples files except sandbox
data_file_prefix = 'share/kivy-'
examples = {}
examples_allowed_ext = ('readme', 'py', 'wav', 'png', 'jpg', 'svg',
                        'avi', 'gif', 'txt', 'ttf', 'obj', 'mtl')
for root, subFolders, files in os.walk('examples'):
    if 'sandbox' in root:
        continue
    for file in files:
        ext = file.split('.')[-1].lower()
        if ext not in examples_allowed_ext:
            continue
        filename = os.path.join(root, file)
        directory = '%s%s' % (data_file_prefix, os.path.dirname(filename))
        if not directory in examples:
            examples[directory] = []
        examples[directory].append(filename)



# setup !
setup(
    name='Kivy',
    version=kivy.__version__,
    author='Kivy Crew',
    author_email='kivy-dev@googlegroups.com',
    url='http://kivy.org/',
    license='LGPL',
    description='A framework for making accelerated multitouch UI',
    ext_modules=ext_modules,
    cmdclass=cmdclass,
    test_suite='nose.collector',
    packages=[
        'kivy',
        'kivy.c_ext',
        'kivy.core',
        'kivy.core.audio',
        'kivy.core.camera',
        'kivy.core.clipboard',
        'kivy.core.image',
        'kivy.core.gl',
        'kivy.core.spelling',
        'kivy.core.svg',
        'kivy.core.text',
        'kivy.core.video',
        'kivy.core.window',
        'kivy.graphics',
        'kivy.input',
        'kivy.input.postproc',
        'kivy.input.providers',
        'kivy.lib',
        'kivy.lib.osc',
        'kivy.modules',
        'kivy.tools',
        'kivy.tools.packaging',
        'kivy.tools.packaging.win32',
        'kivy.tools.packaging.osx',
        'kivy.uix',
    ],
    package_dir={'kivy': 'kivy'},
    package_data={'kivy': [
        'data/*.css',
        'data/*.png',
        'data/*.ttf',
        'tools/packaging/README.txt',
        'tools/packaging/win32/kivy.bat',
        'tools/packaging/win32/README.txt',
        'tools/packaging/osx/kivy.sh',]
    },
    data_files=examples.items(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: BSD :: FreeBSD',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
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
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: User Interfaces',
    ]
)
