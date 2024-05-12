include "../../include/config.pxi"

cdef extern from *:
    """
    #if __USE_WAYLAND
        #include <wayland-client-protocol.h>
    #else
        typedef struct {
        } wl_display;
        typedef struct {
        } wl_surface;
        typedef struct {
        } wl_shell_surface;
    #endif

    #if __USE_X11
        #include <X11/Xlib.h>
    #else
        typedef struct {
        } _XDisplay;
    
        typedef _XDisplay Display;
        typedef int XID;
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

        #if TARGET_OS_MAC
            #include <AppKit/NSWindow.h>
        #else
            typedef void *NSWindow;
        #endif

        UIWindow *_BridgedUIWindow(void* window){
            return (__bridge UIWindow *)window;
        }

        NSWindow *_BridgedNSWindow(void* window){
            return (__bridge NSWindow *)window;
        }

    #else
        typedef void *UIWindow;
        typedef void *NSWindow;

        UIWindow *_BridgedUIWindow(void* window){
            return (UIWindow *)window;
        }

        NSWindow *_BridgedNSWindow(void* window){
            return (NSWindow *)window;
        }

    #endif

    #if defined(__ANDROID__)
        // Android
    #endif

    """

    # Wayland
    ctypedef struct wl_display:
        pass
    ctypedef struct wl_surface:
        pass
    ctypedef struct wl_shell_surface:
        pass

    # X11
    ctypedef struct _XDisplay:
        pass
    ctypedef _XDisplay Display
    ctypedef int XID
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