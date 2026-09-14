'''
Linux OS drag-out via Xdnd v5 (ctypes + libX11).

Works on X11 and XWayland (requires DISPLAY). Pure Wayland sessions without
XWayland are unsupported. Content is staged lazily on SelectionRequest.
'''

__all__ = ('available', 'begin_drag', 'begin_drag_files')

import ctypes
import os
import sys
import tempfile
import threading
import time
import traceback

from kivy.core.window.drag_export import encode_uri_list

SelectionClear, SelectionRequest, SelectionNotify, ClientMessage = 29, 30, 31, 33
PropModeReplace = 0
Button1Mask = 1 << 8
CurrentTime = 0
XDND_VERSION = 5

Atom = ctypes.c_ulong
XWindow = ctypes.c_ulong
Time = ctypes.c_ulong

_ERR_HANDLER = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)(
    lambda _dpy, _ev: 0)


class _XClientMessageEvent(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_int), ('serial', ctypes.c_ulong),
        ('send_event', ctypes.c_int), ('display', ctypes.c_void_p),
        ('window', XWindow), ('message_type', Atom), ('format', ctypes.c_int),
        ('data', ctypes.c_long * 5)]


class _XSelectionRequestEvent(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_int), ('serial', ctypes.c_ulong),
        ('send_event', ctypes.c_int), ('display', ctypes.c_void_p),
        ('owner', XWindow), ('requestor', XWindow), ('selection', Atom),
        ('target', Atom), ('property', Atom), ('time', Time)]


class _XSelectionEvent(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_int), ('serial', ctypes.c_ulong),
        ('send_event', ctypes.c_int), ('display', ctypes.c_void_p),
        ('requestor', XWindow), ('selection', Atom), ('target', Atom),
        ('property', Atom), ('time', Time)]


class XEvent(ctypes.Union):
    _fields_ = [
        ('type', ctypes.c_int),
        ('xclient', _XClientMessageEvent),
        ('xselectionrequest', _XSelectionRequestEvent),
        ('xselection', _XSelectionEvent),
        ('pad', ctypes.c_long * 24)]


def available():
    if not sys.platform.startswith('linux'):
        return False
    if not (os.environ.get('DISPLAY') or '').strip():
        return False
    try:
        ctypes.CDLL('libX11.so.6')
        return True
    except OSError:
        return False


def _staging_root():
    return os.path.join(tempfile.gettempdir(), 'kivy-dnd')


def _sweep_stale_staging(max_age_s=86400.0):
    import shutil
    base = _staging_root()
    try:
        for name in os.listdir(base):
            path = os.path.join(base, name)
            if (name.startswith('dnd-') and os.path.isdir(path)
                    and time.time() - os.path.getmtime(path) > max_age_s):
                shutil.rmtree(path, ignore_errors=True)
    except OSError:
        pass


class _Xdnd(object):
    def __init__(self, items, log, on_complete=None):
        self.items = items
        self.log = log
        self.on_complete = on_complete
        self.x = ctypes.CDLL('libX11.so.6')
        self.x.XOpenDisplay.restype = ctypes.c_void_p
        for fn in ('XDefaultRootWindow', 'XCreateSimpleWindow', 'XInternAtom'):
            getattr(self.x, fn).restype = ctypes.c_ulong
        self.x.XGetWindowProperty.argtypes = [
            ctypes.c_void_p, XWindow, Atom, ctypes.c_long, ctypes.c_long,
            ctypes.c_int, Atom, ctypes.POINTER(Atom),
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_void_p)]
        self.x.XSetErrorHandler(_ERR_HANDLER)
        self.dpy = self.x.XOpenDisplay(None)
        if not self.dpy:
            raise OSError('XOpenDisplay failed')
        self.root = self.x.XDefaultRootWindow(ctypes.c_void_p(self.dpy))
        self.win = self.x.XCreateSimpleWindow(
            ctypes.c_void_p(self.dpy), self.root, -10, -10, 1, 1, 0, 0, 0)
        self.atoms = {
            n: self.x.XInternAtom(ctypes.c_void_p(self.dpy), n.encode(), False)
            for n in (
                'XdndSelection', 'XdndAware', 'XdndEnter', 'XdndPosition',
                'XdndStatus', 'XdndLeave', 'XdndDrop', 'XdndFinished',
                'XdndActionCopy', 'XdndTypeList', 'text/uri-list')}
        self.x.XSetSelectionOwner(
            ctypes.c_void_p(self.dpy), self.atoms['XdndSelection'],
            self.win, CurrentTime)
        self.target = 0
        self.accepted = False
        self.staged = []

    def _send_xdnd(self, to_win, name, l0, l1=0, l2=0, l3=0, l4=0):
        ev = XEvent()
        ev.xclient.type = ClientMessage
        ev.xclient.display = self.dpy
        ev.xclient.window = to_win
        ev.xclient.message_type = self.atoms[name]
        ev.xclient.format = 32
        for i, v in enumerate((l0, l1, l2, l3, l4)):
            ev.xclient.data[i] = v
        self.x.XSendEvent(
            ctypes.c_void_p(self.dpy), to_win, False, 0, ctypes.byref(ev))
        self.x.XFlush(ctypes.c_void_p(self.dpy))

    def _xdnd_aware(self, w):
        at, fmt = Atom(0), ctypes.c_int(0)
        n, after, data = (
            ctypes.c_ulong(0), ctypes.c_ulong(0), ctypes.c_void_p(None))
        r = self.x.XGetWindowProperty(
            ctypes.c_void_p(self.dpy), w, self.atoms['XdndAware'],
            0, 1, False, 0, ctypes.byref(at), ctypes.byref(fmt),
            ctypes.byref(n), ctypes.byref(after), ctypes.byref(data))
        ok = (r == 0 and n.value > 0)
        if data:
            self.x.XFree(data)
        return ok

    def _window_under_pointer(self):
        root_r, child_r = XWindow(0), XWindow(0)
        rx, ry, wx, wy = (ctypes.c_int(0) for _ in range(4))
        mask = ctypes.c_uint(0)
        self.x.XQueryPointer(
            ctypes.c_void_p(self.dpy), self.root, ctypes.byref(root_r),
            ctypes.byref(child_r), ctypes.byref(rx), ctypes.byref(ry),
            ctypes.byref(wx), ctypes.byref(wy), ctypes.byref(mask))
        aware, cur = 0, child_r.value
        while cur:
            if self._xdnd_aware(cur):
                aware = cur
                break
            nx, ny, child2 = ctypes.c_int(0), ctypes.c_int(0), XWindow(0)
            self.x.XTranslateCoordinates(
                ctypes.c_void_p(self.dpy), self.root, cur,
                rx, ry, ctypes.byref(nx), ctypes.byref(ny),
                ctypes.byref(child2))
            cur = child2.value
        return rx.value, ry.value, bool(mask.value & Button1Mask), aware

    def _stage_uris(self):
        if not self.staged:
            base = os.path.join(_staging_root(), 'dnd-%d' % int(time.time()))
            os.makedirs(base, exist_ok=True)
            for item in self.items:
                try:
                    dest = os.path.join(base, item.name)
                    err = item.provide(dest)
                    if err:
                        self.log('warn', 'drag-out fetch of %r failed: %s' % (
                            item.name, err))
                    elif os.path.exists(dest):
                        self.staged.append(dest)
                except Exception as exc:
                    self.log('warn', 'drag-out fetch of %r failed: %s' % (
                        item.name, exc))
        return encode_uri_list(self.staged)

    def run(self, timeout=600.0):
        dropped, finished = False, False
        deadline = time.monotonic() + timeout
        seen_held = False
        grace_until = time.monotonic() + 1.0
        accepted_drop = False
        try:
            while time.monotonic() < deadline:
                while self.x.XPending(ctypes.c_void_p(self.dpy)):
                    ev = XEvent()
                    self.x.XNextEvent(ctypes.c_void_p(self.dpy), ctypes.byref(ev))
                    if ev.type == ClientMessage:
                        mt = ev.xclient.message_type
                        if mt == self.atoms['XdndStatus']:
                            self.accepted = bool(ev.xclient.data[1] & 1)
                        elif mt == self.atoms['XdndFinished']:
                            finished = True
                    elif ev.type == SelectionRequest:
                        req = ev.xselectionrequest
                        uris = self._stage_uris()
                        self.x.XChangeProperty(
                            ctypes.c_void_p(self.dpy), req.requestor,
                            req.property, req.target, 8, PropModeReplace,
                            uris, len(uris))
                        out = XEvent()
                        out.xselection.type = SelectionNotify
                        out.xselection.display = self.dpy
                        out.xselection.requestor = req.requestor
                        out.xselection.selection = req.selection
                        out.xselection.target = req.target
                        out.xselection.property = req.property
                        out.xselection.time = req.time
                        self.x.XSendEvent(
                            ctypes.c_void_p(self.dpy), req.requestor, False, 0,
                            ctypes.byref(out))
                        self.x.XFlush(ctypes.c_void_p(self.dpy))
                if finished:
                    accepted_drop = True
                    return True
                if dropped:
                    time.sleep(0.02)
                    continue
                px, py, held, aware = self._window_under_pointer()
                if held:
                    seen_held = True
                elif not seen_held:
                    if time.monotonic() > grace_until:
                        return False
                    time.sleep(1 / 60)
                    continue
                if aware != self.target:
                    if self.target:
                        self._send_xdnd(self.target, 'XdndLeave', self.win)
                    self.target, self.accepted = aware, False
                    if aware:
                        self._send_xdnd(
                            aware, 'XdndEnter', self.win, XDND_VERSION << 24,
                            self.atoms['text/uri-list'])
                if self.target:
                    self._send_xdnd(
                        self.target, 'XdndPosition', self.win, 0,
                        (px << 16) | (py & 0xFFFF), CurrentTime,
                        self.atoms['XdndActionCopy'])
                if not held:
                    if self.target and self.accepted:
                        self._send_xdnd(
                            self.target, 'XdndDrop', self.win, 0, CurrentTime)
                        dropped = True
                        deadline = time.monotonic() + 120.0
                        continue
                    if self.target:
                        self._send_xdnd(self.target, 'XdndLeave', self.win)
                    return False
                time.sleep(1 / 30)
            return dropped
        finally:
            if self.on_complete is not None:
                try:
                    self.on_complete(accepted_drop or dropped)
                except Exception:
                    pass
            try:
                self.x.XDestroyWindow(ctypes.c_void_p(self.dpy), self.win)
                self.x.XCloseDisplay(ctypes.c_void_p(self.dpy))
            except Exception:
                pass


def begin_drag_files(items, action='copy', on_complete=None, log=None):
    log = log or (lambda *a: None)
    if not available() or not items:
        return False
    _sweep_stale_staging()
    try:
        session = _Xdnd(items, log, on_complete=on_complete)
    except Exception as exc:
        log('warn', 'drag-out unavailable (%s: %s)' % (type(exc).__name__, exc))
        traceback.print_exc(file=sys.stderr)
        return False
    threading.Thread(
        target=session.run, name='kivy-xdnd-source', daemon=True).start()
    return True


def begin_drag(mime_types, data_provider, action='copy', on_complete=None,
               log=None):
    log = log or (lambda *a: None)
    mime_types = [m.lower() for m in (mime_types or ())]
    if 'text/uri-list' in mime_types:
        log('warn', 'Linux begin_drag(text/uri-list): use begin_drag_files')
        return False
    if 'text/plain' in mime_types:
        log('warn', 'Linux begin_drag(text/plain) not implemented yet')
        return False
    log('warn', 'Linux begin_drag: unsupported mime_types %s' % mime_types)
    return False
