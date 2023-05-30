'''
Clipboard xsel: an implementation of the Clipboard using xsel command line
                tool.
'''

__all__ = ('ClipboardXsel', )

from kivy.utils import platform
from kivy.core.clipboard._clipboard_ext import ClipboardExternalBase

if platform != 'linux':
    raise SystemError('unsupported platform for xsel clipboard')

try:
    import subprocess
    p = subprocess.Popen(['xsel'], stdout=subprocess.PIPE)
    p.communicate()
except:
    raise


class ClipboardXsel(ClipboardExternalBase):
    @staticmethod
    def _clip(inout, selection):
        pipe = {'std' + inout: subprocess.PIPE}
        sel = 'b' if selection == 'clipboard' else selection[0]
        io = inout[0]
        return subprocess.Popen(
            ['xsel', '-' + sel + io], **pipe)
