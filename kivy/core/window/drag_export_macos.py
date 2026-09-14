'''
macOS OS drag-out via AppKit + pyobjus.

Eager ``NSURL`` staging + ``NSDraggingSource`` via ``@protocol`` on methods
(requires pyobjus with ``setReturnValue:`` in ``forwardInvocation``).

- Never synthesize an ``NSEvent`` (segfault); wait for a real left-mouse event.
- Do not call ``iconForFile:`` via pyobjus; do not pin ``currentEvent``.
- Pin items / source / session we create.

Trade-off: files materialize when the drag starts, not only on drop.
'''

__all__ = ('available', 'begin_drag', 'begin_drag_files')

import os
import sys
import tempfile
import traceback

_LIVE = []
_STAGING_DIRS = []
_ARMED = {'trigger': None}
_PROTOCOLS_READY = False

NSEventTypeLeftMouseDown = 1
NSEventTypeLeftMouseUp = 2
NSEventTypeLeftMouseDragged = 6
NSDragOperationCopy = 1


def _objc(value):
    return value() if callable(value) else value


def available():
    if sys.platform != 'darwin':
        return False
    try:
        from pyobjus import autoclass  # noqa: F401
        from pyobjus.dylib_manager import load_framework, INCLUDE
        load_framework(INCLUDE.AppKit)
        return True
    except Exception:
        return False


def _ensure_protocols():
    global _PROTOCOLS_READY
    if _PROTOCOLS_READY:
        return
    from pyobjus.protocols import protocols
    protocols['NSDraggingSource'] = {
        'draggingSession:sourceOperationMaskForDraggingContext:': (
            'Q24@0:4@8q12', 'Q32@0:8@16q24'),
    }
    _PROTOCOLS_READY = True


def _new_drag_source():
    '''``@protocol`` goes on methods; bridge with convert_py_to_nsobject.'''
    _ensure_protocols()
    from pyobjus import convert_py_to_nsobject, protocol

    class DragSource(object):
        @protocol('NSDraggingSource')
        def draggingSession_sourceOperationMaskForDraggingContext_(
                self, session, context):
            return NSDragOperationCopy

    py_source = DragSource()
    return py_source, convert_py_to_nsobject(py_source)


def _cancel_arm():
    trigger = _ARMED.get('trigger')
    if trigger is not None:
        try:
            trigger.cancel()
        except Exception:
            pass
    _ARMED['trigger'] = None


def _stage_items_for_url_drag(items):
    root = tempfile.mkdtemp(prefix='kivy-drag-export-')
    _STAGING_DIRS.append(root)
    paths = []
    for item in items:
        name = os.path.basename(str(item.name).rstrip('/\\')) or 'item'
        dest = os.path.join(root, name)
        if item.is_dir:
            err = item.provide(dest)
            if err:
                raise RuntimeError(str(err))
            if not os.path.isdir(dest):
                raise RuntimeError('provide did not create directory: %s' % dest)
        else:
            parent = os.path.dirname(dest)
            if parent:
                os.makedirs(parent, exist_ok=True)
            err = item.provide(dest)
            if err:
                raise RuntimeError(str(err))
            if not os.path.exists(dest):
                raise RuntimeError('provide did not create file: %s' % dest)
        paths.append(dest)
    return paths


def _start_session(view, drag_items_ns, event, source, keep, n_items, log,
                   how='direct'):
    session = view.beginDraggingSessionWithItems_event_source_(
        drag_items_ns, event, source)
    keep.append(session)
    log('info', 'drag-out: URL session started for %d item(s) (%s)' % (
        n_items, how))


def _arm_until_live_mouse(view, drag_items_ns, source, keep, n_items, log,
                          timeout=1.5):
    from kivy.clock import Clock
    from pyobjus import autoclass

    NSApplication = autoclass('NSApplication')
    _cancel_arm()
    state = {'fired': False, 'elapsed': 0.0}

    def _tick(dt):
        if state['fired']:
            return False
        state['elapsed'] += dt
        app = NSApplication.sharedApplication()
        ev = app.currentEvent()
        cur_t = int(_objc(ev.type)) if ev is not None else -1
        if cur_t in (NSEventTypeLeftMouseDown, NSEventTypeLeftMouseDragged):
            state['fired'] = True
            _ARMED['trigger'] = None
            try:
                _start_session(
                    view, drag_items_ns, ev, source, keep, n_items, log,
                    how='live mouse type %s' % cur_t)
            except Exception as exc:
                log('warn', 'drag-out: armed begin failed (%s: %s)' % (
                    type(exc).__name__, exc))
                traceback.print_exc(file=sys.stderr)
            return False
        if cur_t == NSEventTypeLeftMouseUp or state['elapsed'] >= timeout:
            state['fired'] = True
            _ARMED['trigger'] = None
            log('warn', 'drag-out: no live mouse-drag within %.1fs — '
                        'session NOT started' % timeout)
            return False
        return True

    _ARMED['trigger'] = Clock.schedule_interval(_tick, 0)
    log('info', 'drag-out: ARMED — waiting for leftMouseDragged/Down')


def _set_dragging_frame(di, x, y, w=64.0, h=64.0):
    '''Set draggingFrame without pyobjus NSRect (ffi passes size as 0x0).'''
    import ctypes
    from ctypes import CFUNCTYPE, Structure, c_double, c_void_p, c_char_p

    class CGPoint(Structure):
        _fields_ = [('x', c_double), ('y', c_double)]

    class CGSize(Structure):
        _fields_ = [('width', c_double), ('height', c_double)]

    class CGRect(Structure):
        _fields_ = [('origin', CGPoint), ('size', CGSize)]

    objc = ctypes.CDLL('/usr/lib/libobjc.A.dylib')
    objc.sel_registerName.restype = c_void_p
    objc.sel_registerName.argtypes = [c_char_p]
    sel = objc.sel_registerName(b'setDraggingFrame:')
    msg = CFUNCTYPE(None, c_void_p, c_void_p, CGRect)(('objc_msgSend', objc))
    msg(di.get_address(), sel,
        CGRect(CGPoint(float(x), float(y)), CGSize(float(w), float(h))))


def begin_drag_files(items, action='copy', on_complete=None, log=None):
    log = log or (lambda *a: None)
    if not items or not available():
        return False
    try:
        from pyobjus import autoclass, objc_str
        from pyobjus.dylib_manager import load_framework, INCLUDE

        load_framework(INCLUDE.AppKit)
        load_framework(INCLUDE.Foundation)

        paths = _stage_items_for_url_drag(items)
        log('info', 'drag-out: staged %d item(s)' % len(paths))

        NSApplication = autoclass('NSApplication')
        NSDraggingItem = autoclass('NSDraggingItem')
        NSMutableArray = autoclass('NSMutableArray')
        NSURL = autoclass('NSURL')

        app = NSApplication.sharedApplication()
        event = app.currentEvent()
        win = app.keyWindow() or app.mainWindow()
        if win is None:
            log('warn', 'drag-out bail: no key/main window')
            return False
        view = win.contentView()
        if view is None:
            log('warn', 'drag-out bail: no contentView')
            return False

        cur_t = int(_objc(event.type)) if event is not None else -1
        have_mouse = cur_t in (
            NSEventTypeLeftMouseDown, NSEventTypeLeftMouseDragged)
        if have_mouse:
            loc = _objc(event.locationInWindow)
        else:
            loc = _objc(win.mouseLocationOutsideOfEventStream)
            log('info', 'drag-out: currentEvent type %s — will wait for '
                        'live mouse event' % cur_t)

        x, y = float(loc.x), float(loc.y)
        drag_items_ns = NSMutableArray.array()
        keep = [paths]
        for i, path in enumerate(paths):
            url = NSURL.fileURLWithPath_(objc_str(path))
            di = NSDraggingItem.alloc().initWithPasteboardWriter_(url)
            _set_dragging_frame(di, x + i * 4, y - i * 4)
            drag_items_ns.addObject_(di)
            keep.extend((di, url))

        py_source, source = _new_drag_source()
        keep.extend((drag_items_ns, view, win, py_source, source))
        _LIVE.append(keep)
        del _LIVE[:-8]

        if have_mouse:
            _start_session(
                view, drag_items_ns, event, source, keep, len(items), log)
        else:
            _arm_until_live_mouse(
                view, drag_items_ns, source, keep, len(items), log)

        if on_complete is not None:
            log('info', 'drag-out: on_complete not reported on macOS yet')
        return True
    except Exception as exc:
        log('warn', 'drag-out unavailable (%s: %s)' % (type(exc).__name__, exc))
        traceback.print_exc(file=sys.stderr)
        return False


def begin_drag(mime_types, data_provider, action='copy', on_complete=None,
               log=None):
    log = log or (lambda *a: None)
    mime_types = [m.lower() for m in (mime_types or ())]
    if 'text/uri-list' in mime_types:
        log('warn', 'macOS begin_drag(text/uri-list): use begin_drag_files')
        return False
    if 'text/plain' in mime_types:
        log('warn', 'macOS begin_drag(text/plain) not implemented yet')
        return False
    log('warn', 'macOS begin_drag: unsupported mime_types %s' % mime_types)
    return False
