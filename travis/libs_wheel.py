import sys
import os
from os.path import join, dirname
from subprocess import check_call, CalledProcessError


version = "0.0.1"
file, folder, name, license = sys.argv
folder = folder.replace('//', '/')
libs = [
    lib for lib in os.listdir(join(folder, 'kivy', 'deps')) if '.so' in lib
]

# change path manually, because auditwheel doesn't do it in some libs
for lib in libs:
    print('Setting RPATH manually: %s to "$ORIGIN/../../deps"' % lib)
    try:
        check_call([  # chrpath -r <new_path> <executable>
            'chrpath', '-r',
            '$ORIGIN/../../deps',
            join(folder, 'kivy', 'deps', lib)
        ])
    except CalledProcessError as e:
        print('Failed with:', e)

package = {}
package['kivy.deps'] = []
for lib in libs:
    package['kivy.deps'].append(lib)
print(name, os.listdir(join(folder, 'kivy', 'deps')))

with open(join(dirname(file), 'setup.py.tmpl')) as f:
    with open(join(folder, 'setup.py'), 'w') as s:
        s.write(f.read().format(
            package,
            name,
            version,
            license,
            name
        ))
