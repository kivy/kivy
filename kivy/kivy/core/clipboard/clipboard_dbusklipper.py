'''
Clipboard Dbus: an implementation of the Clipboard using dbus and klipper.
'''

__all__ = ('ClipboardDbusKlipper', )

from kivy.utils import platform
from kivy.core.clipboard import ClipboardBase

if platform != 'linux':
    raise SystemError('unsupported platform for dbus kde clipboard')

try:
    import dbus
    bus = dbus.SessionBus()
    proxy = bus.get_object("org.kde.klipper", "/klipper")
except:
    raise


class ClipboardDbusKlipper(ClipboardBase):

    _is_init = False

    def init(self):
        if ClipboardDbusKlipper._is_init:
            return
        self.iface = dbus.Interface(proxy, "org.kde.klipper.klipper")
        ClipboardDbusKlipper._is_init = True

    def get(self, mimetype='text/plain'):
        self.init()
        return str(self.iface.getClipboardContents())

    def put(self, data, mimetype='text/plain'):
        self.init()
        self.iface.setClipboardContents(data.replace('\x00', ''))

    def get_types(self):
        self.init()
        return [u'text/plain']
