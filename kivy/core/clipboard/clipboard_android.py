'''
Clipboard Android:
'''

__all__ = ('ClipboardAndroid', )

from kivy.core.clipboard import ClipboardBase
from kivy.clock import Clock
from jnius import autoclass, cast
from android.runnable import run_on_ui_thread

AndroidString = autoclass('java.lang.String')
PythonActivity = autoclass('org.renpy.android.PythonActivity')
Context = autoclass('android.content.Context') 
ClipData = autoclass('android.content.ClipData')
ClipDescription = autoclass('android.content.ClipDescription')


class ClipboardAndroid(ClipboardBase):

    def __init__(self):
        super(ClipboardAndroid, self).__init__()
        self._clipboard = None
        self._data = dict()
        self._data['text/plain'] = None
        self._data['application/data'] = None
        self._get_clipboard_service()

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

    def _get_clipboard_service(self):
        if not self._clipboard:
            self._initialize_clipboard()
            try:
                self._clipboard = PythonActivity._clipboard
            except AttributeError:
                # don't know why but this happens when trying to access the
                # clipboard for the first time. Works after that
                Clock.schedule_once(lambda dt: self._get_clipboard_service())
                return
        return self._clipboard

    def _get(self, mimetype='text/plain'):
        clippy = self._get_clipboard_service()
        primary_clip = clippy.getPrimaryClip()
        if primary_clip and clippy.getPrimaryClipDescription().hasMimeType(
            ClipDescription.MIMETYPE_TEXT_PLAIN):
            data = primary_clip.getItemAt(0).getText().toString()
        else:
            # TODO: non text data types Not yet implemented
            data = ''
        return data

    def _set(self, data, mimetype):
        clippy = self._get_clipboard_service()
        new_clip = ClipData.newPlainText(AndroidString(""),
                                         AndroidString(data))
        # put text data onto clipboard
        clippy.setPrimaryClip(new_clip)
