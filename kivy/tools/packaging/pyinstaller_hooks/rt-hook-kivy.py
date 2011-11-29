from os.path import join, dirname
from os import environ, chdir
import sys

root = 'kivy_install'
if '_MEIPASS2' in environ:
    chdir(environ['_MEIPASS2'])
    root = join(environ['_MEIPASS2'], root)
else:
    chdir(dirname(sys.argv[0]))
    root = join(dirname(sys.argv[0]), root)

sys.path += [join(root, '_libs')]

environ['KIVY_DATA_DIR'] = join(root, 'data')
environ['KIVY_EXTS_DIR'] = join(root, 'extensions')
environ['KIVY_MODULES_DIR'] = join(root, 'modules')
environ['KIVY_EMBED'] = '1'
