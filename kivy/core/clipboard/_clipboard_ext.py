'''
Clipboard ext: base class for external command clipboards
'''

__all__ = ('ClipboardExternalBase', )

from kivy.core.clipboard import ClipboardBase


class ClipboardExternalBase(ClipboardBase):
    @staticmethod
    def _clip(inout, selection):
        raise NotImplementedError('clip method not implemented')

    def get(self, mimetype='text/plain'):
        p = self._clip('out', 'clipboard')
        data, _ = p.communicate()
        return data

    def put(self, data, mimetype='text/plain'):
        p = self._clip('in', 'clipboard')
        p.communicate(data)

    def get_cutbuffer(self):
        p = self._clip('out', 'primary')
        data, _ = p.communicate()
        return data.decode('utf8')

    def set_cutbuffer(self, data):
        if not isinstance(data, bytes):
            data = data.encode('utf8')
        p = self._clip('in', 'primary')
        p.communicate(data)

    def get_types(self):
        return [u'text/plain']
