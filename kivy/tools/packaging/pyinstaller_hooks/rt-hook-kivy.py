from os.path import join, dirname
from os import environ, chdir
import sys

root = 'kivy_install'
if hasattr(sys, '_MEIPASS'):
    # PyInstaller >= 1.6
    chdir(sys._MEIPASS)
    root = join(sys._MEIPASS, root)
elif '_MEIPASS2' in environ:
    # PyInstaller < 1.6 (tested on 1.5 only)
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
