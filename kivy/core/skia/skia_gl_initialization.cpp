#include <include/gpu/ganesh/gl/GrGLAssembleInterface.h>
// #include "include/gpu/ganesh/gl/GrGLInterface.h"

// Kivy configuration (for build flags)
#include "config.h"

// Windows DLL loading
#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#else
#include <dlfcn.h>
#endif

// angle
#if !defined(__APPLE__)
#include "SDL3/SDL_egl.h"
#endif

#if __USE_ANGLE_GL_BACKEND
#include <EGL/egl.h>
#ifndef GL_GLEXT_PROTOTYPES
#define GL_GLEXT_PROTOTYPES
#endif

#include "angle_gl.h"
#endif

#ifdef _WIN32
static HMODULE egl_dll = nullptr;
#else
static void* egl_dll = nullptr;
#endif

#if defined(__APPLE__) && (TARGET_OS_IOS || TARGET_OS_SIMULATOR)
#include <CoreFoundation/CoreFoundation.h>
#endif


// Dynamic function pointers
typedef void* (*eglGetProcAddressFunc)(const char* procname);

// Global variables
sk_sp<const GrGLInterface> gl_interface;
static eglGetProcAddressFunc egl_get_proc_address = nullptr;




// Function to load EGL DLL dynamically
bool load_egl_dll() {
#ifdef _WIN32
    // Try different possible EGL DLL names on Windows
    const char* dll_names[] = {
        "libEGL.dll",
        "EGL.dll",
        "libGLESv2.dll",  // Sometimes EGL functions are in GLES DLL
        "opengl32.dll"    // Fallback to OpenGL32
    };

    for (const char* dll_name : dll_names) {
        egl_dll = LoadLibraryA(dll_name);
        if (egl_dll) {
            printf("Successfully loaded %s\n", dll_name);
            egl_get_proc_address = (eglGetProcAddressFunc)GetProcAddress(egl_dll, "eglGetProcAddress");

            if (egl_get_proc_address) {
                printf("Found eglGetProcAddress in %s\n", dll_name);
                return true;
            } else {
                // If eglGetProcAddress is not found, try wglGetProcAddress for OpenGL32
                egl_get_proc_address = (eglGetProcAddressFunc)GetProcAddress(egl_dll, "wglGetProcAddress");
                if (egl_get_proc_address) {
                    printf("Using wglGetProcAddress from %s\n", dll_name);
                    return true;
                }
            }

            FreeLibrary(egl_dll);
            egl_dll = nullptr;
        }
    }

    printf("Failed to load any EGL/OpenGL DLL\n");
    return false;
#else
    // Avoid redefinition and keep so_names local to this block
    const char* so_names[] = {
#if defined(__APPLE__) && (TARGET_OS_IOS || TARGET_OS_SIMULATOR)
        // iOS/tvOS: dynamically construct path to libEGL.dylib in app bundle
        nullptr
#else
        "libEGL.so.1", "libEGL.so", "libGL.so.1", "libGL.so", "libEGL.dylib"
#endif
    };

#if defined(__APPLE__) && (TARGET_OS_IOS || TARGET_OS_SIMULATOR)
    // for iOS, we need to construct the path to the libEGL framework
    // We should look into the app bundle's private frameworks directory to find the libEGL
    // framework. We can't hardcode the path cause it changes.
    char bundlePath[PATH_MAX] = {0};
    CFBundleRef mainBundle = CFBundleGetMainBundle();
    if (mainBundle) {
        CFURLRef frameworksURL = CFBundleCopyPrivateFrameworksURL(mainBundle);
        if (frameworksURL) {
            if (CFURLGetFileSystemRepresentation(frameworksURL, true, (UInt8*)bundlePath, sizeof(bundlePath))) {
                strncat(bundlePath, "/libEGL.framework/libEGL", sizeof(bundlePath) - strlen(bundlePath) - 1);
                so_names[0] = bundlePath;
            }
            CFRelease(frameworksURL);
        }
    }
#endif

    for (const char* so_name : so_names) {
        printf("Trying to load EGL/OpenGL shared library: %s\n", so_name);
        egl_dll = dlopen(so_name, RTLD_LAZY);
        if (egl_dll) {
            printf("Successfully loaded %s\n", so_name);
            egl_get_proc_address = (eglGetProcAddressFunc)dlsym(egl_dll, "eglGetProcAddress");

            if (egl_get_proc_address) {
                printf("Found eglGetProcAddress in %s\n", so_name);
                return true;
            } else {
                // Try glXGetProcAddress for OpenGL
                egl_get_proc_address = (eglGetProcAddressFunc)dlsym(egl_dll, "glXGetProcAddress");
                if (egl_get_proc_address) {
                    printf("Using glXGetProcAddress from %s\n", so_name);
                    return true;
                }
            }

            dlclose(egl_dll);
            egl_dll = nullptr;
        }
    }

    printf("Failed to load any EGL/OpenGL shared library\n");
    return false;
#endif
}

// Function to unload EGL DLL
void unload_egl_dll() {
    if (egl_dll) {
#ifdef _WIN32
        FreeLibrary(egl_dll);
#else
        dlclose(egl_dll);
#endif
        egl_dll = nullptr;
        egl_get_proc_address = nullptr;
    }
}

// Custom GetProcAddress wrapper
GrGLFuncPtr custom_get_proc_address(void* ctx, const char* name) {
    if (egl_get_proc_address) {
        return (GrGLFuncPtr)egl_get_proc_address(name);
    }

#ifdef _WIN32
    // Fallback: try to get from OpenGL32.dll
    static HMODULE opengl32 = GetModuleHandleA("opengl32.dll");
    if (opengl32) {
        return (GrGLFuncPtr)GetProcAddress(opengl32, name);
    }
#endif

    return nullptr;
}

void initialize_gl_interface(bool use_angle) {
    // Load EGL DLL first
    if (use_angle && !load_egl_dll()) {
        printf("Failed to load EGL DLL, falling back to native GL\n");
        use_angle = false;
    }

// angle
#if !defined(__APPLE__) || __USE_ANGLE_GL_BACKEND
    if (use_angle && egl_get_proc_address) {
        printf("Using ANGLE GL backend with dynamic DLL loading.\n");
        gl_interface = GrGLMakeAssembledInterface(nullptr, custom_get_proc_address);
    } else
#endif
    {
        printf("Using native GL implementation.\n");
        gl_interface = GrGLMakeNativeInterface();
    }

    // Validate the GL interface to ensure it is valid
    if (!gl_interface || !gl_interface->validate()) {
        printf("GL interface is invalid.\n");
        // Cleanup on failure
        if (use_angle) {
            unload_egl_dll();
        }
    }
}

// Cleanup function to call at program exit
void cleanup_resources() { unload_egl_dll(); }