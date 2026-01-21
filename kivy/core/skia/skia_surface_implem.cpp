#include <cstdio>

// Core Skia includes for basic drawing operations
#include "include/core/SkCanvas.h"
#include "include/core/SkColorSpace.h"
#include "include/core/SkSurface.h"

// Skia GPU acceleration includes (Ganesh backend)
#include "include/gpu/ganesh/GrBackendSurface.h"
#include "include/gpu/ganesh/GrDirectContext.h"
#include "include/gpu/ganesh/SkSurfaceGanesh.h"
#include "include/gpu/ganesh/gl/GrGLBackendSurface.h"
#include "include/gpu/ganesh/gl/GrGLDirectContext.h"
#include "include/gpu/ganesh/gl/GrGLInterface.h"
#include "src/gpu/ganesh/gl/GrGLDefines.h"

// Runtime shader
#include "include/effects/SkRuntimeEffect.h"

// Global OpenGL interface instance - must be initialized elsewhere
extern sk_sp<const GrGLInterface> gl_interface;

/**
 * Structure to hold all Skia surface components
 */
struct SkiaSurfaceData {
    sk_sp<SkSurface> surface;
    SkCanvas *canvas;
    sk_sp<GrDirectContext> context;
};

/**
 * Creates a GPU-accelerated Skia surface
 * @param width Surface width in pixels
 * @param height Surface height in pixels
 * @return SkiaSurfaceData structure with initialized components
 */
SkiaSurfaceData createSkiaSurfaceData(int width, int height) {
    // SkSurfaceProps props(SkSurfaceProps::kUseDeviceIndependentFonts_Flag, SkPixelGeometry::kUnknown_SkPixelGeometry);
    SkSurfaceProps props(SkSurfaceProps::kDefault_Flag, kUnknown_SkPixelGeometry);

    // Create GPU context using the global OpenGL interface
    sk_sp<GrDirectContext> context = GrDirectContexts::MakeGL(gl_interface);
    if (!context) {
        printf("Failed to create GrContext.\n");
    }

    // Configure framebuffer to wrap existing OpenGL framebuffer (FBO ID 0 = default)
    GrGLFramebufferInfo framebufferInfo;
    framebufferInfo.fFBOID = 0;             // Use default framebuffer
    framebufferInfo.fFormat = GR_GL_RGBA8;  // 8-bit RGBA format

    // Create backend render target from OpenGL framebuffer
    GrBackendRenderTarget backendRenderTarget = GrBackendRenderTargets::MakeGL(width, height, 0, 0, framebufferInfo);

    // Create sRGB color space
    sk_sp<SkColorSpace> colorSpace = SkColorSpace::MakeSRGB();

    // Wrap the OpenGL render target in a Skia surface
    sk_sp<SkSurface> surface = SkSurfaces::WrapBackendRenderTarget(
        context.get(), backendRenderTarget, kTopLeft_GrSurfaceOrigin, kRGBA_8888_SkColorType, colorSpace, &props, nullptr, nullptr
    );

    if (!surface) {
        printf("Failed to create Skia surface.\n");
    }

    // Get the canvas for drawing operations
    SkCanvas *canvas = surface->getCanvas();

    // Return populated structure
    SkiaSurfaceData surfaceData;
    surfaceData.surface = surface;
    surfaceData.canvas = canvas;
    surfaceData.context = context;

    return surfaceData;
}


void clearCanvas(SkCanvas *canvas, sk_sp<GrDirectContext> context, uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
    SkColor color = SkColorSetARGB(a, r, g, b);
    canvas->clear(color);
}


void resetContext(sk_sp<GrDirectContext> context){
    context->resetContext();  // Force state refresh
    // context->performDeferredCleanup(std::chrono::milliseconds(0));

}

/**
 * Flushes all pending drawing operations and submits them to the GPU
 * This ensures all Skia commands are executed and visible on screen
 * @param context The GrDirectContext to flush and submit
 */
void flushAndSubmit(sk_sp<GrDirectContext> context) {
    //  context->submit(GrSyncCpu::kYes);
    // context->flushAndSubmit(GrSyncCpu::kYes);  // Force CPU wait
    // gl_interface->fFunctions.fFinish();  // Force GPU completion
    // gl_interface->fFunctions.fFlush();   // Additional flush

    context->flushAndSubmit(GrSyncCpu::kNo);
    context->submit(GrSyncCpu::kNo);  // Ensure GPU starts work
}

/**
 * Flushes all pending drawing operations
 * @param context The GrDirectContext to flush and submit
 */
void flush(sk_sp<GrDirectContext> context)
{
    context->flush();
}
