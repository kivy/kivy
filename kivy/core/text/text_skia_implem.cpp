#include "text_skia_implem.h"

using namespace skia::textlayout;

SkiaOpenGLRenderer::SkiaOpenGLRenderer(unsigned int buffer_id, unsigned int tex_width, unsigned int tex_height)
{

    /*
    FBO ALTERNATIVE.

    fboInfo.fFBOID = buffer_id;
    fboInfo.fFormat = GR_GL_RGBA8;
    */

    texInfo.fTarget = GL_TEXTURE_2D;
    texInfo.fID = buffer_id;
    texInfo.fFormat = GR_GL_RGBA8;

    this->tex_width = tex_width;
    this->tex_height = tex_height;

    printf("SkiaOpenGLRenderer: Creating OpenGL context\n");

    // Create an interface to the OpenGL context
    auto interface = GrGLMakeNativeInterface();
    context = GrDirectContexts::MakeGL(interface).release();

    printf("SkiaOpenGLRenderer: Have OpenGL context\n");

    printf("SkiaOpenGLRenderer: Everything set up, and ready to render\n");

    // A little test to see if we can render something, just to make sure everything is working
    // this->renderHelloWorld();
}

void SkiaOpenGLRenderer::reset_context()
{
    // context->resetContext(kRenderTarget_GrGLBackendState | kMisc_GrGLBackendState);
    context->resetContext(kTextureBinding_GrGLBackendState | kMisc_GrGLBackendState);
}

sk_sp<SkSurface> SkiaOpenGLRenderer::get_surface()
{
    /*
    FBO ALTERNATIVE.

    sk_sp<SkColorSpace> colorSpace = SkColorSpace::MakeSRGB();

    GrGLint sampleCnt;
    glGetIntegerv(GL_SAMPLES, &sampleCnt);
    GrGLint stencil;
    glGetIntegerv(GL_STENCIL_BITS, &stencil);

    auto backend_render_target = GrBackendRenderTargets::MakeGL(this->tex_width, this->tex_height, sampleCnt, stencil, fboInfo);

    return SkSurfaces::WrapBackendRenderTarget(
        context, backend_render_target, kBottomLeft_GrSurfaceOrigin, kRGBA_8888_SkColorType, colorSpace, nullptr);
    */

    auto backend_texture = GrBackendTextures::MakeGL(this->tex_width, this->tex_height, GrMipMapped::kNo, texInfo);

    return SkSurfaces::WrapBackendTexture(
        context, backend_texture, kTopLeft_GrSurfaceOrigin, 0, kRGBA_8888_SkColorType, nullptr, nullptr, nullptr);

}

void SkiaOpenGLRenderer::render_text(std::string text)
{
    this->reset_context();

    sk_sp<SkSurface> surface = this->get_surface();

    if (surface) 
    {
        SkCanvas *canvas = surface->getCanvas();
        canvas->clear(SK_ColorWHITE);

        SkPaint fg_color = SkPaint();
        fg_color.setColor(SK_ColorBLACK);
        fg_color.setAntiAlias(true);

        TextStyle text_default_style;
        text_default_style.setForegroundColor(fg_color);
        text_default_style.setFontSize(40.0f);
        text_default_style.setFontFamilies({SkString("Roboto")});

        ParagraphStyle paragraph_style;
        paragraph_style.setTextStyle(text_default_style);
        paragraph_style.setTextAlign(TextAlign::kJustify);

        auto font_collection = sk_make_sp<FontCollection>();
        font_collection.get()->setDefaultFontManager(SkFontMgr::RefDefault());

        auto builder = ParagraphBuilderImpl::make(paragraph_style, font_collection);
        builder->addText(text.c_str(), text.length());
        builder->pop();

        auto paragraph = builder->Build();

        paragraph.get()->layout(this->tex_width);
        paragraph.get()->paint(canvas, 0, 0);

        // Flush the canvas
        if (auto dContext = GrAsDirectContext(canvas->recordingContext()))
        {
            dContext->flushAndSubmit();
        }

    }
}

void SkiaOpenGLRenderer::renderHelloWorld()
{
    this->reset_context();

    sk_sp<SkSurface> surface = this->get_surface();

    if (surface)
    {
        // Get the SkCanvas from the SkSurface
        SkCanvas *canvas = surface->getCanvas();

        // Clear the canvas
        canvas->clear(SK_ColorWHITE);

        canvas->drawColor(SK_ColorWHITE);

        // Draw a red circle
        SkPaint painta;
        painta.setAntiAlias(true);
        painta.setColor(SK_ColorRED);
        canvas->drawCircle(500, 500, 400, painta);

        // Draw a rectangle with half transparency
        SkPaint paintb;
        paintb.setAntiAlias(true);
        paintb.setColor(SK_ColorBLUE);
        paintb.setAlpha(128);
        SkRect rect = SkRect::MakeXYWH(50, 50, 400, 900);
        canvas->drawRect(rect, paintb);

        SkPaint paint;
        paint.setAntiAlias(true);
        paint.setColor(SK_ColorBLACK);

        SkPaint black;
        black.setColor(SK_ColorBLACK);

        TextStyle defaultStyle;
        // defaultStyle.setBackgroundColor(black);
        defaultStyle.setForegroundColor(paint);
        defaultStyle.setFontSize(40.0f);
        defaultStyle.setFontFamilies({SkString("Roboto")});

        ParagraphStyle paragraphStyle;
        paragraphStyle.setTextStyle(defaultStyle);
        paragraphStyle.setTextAlign(TextAlign::kJustify);

        auto font_collection = sk_make_sp<FontCollection>();
        font_collection.get()->setDefaultFontManager(SkFontMgr::RefDefault());

        auto builder = ParagraphBuilderImpl::make(paragraphStyle, font_collection);
        std::string name = "Lorem 🎉 ipsum dolor sit amet, consectetur 🥰 adipiscing elit. Donec a diam lectus. Sed sit amet ipsum mauris. Maecenas congue ligula ac quam viverra nec consectetur ante hendrerit. Donec et mollis dolor.\n\n\n";
        builder->addText(name.c_str(), name.length());
        // mix arabic and english
        std::string arabic_name = "تشاو موند Hellow world Hello World!";
        builder->addText(arabic_name.c_str(), arabic_name.length());
        builder->pop();

        auto para = builder->Build();

        para.get()->layout(400);

        // auto rect = SkRect();che

        para.get()->paint(canvas, 50, 50);

        // Flush the canvas
        if (auto dContext = GrAsDirectContext(canvas->recordingContext()))
        {
            dContext->flushAndSubmit();
        }
        printf("Rendered Hello, World!\n");
    }
}