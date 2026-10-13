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
# ctypes structures
# ---------------------------------------------------------------------------


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
    """Approximate physical DPI derived from UIKit nativeScale.

    iOS does not expose a physical DPI API.  The base DPI values (163 ppi
    for iPhone/iPod, 132 ppi for iPad) are the non-retina screen densities;
    multiplying by nativeScale gives a close approximation that works
    correctly for any device, including future models.
    """
    scale = get_scale()
    try:
        rt = _objc_runtime()
        device = rt.send_id(
            rt.get_class(b"UIDevice"), rt.sel(b"currentDevice"))
        ns_model = rt.send_id(device, rt.sel(b"model"))
        utf8 = ctypes.cast(
            rt.send_id(ns_model, rt.sel(b"UTF8String")),
            ctypes.c_char_p,
        )
        if utf8.value and b"iPad" in utf8.value:
            return 132.0 * scale
    except Exception:
        pass
    return 163.0 * scale


def get_density() -> float:
    """Logical pixel density.  Alias for get_scale()."""
    return get_scale()


def get_fontscale() -> float:
    """User font-scale preference.

    iOS text scaling (Dynamic Type) is a per-text-style mapping driven by
    ``UIApplication.preferredContentSizeCategory``/``UIFontMetrics`` rather than
    a single global multiplier, so there is no direct analogue to Android's
    ``Configuration.fontScale``.  Kivy therefore reports ``1.0`` here, matching
    its historical behaviour; apps needing Dynamic Type must query UIKit
    directly.
    """
    return 1.0


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
