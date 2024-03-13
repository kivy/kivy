#include "egl_angle_metal_implem.h"


MetalANGLEGraphicsContext::MetalANGLEGraphicsContext(void * nativeMetalLayer) {
    m_nativeMetalLayer = nativeMetalLayer;
    // Initialize the EGL display
    initialiseEGLDisplay();
    // Initialize the EGL context
    initialiseEGLContext();
}

MetalANGLEGraphicsContext::~MetalANGLEGraphicsContext() {
    // Destroy the EGL context, surface and display objects
    eglMakeCurrent(m_displayObj, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    eglDestroySurface(m_displayObj, m_surfaceObj);
    eglDestroyContext(m_displayObj, m_contextObj);
    eglTerminate(m_displayObj);
}

void MetalANGLEGraphicsContext::swapBuffersEGL() {
    eglSwapBuffers(m_displayObj, m_surfaceObj);
}


// Search and initialize the EGL display
void MetalANGLEGraphicsContext::initialiseEGLDisplay() {

    EGLAttrib attribs[] = {
        EGL_PLATFORM_ANGLE_TYPE_ANGLE, EGL_PLATFORM_ANGLE_TYPE_METAL_ANGLE,
        EGL_POWER_PREFERENCE_ANGLE, EGL_HIGH_POWER_ANGLE,
        EGL_NONE
    };

    // Search for a display
    EGLDisplay display = eglGetPlatformDisplay(
        EGL_PLATFORM_ANGLE_ANGLE,
        reinterpret_cast<void*>(EGL_DEFAULT_DISPLAY),
        attribs
    );

    // If no display was found, return EGL_NO_DISPLAY
    if (display == EGL_NO_DISPLAY) {
        NSLog(@"EGLMetalANGLE: Failed to get EGL display.");
        return;
    }

    EGLint majorVersion = 0;
    EGLint minorVersion = 0;
    // Initialize the display
    if (!eglInitialize(display, &majorVersion, &minorVersion)) {
        NSLog(@"EGLMetalANGLE: Failed to initialize EGL display.");
        return;
    }

    NSLog(@"EGLMetalANGLE: Initialized EGL display with version %d.%d.", majorVersion, minorVersion);
    m_displayObj = display;
}

void MetalANGLEGraphicsContext::initialiseEGLContext() {

    EGLint configAttributes[] = {
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_RED_SIZE, 8,
        EGL_GREEN_SIZE, 8,
        EGL_BLUE_SIZE, 8,
        EGL_ALPHA_SIZE, 8,
        EGL_DEPTH_SIZE, 16,
        EGL_STENCIL_SIZE, 8,
        EGL_COLOR_BUFFER_TYPE, EGL_RGB_BUFFER,
        EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
        EGL_NONE
    };

    EGLConfig m_configObj;

    EGLint numberConfigsReturned = 0;
    eglChooseConfig(m_displayObj, configAttributes, &m_configObj, 1, &numberConfigsReturned);
    if (numberConfigsReturned != 1) {
        NSLog(@"EGLMetalANGLE: Failed to choose EGL config, got %d configs.", numberConfigsReturned);
        return;
    }

    eglBindAPI(EGL_OPENGL_ES_API);
    if(eglGetError() != EGL_SUCCESS) {
        NSLog(@"EGLMetalANGLE: Failed to bind OpenGL ES API.");
        return;
    }

    EGLint contextAttributes[] = {
        EGL_CONTEXT_CLIENT_VERSION, 2,
        EGL_NONE,
    };

    // Create the context
    EGLContext context = eglCreateContext(m_displayObj, m_configObj, EGL_NO_CONTEXT, contextAttributes);
    if (context == EGL_NO_CONTEXT) {
        NSLog(@"EGLMetalANGLE: Failed to create EGL context.");
        return;
    }

    // No specific surface attributes needed ATM
    EGLint surface_attributes[] = {
        EGL_NONE
    };

    // Get the native pointer to the Metal layer
    EGLNativeWindowType nativeWindowPtr = (__bridge EGLNativeWindowType)m_nativeMetalLayer;

    // Create the surface
    m_surfaceObj = eglCreateWindowSurface(m_displayObj, m_configObj, nativeWindowPtr, surface_attributes);

    if (m_surfaceObj == EGL_NO_SURFACE) {
        NSLog(@"EGLMetalANGLE: Failed to create EGL surface.");
        return;
    }

    // Make the context current
    if (!eglMakeCurrent(m_displayObj, m_surfaceObj, m_surfaceObj, context)) {
        NSLog(@"EGLMetalANGLE: Failed to make EGL context current.");
        return;
    }

    NSLog(@"Successfully initialized EGL context.");

    // Set the context
    m_contextObj = context;
}