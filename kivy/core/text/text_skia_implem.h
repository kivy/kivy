#include "include/ports/SkFontMgr_mac_ct.h"
#include "include/core/SkCanvas.h"
#include "include/core/SkSurface.h"
#include "include/core/SkTextBlob.h"
#include "include/gpu/GrBackendSurface.h"
#include "include/gpu/gl/GrGLInterface.h"
#include "include/gpu/GrDirectContext.h"
#include "include/gpu/ganesh/gl/GrGLDirectContext.h"
#include "include/gpu/ganesh/SkSurfaceGanesh.h"
#include "include/gpu/ganesh/gl/GrGLBackendSurface.h"
#include "modules/skparagraph/include/Paragraph.h"
#include "modules/skparagraph/src/ParagraphBuilderImpl.h"
#include "modules/skparagraph/src/ParagraphImpl.h"
#include "include/core/SkColorSpace.h"
#include "include/gpu/gl/GrGLTypes.h"
#include "modules/skparagraph/include/TextStyle.h"
#include "src/gpu/ganesh/gl/GrGLDefines.h"



#include <OpenGL/gl.h>



class SkiaOpenGLRenderer
{
public:
    SkiaOpenGLRenderer(unsigned int buffer_id, unsigned int tex_width, unsigned int tex_height);
    ~SkiaOpenGLRenderer();
    void render_text(std::string text);
    void renderHelloWorld();

private:
    unsigned int tex_width;
    unsigned int tex_height;
    GrDirectContext *context;
    GrBackendTexture backendTexture;
    // GrGLFramebufferInfo fboInfo; // FBO ALTERNATIVE
    GrGLTextureInfo texInfo;

    void reset_context();
    sk_sp<SkSurface> get_surface();
};
