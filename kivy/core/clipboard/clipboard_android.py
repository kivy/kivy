'''
Clipboard Android
=================

Android implementation of Clipboard provider, using Pyjnius.
'''

__all__ = ('ClipboardAndroid', )

import threading

from kivy import Logger
from kivy.core.clipboard import ClipboardBase
from kivy.mobile._platform.android import get_app_context, run_on_ui_thread
from jnius import autoclass

AndroidString = autoclass('java.lang.String')
Context = autoclass('android.content.Context')
VER = autoclass('android.os.Build$VERSION')
sdk = VER.SDK_INT

# The ClipboardManager, fetched once on the UI thread.  Process-wide rather than
# per-instance because it comes from the Application context, which outlives any
# one Activity.
_clipboard = None


class ClipboardAndroid(ClipboardBase):

    def __init__(self):
        super(ClipboardAndroid, self).__init__()
        self._data = dict()
        self._data['text/plain'] = None
        self._data['application/data'] = None

    def get(self, mimetype='text/plain'):
        return self._get(mimetype).encode('utf-8')

    def put(self, data, mimetype='text/plain'):
        self._set(data, mimetype)

    def get_types(self):
        return list(self._data.keys())

    def _initialize_clipboard(self):
        '''Fetch the ClipboardManager, waiting for the UI thread to deliver it.

        The lookup has to happen on the UI thread, so the failure has to be
        carried back rather than raised in place: without that, a Context we
        cannot reach would leave the wait below hanging forever instead of
        reporting itself.
        '''
        failure = []
        done = threading.Event()

        def work():
            global _clipboard
            try:
                _clipboard = get_app_context().getSystemService(
                    Context.CLIPBOARD_SERVICE)
            except Exception as exc:
                failure.append(exc)
            finally:
                done.set()

        run_on_ui_thread(work)
        if not done.wait(timeout=5.0):
            raise TimeoutError(
                'Clipboard: timed out waiting for the UI thread to '
                'initialize the ClipboardManager')
        if failure:
            raise failure[0]

    def _get_clipboard(f):
        def called(*args, **kargs):
            if not _clipboard:
                args[0]._initialize_clipboard()
            return f(*args, **kargs)
        return called

    @_get_clipboard
    def _get(self, mimetype='text/plain'):
        clippy = _clipboard
        data = ''
        if sdk < 11:
            data = clippy.getText()
        else:
            primary_clip = clippy.getPrimaryClip()
            if primary_clip:
                try:
                    data = primary_clip.getItemAt(0).coerceToText(get_app_context())
                except Exception:
                    Logger.exception('Clipboard: failed to paste')
        return data

    @_get_clipboard
    def _set(self, data, mimetype):
        clippy = _clipboard

        if sdk < 11:
            # versions previous to honeycomb
            clippy.setText(AndroidString(data))
        else:
            ClipData = autoclass('android.content.ClipData')
            new_clip = ClipData.newPlainText(AndroidString(""),
                                         AndroidString(data))
            # put text data onto clipboard
            clippy.setPrimaryClip(new_clip)
