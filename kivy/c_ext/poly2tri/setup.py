from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

from imports import CPP_SOURCES

mod_math = Extension(
    "p2t",
    ["src/p2t.pyx"] + CPP_SOURCES,
    language = "c++"
)

setup(
    cmdclass = {'build_ext': build_ext},
    ext_modules = [mod_math],
)
