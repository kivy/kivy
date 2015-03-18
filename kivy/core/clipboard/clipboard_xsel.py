'''
Clipboard xsel: an implementation of the Clipboard using xsel command line tool.
'''

__all__ = ('Clipboardxsel', )

from kivy.utils import platform
from kivy.core.clipboard import ClipboardBase

if platform != 'linux':
    raise SystemError('unsupported platform for xsel clipboard')

try:
    import subprocess
    p = subprocess.Popen(['xsel'], stdout=subprocess.PIPE)
    p.communicate()
except:
    raise


class Clipboardxsel(ClipboardBase):

    def get(self, mimetype='text/plain'):
        p = subprocess.Popen(['xsel', 'b'], stdout=subprocess.PIPE)
        data, _ = p.communicate()
        return data

    def put(self, data, mimetype='text/plain'):
        p = subprocess.Popen(['xsel', '-bi'], stdin=subprocess.PIPE)
        p.communicate(data)

    def get_types(self):
        return 'text/plain'
