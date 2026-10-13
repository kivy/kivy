#
# Kivy-examples - the bundled Kivy example applications, packaged as a
# standalone wheel separate from the main Kivy distribution.
#
# Metadata lives in this directory's pyproject.toml. This script only collects
# the example data files (which live at the repository root, two levels up) and
# resolves the version from the shared kivy/_version.py so the examples wheel
# always matches the Kivy release it ships with.
#
import os
from os.path import abspath, dirname, join

from setuptools import setup

# This packaging directory is <repo_root>/packaging/kivy_examples.
HERE = dirname(abspath(__file__))
ROOT = abspath(join(HERE, '..', '..'))

# __version__ is provided by exec, this assignment just keeps linters happy.
__version__ = None
with open(join(ROOT, 'kivy', '_version.py'), encoding='utf-8') as f:
    exec(f.read())

# Collect the example files from the repository-root examples/ tree, mirroring
# the layout used by the main setup.py so the produced wheel is identical to the
# historical Kivy-examples wheel.
data_file_prefix = 'share/kivy-'
examples = {}
examples_allowed_ext = ('readme', 'py', 'wav', 'png', 'jpg', 'svg', 'json',
                        'avi', 'gif', 'txt', 'ttf', 'obj', 'mtl', 'kv', 'mpg',
                        'glsl', 'zip')
for root, sub_folders, files in os.walk(join(ROOT, 'examples')):
    for fn in files:
        ext = fn.split('.')[-1].lower()
        if ext not in examples_allowed_ext:
            continue
        filename = join(root, fn)
        rel_dir = os.path.relpath(dirname(filename), ROOT)
        directory = '{}{}'.format(data_file_prefix, rel_dir)
        if directory not in examples:
            examples[directory] = []
        examples[directory].append(filename)

setup(
    version=__version__,
    data_files=list(examples.items()),
)
