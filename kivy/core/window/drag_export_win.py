'''
Windows OS drag-out via OLE DoDragDrop + pywin32.

Publishes CFSTR_FILEDESCRIPTORW / CFSTR_FILECONTENTS virtual files. Content is
fetched lazily inside IDataObject.GetData when Explorer requests a stream.
'''

__all__ = ('available', 'begin_drag', 'begin_drag_files')

import sys
import traceback

from kivy.core.window.drag_export import group_descriptor_w

DROPEFFECT_COPY = 1
DRAGDROP_S_DROP = 0x00040100
DRAGDROP_S_CANCEL = 0x00040101
DRAGDROP_S_USEDEFAULTCURSORS = 0x00040102
MK_LBUTTON = 1


def available():
    if sys.platform != 'win32':
        return False
    try:
        import pythoncom  # noqa: F401
        import win32com.server.util  # noqa: F401
        return hasattr(__import__('pythoncom'), 'DoDragDrop')
    except Exception:
        return False


def begin_drag_files(items, action='copy', on_complete=None, log=None):
    '''OLE drag of virtual file items.

    Each item.provide(dest_path) is adapted: on Windows Explorer requests bytes
    via FileContents, so provide() is asked to write to a temp path which is
    then read. For directory items, relative tree expansion is the caller's
    responsibility (pass flat file entries with relative names).
    '''
    log = log or (lambda *a: None)
    if not items or not available():
        return False

    # Build descriptor entries: files only get FileContents indexes.
    # Directories are published as directory descriptors (size 0).
    entries = []
    providers = {}
    for item in items:
        entries.append((item.name, bool(item.is_dir), 0))
        if not item.is_dir:
            providers[len(entries) - 1] = item.provide

    def fetch(index):
        provide = providers.get(index)
        if provide is None:
            return None
        import os
        import tempfile
        fd, path = tempfile.mkstemp(prefix='kivy-dnd-')
        os.close(fd)
        try:
            err = provide(path)
            if err:
                log('warn', 'drag-out fetch failed: %s' % err)
                return None
            with open(path, 'rb') as fh:
                return fh.read()
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    return _do_drag_drop(entries, fetch, on_complete=on_complete, log=log)


def begin_drag(mime_types, data_provider, action='copy', on_complete=None,
               log=None):
    log = log or (lambda *a: None)
    mime_types = [m.lower() for m in (mime_types or ())]
    if 'text/plain' in mime_types:
        log('warn', 'Windows begin_drag(text/plain) not implemented yet')
        return False
    if 'text/uri-list' in mime_types:
        log('warn', 'Windows begin_drag(text/uri-list): use begin_drag_files')
        return False
    log('warn', 'Windows begin_drag: unsupported mime_types %s' % mime_types)
    return False


def _do_drag_drop(entries, fetch, on_complete=None, log=None):
    log = log or (lambda *a: None)
    try:
        import pythoncom
        import win32clipboard
        import win32com.server.util

        cf_descriptor = win32clipboard.RegisterClipboardFormat(
            'FileGroupDescriptorW')
        cf_contents = win32clipboard.RegisterClipboardFormat('FileContents')
        group = group_descriptor_w(entries)
        file_indexes = [i for i, (_n, d, _s) in enumerate(entries) if not d]

        class DataObject:
            _com_interfaces_ = [pythoncom.IID_IDataObject]
            _public_methods_ = [
                'GetData', 'GetDataHere', 'QueryGetData',
                'GetCanonicalFormatEtc', 'SetData', 'EnumFormatEtc',
                'DAdvise', 'DUnadvise', 'EnumDAdvise']

            def GetData(self, fe):
                cf, _target, _aspect, lindex, tymed = fe
                if cf == cf_descriptor:
                    med = pythoncom.STGMEDIUM()
                    med.set(pythoncom.TYMED_HGLOBAL, group)
                    return med
                if cf == cf_contents and lindex in file_indexes:
                    data = fetch(lindex)
                    if data is None:
                        raise pythoncom.com_error(
                            -2147287037, 'fetch failed', None, None)
                    stream = pythoncom.CreateStreamOnHGlobal()
                    stream.Write(data)
                    stream.Seek(0, 0)
                    med = pythoncom.STGMEDIUM()
                    med.set(pythoncom.TYMED_ISTREAM, stream)
                    return med
                raise pythoncom.com_error(
                    -2147221404, 'bad format', None, None)

            def GetDataHere(self, *_a):
                raise pythoncom.com_error(-2147221404, '', None, None)

            def QueryGetData(self, fe):
                if fe[0] in (cf_descriptor, cf_contents):
                    return None
                raise pythoncom.com_error(-2147221404, '', None, None)

            def GetCanonicalFormatEtc(self, _fe):
                raise pythoncom.com_error(-2147221404, '', None, None)

            def SetData(self, *_a):
                raise pythoncom.com_error(-2147467263, '', None, None)

            def EnumFormatEtc(self, direction):
                if direction != pythoncom.DATADIR_GET:
                    raise pythoncom.com_error(-2147467263, '', None, None)
                fes = (
                    [(cf_descriptor, None, pythoncom.DVASPECT_CONTENT, -1,
                      pythoncom.TYMED_HGLOBAL)]
                    + [(cf_contents, None, pythoncom.DVASPECT_CONTENT, i,
                        pythoncom.TYMED_ISTREAM) for i in file_indexes])
                return win32com.server.util.wrap(
                    EnumFORMATETC(fes), pythoncom.IID_IEnumFORMATETC)

            def DAdvise(self, *_a):
                raise pythoncom.com_error(-2147221501, '', None, None)

            def DUnadvise(self, *_a):
                raise pythoncom.com_error(-2147221501, '', None, None)

            def EnumDAdvise(self, *_a):
                raise pythoncom.com_error(-2147221501, '', None, None)

        class EnumFORMATETC:
            _com_interfaces_ = [pythoncom.IID_IEnumFORMATETC]
            _public_methods_ = ['Next', 'Skip', 'Reset', 'Clone']

            def __init__(self, fes, pos=0):
                self._fes, self._pos = fes, pos

            def Next(self, count):
                out = self._fes[self._pos:self._pos + count]
                self._pos += len(out)
                return out

            def Skip(self, count):
                self._pos = min(self._pos + count, len(self._fes))
                return None

            def Reset(self):
                self._pos = 0

            def Clone(self):
                return win32com.server.util.wrap(
                    EnumFORMATETC(self._fes, self._pos),
                    pythoncom.IID_IEnumFORMATETC)

        class DropSource:
            _com_interfaces_ = [pythoncom.IID_IDropSource]
            _public_methods_ = ['QueryContinueDrag', 'GiveFeedback']

            def QueryContinueDrag(self, esc, key_state):
                if esc:
                    return DRAGDROP_S_CANCEL
                if not (key_state & MK_LBUTTON):
                    return DRAGDROP_S_DROP
                return None

            def GiveFeedback(self, _effect):
                return DRAGDROP_S_USEDEFAULTCURSORS

        do = win32com.server.util.wrap(DataObject(), pythoncom.IID_IDataObject)
        src = win32com.server.util.wrap(DropSource(), pythoncom.IID_IDropSource)
        pythoncom.OleInitialize()
        accepted = False
        try:
            effect = pythoncom.DoDragDrop(do, src, DROPEFFECT_COPY)
            accepted = bool(effect)
        finally:
            try:
                pythoncom.OleUninitialize()
            except Exception:
                pass
        if on_complete is not None:
            try:
                on_complete(accepted)
            except Exception:
                pass
        return True
    except Exception as exc:
        log('warn', 'drag-out unavailable (%s: %s)' % (type(exc).__name__, exc))
        traceback.print_exc(file=sys.stderr)
        return False
