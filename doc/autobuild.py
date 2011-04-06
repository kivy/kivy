'''
Script to generate Kivy API from source code.

Code is messy, but working.
Be careful if you change anything in !

'''

ignore_list = (
    'kivy.factory_registers',
    'kivy.graphics.buffer',
    'kivy.graphics.shader',
    'kivy.graphics.vbo',
    'kivy.graphics.vertex',
)

import os
import sys
import re
from glob import glob

os.environ['KIVY_SHADOW_WINDOW'] = '0'
import kivy

# force loading of kivy modules
import kivy.app
import kivy.core.audio
import kivy.core.camera
import kivy.core.clipboard
import kivy.core.gl
import kivy.core.image
import kivy.core.spelling
import kivy.core.text
import kivy.core.video
import kivy.core.window
import kivy.ext
import kivy.graphics
import kivy.animation
from kivy.factory import Factory

# force loading of all classes from factory
for x in Factory.classes:
    getattr(Factory, x)


# Directory of doc
base_dir = os.path.dirname(__file__)
dest_dir = os.path.join(base_dir, 'sources')
examples_framework_dir = os.path.join(base_dir, '..', 'examples', 'framework')

def writefile(filename, data):
    global dest_dir
    print 'write', filename
    f = os.path.join(dest_dir, filename)
    h = open(f, 'w')
    h.write(data)
    h.close()


# Activate Kivy modules
'''
for k in kivy.kivy_modules.list().keys():
    kivy.kivy_modules.import_module(k)
'''

# Search all kivy module
l = [(x, sys.modules[x], os.path.basename(sys.modules[x].__file__).rsplit('.', 1)[0]) for x in sys.modules if x.startswith('kivy') and sys.modules[x]]

# Extract packages from modules
packages = []
modules = {}
for name, module, filename in l:
    if name in ignore_list:
        continue
    if filename == '__init__':
        packages.append(name)
    else:
        if hasattr(module, '__all__'):
            modules[name] = module.__all__
        else:
            modules[name] = [x for x in dir(module) if not x.startswith('__')]

packages.sort()

# Create index
api_index = \
'''API Reference
-------------

The API reference is a lexicographic list of all the different classes,
methods and features that Kivy offers.

.. toctree::
    :maxdepth: 2

'''
for package in [x for x in packages if len(x.split('.')) <= 2]:
    api_index += "    api-%s.rst\n" % package

writefile('api-index.rst', api_index)

# Create index for all packages
template = \
'''==========================================================================================================
$SUMMARY
==========================================================================================================

$EXAMPLES_REF

.. automodule:: $PACKAGE
    :members:
    :show-inheritance:

.. toctree::

$EXAMPLES
'''

template_examples = \
'''.. _example-reference%d:

Examples
--------

%s
'''

template_examples_ref = \
'''# :ref:`Jump directly to Examples <example-reference%d>`'''

for package in packages:
    try:
        summary = [x for x in sys.modules[package].__doc__.split("\n") if len(x) > 1][0]
    except:
        summary = 'NO DOCUMENTATION (package %s)' % package
    t = template.replace('$SUMMARY', summary)
    t = t.replace('$PACKAGE', package)
    t = t.replace('$EXAMPLES_REF', '')
    t = t.replace('$EXAMPLES', '')

    # search packages
    for subpackage in packages:
        packagemodule = subpackage.rsplit('.', 1)[0]
        if packagemodule != package or len(subpackage.split('.')) <= 2:
            continue
        t += "    api-%s.rst\n" % subpackage

    # search modules
    m = modules.keys()
    m.sort()
    for module in m:
        packagemodule = module.rsplit('.', 1)[0]
        if packagemodule != package:
            continue
        t += "    api-%s.rst\n" % module

    writefile('api-%s.rst' % package, t)


# Create index for all module
m = modules.keys()
m.sort()
refid = 0
for module in m:
    try:
        summary = [x for x in sys.modules[module].__doc__.split("\n") if len(x) > 1][0]
    except:
        summary = 'NO DOCUMENTATION (module %s)' % module

    # search examples
    example_output = []
    example_prefix = module
    if module.startswith('kivy.'):
        example_prefix = module[5:]
    example_prefix = example_prefix.replace('.', '_')

    # try to found any example in framework directory
    list_examples = glob('%s*.py' % os.path.join(examples_framework_dir, example_prefix))
    for x in list_examples:
        # extract filename without directory
        xb = os.path.basename(x)

        # add a section !
        example_output.append('File :download:`%s <%s>` ::' % (
            xb, os.path.join('..', x)))

        # put the file in
        with open(x, 'r') as fd:
            d = fd.read().strip()
            d = '\t' + '\n\t'.join(d.split('\n'))
            example_output.append(d)

    t = template.replace('$SUMMARY', summary)
    t = t.replace('$PACKAGE', module)
    if len(example_output):
        refid += 1
        example_output = template_examples % (refid, '\n\n\n'.join(example_output))
        t = t.replace('$EXAMPLES_REF', template_examples_ref % refid)
        t = t.replace('$EXAMPLES', example_output)
    else:
        t = t.replace('$EXAMPLES_REF', '')
        t = t.replace('$EXAMPLES', '')
    writefile('api-%s.rst' % module, t)


# Generation finished
print 'Generation finished, do make html'
