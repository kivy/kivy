#include <Metal/Metal.h>
#include <QuartzCore/CAMetalLayer.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>

class MetalANGLEGraphicsContext
{
public:
    MetalANGLEGraphicsContext(void *nativeMetalLayer);
    ~MetalANGLEGraphicsContext();
    void swapBuffersEGL();
    void initialiseEGLDisplay();
    void initialiseEGLContext();

private:
    void *m_nativeMetalLayer;
    EGLContext m_contextObj;
    EGLDisplay m_displayObj;
    EGLSurface m_surfaceObj;
};