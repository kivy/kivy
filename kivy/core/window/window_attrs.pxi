include "../../include/config.pxi"

cdef extern from *:
    """
    #if __USE_WAYLAND
        #include <wayland-client.h>
        typedef struct wl_display struct_wl_display;
        typedef struct wl_surface struct_wl_surface;
        typedef struct wl_shell_surface struct_wl_shell_surface;
    #else
        struct wl_display;
        struct wl_surface;
        struct wl_shell_surface;

        typedef struct wl_display struct_wl_display;
        typedef struct wl_surface struct_wl_surface;
        typedef struct wl_shell_surface struct_wl_shell_surface;
    #endif

    #if __USE_X11
        #include <X11/Xlib.h>
    #else
        struct _XDisplay;
        typedef struct _XDisplay Display;
        typedef unsigned long XID;
        typedef XID Window;
    #endif

    #if defined(WIN32) || defined(_WIN32) || defined(__WIN32__) || defined(__NT__)
        #include <windows.h>
    #else
        typedef void *HANDLE;
        typedef HANDLE HWND;
        typedef HANDLE HDC;
        typedef HANDLE HINSTANCE;
    #endif

    #if defined(__APPLE__)
        #include <TargetConditionals.h>

        #if TARGET_OS_IPHONE && TARGET_IPHONE_SIMULATOR
            // iOS, tvOS, watchOS and iOS Simulator (UIKit)
            #include <UIKit/UIWindow.h>
        #else
            typedef void *UIWindow;
        #endif

        #if TARGET_OS_OSX
            #include <AppKit/NSWindow.h>
        #else
            typedef void *NSWindow;
        #endif

        #ifndef _BRIDGEDUIWINDOW_DEFINED
        #define _BRIDGEDUIWINDOW_DEFINED

        UIWindow *_BridgedUIWindow(void* window){
            return (__bridge UIWindow *)window;
        }

        NSWindow *_BridgedNSWindow(void* window){
            return (__bridge NSWindow *)window;
        }

        #endif

    #else
        typedef void *UIWindow;
        typedef void *NSWindow;

        #ifndef _BRIDGEDUIWINDOW_DEFINED
        #define _BRIDGEDUIWINDOW_DEFINED

        UIWindow *_BridgedUIWindow(void* window){
            return (UIWindow *)window;
        }

        NSWindow *_BridgedNSWindow(void* window){
            return (NSWindow *)window;
        }

        #endif

    #endif

    #if defined(__ANDROID__)
        #include <android/native_window.h>
        #include <EGL/egl.h>
    #else
        struct ANativeWindow;
        typedef void *EGLSurface;
    #endif

    """

    # Wayland
    ctypedef void* struct_wl_display
    ctypedef void* struct_wl_surface
    ctypedef void* struct_wl_shell_surface

    # X11
    cdef struct _XDisplay:
        pass
    ctypedef _XDisplay Display
    ctypedef unsigned long XID
    ctypedef XID Window

    # Windows
    ctypedef void *HANDLE
    ctypedef HANDLE HWND
    ctypedef HANDLE HDC
    ctypedef HANDLE HINSTANCE

    # Apple iOS, tvOS, watchOS and iOS Simulator (UIKit)
    ctypedef void *UIWindow

    # Apple macOS
    ctypedef void *NSWindow
    cdef NSWindow* _BridgedNSWindow(void* window)
    cdef UIWindow* _BridgedUIWindow(void* window)

    # Android
    cdef struct ANativeWindow:
        pass
    ctypedef void *EGLSurface