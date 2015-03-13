'''
Clipboard Android
=================

Android implementation of Clipboard provider, using Pyjnius.
'''

__all__ = ('ClipboardAndroid', )

from kivy.core.clipboard import ClipboardBase
from jnius import autoclass
from android.runnable import run_on_ui_thread

AndroidString = autoclass('java.lang.String')
PythonActivity = autoclass('org.renpy.android.PythonActivity')
Context = autoclass('android.content.Context')
VER = autoclass('android.os.Build$VERSION')
sdk = VER.SDK_INT


class ClipboardAndroid(ClipboardBase):

    def __init__(self):
        super(ClipboardAndroid, self).__init__()
        self._clipboard = None
        self._data = dict()
        self._data['text/plain'] = None
        self._data['application/data'] = None
        PythonActivity._clipboard = None

    def get(self, mimetype='text/plain'):
        return self._get(mimetype)

    def put(self, data, mimetype='text/plain'):
        self._set(data, mimetype)

    def get_types(self):
        return list(self._data.keys())

    @run_on_ui_thread
    def _initialize_clipboard(self):
        PythonActivity._clipboard = PythonActivity.getSystemService(
            Context.CLIPBOARD_SERVICE)

    def _get_clipboard(f):
        def called(*args, **kargs):
            self = args[0]
            if not PythonActivity._clipboard:
                self._initialize_clipboard()
                import time
                while not PythonActivity._clipboard:
                    time.sleep(.01)
            return f(*args, **kargs)
        return called

    @_get_clipboard
    def _get(self, mimetype='text/plain'):
        clippy = PythonActivity._clipboard
        if sdk < 11:
            data = clippy.getText()
        else:
            ClipDescription = autoclass('android.content.ClipDescription')
            primary_clip = clippy.getPrimaryClip()
            if primary_clip and clippy.getPrimaryClipDescription().hasMimeType(
                    ClipDescription.MIMETYPE_TEXT_PLAIN):
                data = primary_clip.getItemAt(0).getText().toString()
            else:
                # TODO: non text data types Not yet implemented
                data = ''
        return data

    @_get_clipboard
    def _set(self, data, mimetype):
        clippy = PythonActivity._clipboard

        if sdk < 11:
            #versions previous to honeycomb
            clippy.setText(AndroidString(data))
        else:
            ClipData = autoclass('android.content.ClipData')
            new_clip = ClipData.newPlainText(AndroidString(""),
                                         AndroidString(data))
            # put text data onto clipboard
            clippy.setPrimaryClip(new_clip)
