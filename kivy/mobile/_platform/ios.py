"""iOS implementation of the kivy.mobile platform API.

Uses ctypes and the Objective-C runtime to read UIKit geometry without
adding any compiled extension dependency.  All values are returned in UIKit
*points*, which equal Kivy layout coordinates on iOS (``nativeScale`` applies
only to rasterization, not layout).

This module is imported automatically by ``kivy.mobile`` when
``kivy.utils.platform == 'ios'``.  Do not import it directly.
"""

from __future__ import annotations

import ctypes

# ---------------------------------------------------------------------------
# Device DPI table (from legacy kivy-ios ios_utils.m).
# ---------------------------------------------------------------------------

_DEVICE_DPI: dict[str, int] = {
    "iPhone1,1": 163, "iPhone1,2": 163, "iPhone2,1": 163,
    "iPhone3,1": 326, "iPhone3,2": 326, "iPhone3,3": 326,
    "iPhone4,1": 326,
    "iPhone5,1": 326, "iPhone5,2": 326, "iPhone5,3": 326, "iPhone5,4": 326,
    "iPhone6,1": 326, "iPhone6,2": 326,
    "iPhone7,1": 401, "iPhone7,2": 326,
    "iPhone8,1": 326, "iPhone8,2": 401, "iPhone8,4": 326,
    "iPhone9,1": 326, "iPhone9,2": 401, "iPhone9,3": 326, "iPhone9,4": 401,
    "iPhone10,1": 326, "iPhone10,2": 401, "iPhone10,3": 458,
    "iPhone10,4": 326, "iPhone10,5": 401, "iPhone10,6": 458,
    "iPhone11,2": 458, "iPhone11,4": 458, "iPhone11,6": 458, "iPhone11,8": 326,
    "iPhone12,1": 326, "iPhone12,3": 458, "iPhone12,5": 458, "iPhone12,8": 326,
    "iPhone13,1": 476, "iPhone13,2": 460, "iPhone13,3": 460, "iPhone13,4": 458,
    "iPhone14,2": 460, "iPhone14,3": 458, "iPhone14,4": 476,
    "iPhone14,5": 460, "iPhone14,6": 326,
    "iPad1,1": 132,
    "iPad2,1": 132, "iPad2,2": 132, "iPad2,3": 132, "iPad2,4": 132,
    "iPad2,5": 163, "iPad2,6": 163, "iPad2,7": 163,
    "iPad3,1": 264, "iPad3,2": 264, "iPad3,3": 264,
    "iPad3,4": 264, "iPad3,5": 264, "iPad3,6": 264,
    "iPad4,1": 264, "iPad4,2": 264, "iPad4,3": 264,
    "iPad4,4": 326, "iPad4,5": 326, "iPad4,6": 326,
    "iPad4,7": 326, "iPad4,8": 326, "iPad4,9": 326,
    "iPad5,1": 326, "iPad5,2": 326, "iPad5,3": 264, "iPad5,4": 264,
    "iPad6,3": 264, "iPad6,4": 264, "iPad6,7": 264, "iPad6,8": 264,
    "iPad6,11": 264, "iPad6,12": 264,
    "iPad7,1": 264, "iPad7,2": 264, "iPad7,3": 264, "iPad7,4": 264,
    "iPad7,5": 264, "iPad7,6": 264, "iPad7,11": 264, "iPad7,12": 264,
    "iPad8,1": 264, "iPad8,2": 264, "iPad8,3": 264, "iPad8,4": 264,
    "iPad8,5": 264, "iPad8,6": 264, "iPad8,7": 264, "iPad8,8": 264,
    "iPad11,1": 326, "iPad11,2": 326, "iPad11,3": 326, "iPad11,4": 326,
    "iPod1,1": 163, "iPod2,1": 163, "iPod3,1": 163,
    "iPod4,1": 326, "iPod5,1": 326, "iPod7,1": 326, "iPod9,1": 326,
}

# ---------------------------------------------------------------------------
# ctypes structures
# ---------------------------------------------------------------------------


class _Utsname(ctypes.Structure):
    _fields_ = [
        ("sysname",  ctypes.c_char * 256),
        ("nodename", ctypes.c_char * 256),
        ("release",  ctypes.c_char * 256),
        ("version",  ctypes.c_char * 256),
        ("machine",  ctypes.c_char * 256),
    ]


class _UIEdgeInsets(ctypes.Structure):
    _fields_ = [
        ("top",    ctypes.c_double),
        ("left",   ctypes.c_double),
        ("bottom", ctypes.c_double),
        ("right",  ctypes.c_double),
    ]


class _CGPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


class _CGSize(ctypes.Structure):
    _fields_ = [("width", ctypes.c_double), ("height", ctypes.c_double)]


class _CGRect(ctypes.Structure):
    _fields_ = [("origin", _CGPoint), ("size", _CGSize)]


# ---------------------------------------------------------------------------
# ObjC runtime helpers
# ---------------------------------------------------------------------------


def _device_model() -> str:
    """Return the Darwin machine string, e.g. ``'iPhone14,5'``."""
    libc = ctypes.CDLL(None)
    if not hasattr(libc, "uname"):
        return ""
    libc.uname.argtypes = [ctypes.POINTER(_Utsname)]
    libc.uname.restype = ctypes.c_int
    info = _Utsname()
    if libc.uname(ctypes.byref(info)) != 0:
        return ""
    return info.machine.decode("ascii", "ignore")


def _objc_runtime():
    """Return a namespace of typed objc_msgSend wrappers.

    UIEdgeInsets and CGRect are 4-double HFAs returned in d0–d3 on ARM64;
    libffi handles these without needing objc_msgSend_stret.
    """
    lib = ctypes.CDLL(None)

    get_class = lib.objc_getClass
    get_class.restype = ctypes.c_void_p
    get_class.argtypes = [ctypes.c_char_p]

    sel = lib.sel_registerName
    sel.restype = ctypes.c_void_p
    sel.argtypes = [ctypes.c_char_p]

    alloc_cls = lib.objc_allocateClassPair
    alloc_cls.restype = ctypes.c_void_p
    alloc_cls.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]

    add_method = lib.class_addMethod
    add_method.restype = ctypes.c_bool
    add_method.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p,
    ]

    reg_cls = lib.objc_registerClassPair
    reg_cls.restype = None
    reg_cls.argtypes = [ctypes.c_void_p]

    addr = ctypes.cast(lib.objc_msgSend, ctypes.c_void_p).value
    send_id = ctypes.CFUNCTYPE(
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(addr)
    send_id2 = ctypes.CFUNCTYPE(
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_void_p)(addr)
    send_f64 = ctypes.CFUNCTYPE(
        ctypes.c_double, ctypes.c_void_p, ctypes.c_void_p)(addr)
    send_insets = ctypes.CFUNCTYPE(
        _UIEdgeInsets, ctypes.c_void_p, ctypes.c_void_p)(addr)

    class _RT:
        pass

    rt = _RT()
    rt.lib = lib
    rt.get_class = get_class
    rt.sel = sel
    rt.alloc_cls = alloc_cls
    rt.add_method = add_method
    rt.reg_cls = reg_cls
    rt.send_id = send_id
    rt.send_id2 = send_id2
    rt.send_f64 = send_f64
    rt.send_insets = send_insets
    return rt


def _ns_string(rt, text: bytes) -> ctypes.c_void_p:
    cls = rt.get_class(b"NSString")
    return rt.send_id2(
        cls,
        rt.sel(b"stringWithUTF8String:"),
        ctypes.cast(ctypes.c_char_p(text), ctypes.c_void_p),
    )


def _key_window(rt) -> ctypes.c_void_p:
    app_cls = rt.get_class(b"UIApplication")
    app = rt.send_id(app_cls, rt.sel(b"sharedApplication"))
    win = rt.send_id(app, rt.sel(b"keyWindow"))
    if not win:
        windows = rt.send_id(app, rt.sel(b"windows"))
        win = rt.send_id(windows, rt.sel(b"firstObject"))
    return win


# ---------------------------------------------------------------------------
# Tier-1 API
# ---------------------------------------------------------------------------


def get_scale() -> float:
    """UIKit nativeScale of the main screen (e.g. 3.0 on iPhone Pro)."""
    try:
        rt = _objc_runtime()
        win = _key_window(rt)
        screen = rt.send_id(
            rt.send_id(win, rt.sel(b"windowScene")), rt.sel(b"screen"))
        return float(rt.send_f64(screen, rt.sel(b"nativeScale")))
    except Exception:
        return 2.0


def get_dpi() -> float:
    """Physical screen DPI (device lookup table or derived from nativeScale)."""
    model = _device_model()
    if model in _DEVICE_DPI:
        return float(_DEVICE_DPI[model])
    scale = get_scale()
    if model.startswith("iPad"):
        return 132.0 * scale
    if model.startswith(("iPhone", "iPod")):
        return 163.0 * scale
    return 160.0 * scale


def get_density() -> float:
    """Logical pixel density.  Alias for get_scale()."""
    return get_scale()


def get_safe_area() -> dict[str, float]:
    """Safe-area insets in UIKit points (== Kivy layout coordinates).

    Returns ``{"top", "left", "bottom", "right"}``.
    """
    try:
        rt = _objc_runtime()
        win = _key_window(rt)
        insets = rt.send_insets(win, rt.sel(b"safeAreaInsets"))
        return {
            "top":    float(insets.top),
            "left":   float(insets.left),
            "bottom": float(insets.bottom),
            "right":  float(insets.right),
        }
    except Exception:
        return {"top": 0.0, "left": 0.0, "bottom": 0.0, "right": 0.0}


# ---------------------------------------------------------------------------
# Keyboard height — ObjC NSNotificationCenter observer
# ---------------------------------------------------------------------------

_keyboard_height: float = 0.0
_kb_subscribers: list = []

# Strong Python references — must outlive the app.
_kb_imp_ref = None
_kb_observer_ref = None


def _install_keyboard_observer() -> None:
    """Register an ObjC observer for UIKeyboard frame notifications.

    Creates a small ObjC class (``_KivyMobileKBObserver``) and registers it
    with ``NSNotificationCenter`` for:

    * ``UIKeyboardWillChangeFrameNotification`` — keyboard appears / resizes
    * ``UIKeyboardWillHideNotification`` — keyboard hides

    UIKit fires these on the main thread; Kivy also runs on the main thread,
    so no cross-thread synchronisation is required.
    """
    global _kb_imp_ref, _kb_observer_ref

    try:
        rt = _objc_runtime()

        ImpType = ctypes.CFUNCTYPE(
            None,
            ctypes.c_void_p,  # self
            ctypes.c_void_p,  # _cmd
            ctypes.c_void_p,  # NSNotification *
        )

        def _kb_imp(self_ptr, cmd_ptr, notif_ptr):
            global _keyboard_height
            try:
                user_info = rt.send_id(notif_ptr, rt.sel(b"userInfo"))
                key = _ns_string(rt, b"UIKeyboardFrameEndUserInfoKey")
                ns_value = rt.send_id2(
                    user_info, rt.sel(b"objectForKey:"), key)

                if ns_value:
                    rect_fn = ctypes.CFUNCTYPE(
                        _CGRect, ctypes.c_void_p, ctypes.c_void_p,
                    )(ctypes.cast(rt.lib.objc_msgSend,
                                  ctypes.c_void_p).value)
                    rect = rect_fn(ns_value, rt.sel(b"CGRectValue"))
                    height = float(rect.size.height)
                else:
                    height = 0.0

                notif_name = rt.send_id(notif_ptr, rt.sel(b"name"))
                hide_name = _ns_string(rt, b"UIKeyboardWillHideNotification")
                is_hide = bool(rt.send_id2(
                    notif_name, rt.sel(b"isEqualToString:"), hide_name))
                _keyboard_height = 0.0 if is_hide else height

                for cb in list(_kb_subscribers):
                    try:
                        cb(_keyboard_height)
                    except Exception:
                        pass
            except Exception:
                pass

        imp = ImpType(_kb_imp)
        _kb_imp_ref = imp

        ns_object_cls = rt.get_class(b"NSObject")
        cls = rt.alloc_cls(ns_object_cls, b"_KivyMobileKBObserver", 0)
        if not cls:
            cls = rt.get_class(b"_KivyMobileKBObserver")
        rt.add_method(
            cls,
            rt.sel(b"keyboardEvent:"),
            ctypes.cast(imp, ctypes.c_void_p),
            b"v@:@",
        )
        rt.reg_cls(cls)

        observer = rt.send_id(cls, rt.sel(b"alloc"))
        observer = rt.send_id(observer, rt.sel(b"init"))
        _kb_observer_ref = observer

        nc = rt.send_id(
            rt.get_class(b"NSNotificationCenter"),
            rt.sel(b"defaultCenter"),
        )
        _add_obs = ctypes.CFUNCTYPE(
            None,
            ctypes.c_void_p,  # nc
            ctypes.c_void_p,  # SEL addObserver:selector:name:object:
            ctypes.c_void_p,  # observer
            ctypes.c_void_p,  # SEL keyboardEvent:
            ctypes.c_void_p,  # name NSString *
            ctypes.c_void_p,  # object (nil)
        )(ctypes.cast(rt.lib.objc_msgSend, ctypes.c_void_p).value)

        for notif_name_bytes in (
            b"UIKeyboardWillChangeFrameNotification",
            b"UIKeyboardWillHideNotification",
        ):
            _add_obs(
                nc,
                rt.sel(b"addObserver:selector:name:object:"),
                observer,
                rt.sel(b"keyboardEvent:"),
                _ns_string(rt, notif_name_bytes),
                None,
            )

    except Exception as exc:
        import warnings
        warnings.warn(
            f"kivy.mobile: keyboard observer setup failed: {exc}",
            RuntimeWarning,
            stacklevel=1,
        )


def get_keyboard_height() -> float:
    """Current software keyboard height in UIKit points (0 when hidden)."""
    return _keyboard_height


def subscribe_keyboard_height(callback) -> None:
    """Register *callback(height: float)* for keyboard height changes.

    The callback is invoked on the UIKit / Kivy main thread each time the
    keyboard frame changes.  It is safe to update Kivy properties directly
    or via ``kivy.clock.Clock.schedule_once``.
    """
    _kb_subscribers.append(callback)


# ---------------------------------------------------------------------------
# Tier-2 API — Android concepts not applicable on iOS
# ---------------------------------------------------------------------------


def get_display_cutout():
    """Always ``None`` on iOS.

    On Android this returns a list of ``{"left", "top", "right", "bottom"}``
    dicts for each physical display cutout.  iOS folds cutout geometry into
    the safe-area insets returned by :func:`get_safe_area`.
    """
    return None


def get_system_bar_insets():
    """Always ``None`` on iOS.

    On Android this returns ``{"status_bar": {...}, "nav_bar": {...}}``.
    iOS provides the equivalent data combined in :func:`get_safe_area`.
    """
    return None


# ---------------------------------------------------------------------------
# Module init
# ---------------------------------------------------------------------------

_install_keyboard_observer()
