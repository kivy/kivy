from distutils.core import setup
from Cython.Build import cythonize
from os.path import join, dirname, abspath

setup(
    ext_modules=cythonize(abspath(join(dirname(__file__), "kv_cython_test.pyx")))
)
