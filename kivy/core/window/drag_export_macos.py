'''
macOS OS drag-out via AppKit + pyobjus.

Uses NSFilePromiseProvider (lazy file/folder promises) and NSDraggingSession.
Protocol methods are plain Python functions registered with pyobjus @protocol;
missing protocols are extended on pyobjus.protocols.protocols.
'''

__all__ = ('available', 'begin_drag', 'begin_drag_files')

import sys
import traceback

from pyobjus import protocol

_LIVE = []
_ARMED = {'monitor': None}
_PROTOCOLS_READY = False

NSEventTypeLeftMouseDown = 1
NSEventTypeLeftMouseDragged = 6
NSEventMaskLeftMouseDown = 1 << NSEventTypeLeftMouseDown
NSEventMaskLeftMouseDragged = 1 << NSEventTypeLeftMouseDragged
NSDragOperationCopy = 1


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
    protocols['NSFilePromiseProviderDelegate'] = {
        'filePromiseProvider:fileNameForType:': ('@@:@@', '@@:@@'),
        'filePromiseProvider:writePromiseToURL:completionHandler:': (
            'v@:@@@', 'v@:@@@'),
    }
    protocols.setdefault('NSDraggingSource', {})
    protocols['NSDraggingSource'].update({
        'draggingSession:sourceOperationMaskForDraggingContext:': (
            'Q@:@@', 'Q@:@@'),
        'draggingSession:willBeginAtPoint:': (
            'v@:@{CGPoint=dd}', 'v@:@{CGPoint=dd}'),
        'draggingSession:movedToPoint:': (
            'v@:@{CGPoint=dd}', 'v@:@{CGPoint=dd}'),
        'draggingSession:endedAtPoint:operation:': (
            'v@:@{CGPoint=dd}Q', 'v@:@{CGPoint=dd}Q'),
    })
    _PROTOCOLS_READY = True


def _promise_log(level, msg):
    try:
        from kivy.logger import Logger
        (Logger.warning if level in ('warn', 'error', 'warning')
         else Logger.info)('DragExport: %s' % msg)
    except Exception:
        pass


class FilePromiseDelegate(object):
    '''One promised file/folder. AppKit calls the @protocol methods later.'''

    def __init__(self, name, provide):
        self._name = str(name)
        self._provide = provide

    @protocol('NSFilePromiseProviderDelegate')
    def filePromiseProvider_fileNameForType_(self, provider, file_type):
        _promise_log('info', 'promise: name asked → %s' % self._name)
        from pyobjus import objc_str
        return objc_str(self._name)

    @protocol('NSFilePromiseProviderDelegate')
    def filePromiseProvider_writePromiseToURL_completionHandler_(
            self, provider, url, completion_handler):
        err_msg = None
        try:
            path = url.path.cString()
            if isinstance(path, bytes):
                path = path.decode('utf-8')
            _promise_log('info', 'promise: writing %s → %s' % (self._name, path))
            err_msg = self._provide(path)
            if err_msg:
                _promise_log('warn', 'promise: %s FAILED: %s' % (
                    self._name, err_msg))
        except Exception as exc:
            err_msg = '%s: %s' % (type(exc).__name__, exc)
            _promise_log('warn', 'promise: %s FAILED: %s' % (
                self._name, err_msg))
        if completion_handler is None:
            return
        try:
            if err_msg:
                from pyobjus import autoclass, objc_str
                NSError = autoclass('NSError')
                info = autoclass('NSDictionary').dictionaryWithObject_forKey_(
                    objc_str(str(err_msg)),
                    objc_str('NSLocalizedDescription'))
                error = NSError.errorWithDomain_code_userInfo_(
                    objc_str('KivyDragExport'), 1, info)
                completion_handler(error)
            else:
                completion_handler(None)
                _promise_log('info', 'promise: %s DONE' % self._name)
        except Exception as exc:
            _promise_log('warn', 'completion_handler invoke failed: %s' % exc)


class DragSource(object):
    '''NSDraggingSource lifecycle; AppKit calls @protocol methods later.'''

    def __init__(self, log=None, on_complete=None):
        self._log = log or (lambda *a: None)
        self._on_complete = on_complete
        self._moved_once = False

    @protocol('NSDraggingSource')
    def draggingSession_sourceOperationMaskForDraggingContext_(
            self, session, context):
        return NSDragOperationCopy

    @protocol('NSDraggingSource')
    def draggingSession_willBeginAtPoint_(self, session, point):
        try:
            self._log('info', 'drag-out session WILL BEGIN at (%.0f,%.0f)' % (
                point.x, point.y))
        except Exception:
            self._log('info', 'drag-out session WILL BEGIN')

    @protocol('NSDraggingSource')
    def draggingSession_movedToPoint_(self, session, point):
        if not self._moved_once:
            self._moved_once = True
            self._log('info', 'drag-out session TRACKING')

    @protocol('NSDraggingSource')
    def draggingSession_endedAtPoint_operation_(
            self, session, point, operation):
        accepted = bool(int(operation))
        self._log('info', 'drag-out session ENDED operation=%s (%s)' % (
            int(operation),
            'drop accepted' if accepted else 'NO drop — cancelled/untracked'))
        if self._on_complete is not None:
            try:
                self._on_complete(accepted)
            except Exception:
                pass


def begin_drag_files(items, action='copy', on_complete=None, log=None):
    '''Arm an NSDraggingSession of NSFilePromiseProvider items.'''
    log = log or (lambda *a: None)
    if not items or not available():
        return False
    try:
        from pyobjus import autoclass, objc_str
        from pyobjus.dylib_manager import load_framework, INCLUDE
        from pyobjus.objc_py_types import NSPoint, NSSize, NSRect

        load_framework(INCLUDE.AppKit)
        load_framework(INCLUDE.Foundation)
        _ensure_protocols()

        NSApplication = autoclass('NSApplication')
        NSEvent = autoclass('NSEvent')
        NSFilePromiseProvider = autoclass('NSFilePromiseProvider')
        NSDraggingItem = autoclass('NSDraggingItem')
        NSProcessInfo = autoclass('NSProcessInfo')

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

        cur_t = int(event.type()) if event is not None else -1
        if cur_t not in (NSEventTypeLeftMouseDown, NSEventTypeLeftMouseDragged):
            loc = win.mouseLocationOutsideOfEventStream()
            event = NSEvent.mouseEventWithType_location_modifierFlags_timestamp_windowNumber_context_eventNumber_clickCount_pressure_(
                NSEventTypeLeftMouseDragged, loc, 0,
                NSProcessInfo.processInfo().systemUptime(),
                win.windowNumber(), None, 0, 1, 1.0)
            if event is None:
                log('warn', 'drag-out bail: could not synthesize mouse anchor '
                            '(currentEvent type %s)' % cur_t)
                return False
            log('info', 'drag-out: synthesized leftMouseDragged anchor')

        loc = event.locationInWindow()
        x, y = float(loc.x), float(loc.y)
        drag_items = []
        keep = []
        for i, item in enumerate(items):
            file_type = 'public.folder' if item.is_dir else 'public.data'
            delegate = FilePromiseDelegate(item.name, item.provide)
            provider = NSFilePromiseProvider.alloc().initWithFileType_delegate_(
                objc_str(file_type), delegate)
            di = NSDraggingItem.alloc().initWithPasteboardWriter_(provider)
            frame = NSRect(
                origin=NSPoint(x=x + i * 4, y=y - i * 4),
                size=NSSize(width=64, height=64))
            di.setDraggingFrame_(frame)
            drag_items.append(di)
            keep.append(delegate)
            keep.append(provider)

        source = DragSource(log=log, on_complete=on_complete)
        keep.append(source)
        _LIVE.append(keep)
        del _LIVE[:-8]

        global _ARMED
        try:
            if _ARMED.get('monitor') is not None:
                NSEvent.removeMonitor_(_ARMED['monitor'])
                _ARMED = {'monitor': None}
        except Exception:
            _ARMED = {'monitor': None}

        state = {'fired': False}

        def _handler(ev):
            if not state['fired']:
                state['fired'] = True
                try:
                    view.beginDraggingSessionWithItems_event_source_(
                        drag_items, ev, source)
                    log('info', 'drag-out: session started IN-DISPATCH')
                except Exception as exc:
                    log('warn', 'drag-out: in-dispatch begin failed (%s: %s)' % (
                        type(exc).__name__, exc))
                mon, _ARMED['monitor'] = _ARMED.get('monitor'), None
                if mon is not None:
                    try:
                        NSEvent.removeMonitor_(mon)
                    except Exception:
                        pass
            return ev

        try:
            mask = NSEventMaskLeftMouseDragged | NSEventMaskLeftMouseDown
            _ARMED['monitor'] = (
                NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
                    mask, _handler))
        except Exception as exc:
            log('warn', 'drag-out: local monitor unavailable (%s) — '
                        'starting directly' % exc)
            view.beginDraggingSessionWithItems_event_source_(
                drag_items, event, source)
            return True

        try:
            from kivy.clock import Clock

            def _expire(dt):
                if not state['fired']:
                    state['fired'] = True
                    mon, _ARMED['monitor'] = _ARMED.get('monitor'), None
                    if mon is not None:
                        try:
                            NSEvent.removeMonitor_(mon)
                        except Exception:
                            pass
                    log('warn', 'drag-out: no live mouse-drag within 1.5s — '
                                'session NOT started')
            Clock.schedule_once(_expire, 1.5)
        except Exception:
            pass

        log('info', 'drag-out: ARMED for %d item(s)' % len(items))
        return True
    except Exception as exc:
        log('warn', 'drag-out unavailable (%s: %s)' % (type(exc).__name__, exc))
        traceback.print_exc(file=sys.stderr)
        return False


def begin_drag(mime_types, data_provider, action='copy', on_complete=None,
               log=None):
    '''General MIME drag. Prefer begin_drag_files for file promises.'''
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
