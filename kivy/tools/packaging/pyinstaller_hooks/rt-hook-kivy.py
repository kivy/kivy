from os.path import join, dirname
from os import environ
import sys

root = 'kivy_install'
if '_MEIPASS2' in environ:
    root = join(environ['_MEIPASS2'], root)
else:
    root = join(dirname(sys.argv[0]), root)

environ['KIVY_DATA_DIR'] = join(root, 'data')
environ['KIVY_EXTS_DIR'] = join(root, 'extensions')
environ['KIVY_MODULES_DIR'] = join(root, 'modules')

