#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// STL
#include <cmath>
#include <cstdio>
#include <future>
#include <memory>
#include <string>
#include <vector>

// Core Skia
#include "include/core/SkBitmap.h"
#include "include/core/SkCanvas.h"
#include "include/core/SkColorSpace.h"
#include "include/core/SkImage.h"
#include "include/core/SkImageInfo.h"
#include "include/core/SkPaint.h"
#include "include/core/SkPath.h"
#include "include/core/SkPathBuilder.h"
#include "include/core/SkRRect.h"
#include "include/core/SkRect.h"
#include "include/core/SkSamplingOptions.h"
#include "include/core/SkStream.h"
#include "include/core/SkSurface.h"

// Effects and filters
#include "include/effects/SkImageFilters.h"

// Skottie
#include "modules/skottie/include/Skottie.h"

// Function to clear the canvas

class Texture {
private:
    std::string m_path;
    int m_width = 0;
    int m_height = 0;

    struct TextureCacheKey {
        std::string path;
        int width;
        int height;

        bool operator==(const TextureCacheKey& other) const { return path == other.path && width == other.width && height == other.height; }
    };

    struct TextureCacheKeyHash {
        std::size_t operator()(const TextureCacheKey& key) const {
            return std::hash<std::string>{}(key.path) ^ (std::hash<int>{}(key.width) << 1) ^ (std::hash<int>{}(key.height) << 2);
        }
    };

    // Shared cache for resized textures
    static std::unordered_map<TextureCacheKey, sk_sp<SkImage>, TextureCacheKeyHash>& getTextureCache() {
        static std::unordered_map<TextureCacheKey, sk_sp<SkImage>, TextureCacheKeyHash> cache;
        return cache;
    }

    // Original image cache (loaded once per file)
    static std::unordered_map<std::string, sk_sp<SkImage>>& getOriginalCache() {
        static std::unordered_map<std::string, sk_sp<SkImage>> cache;
        return cache;
    }

    static sk_sp<SkImage> loadOriginalImage(const std::string& path) {
        auto& cache = getOriginalCache();
        auto it = cache.find(path);
        if (it != cache.end()) {
            return it->second;
        }

        sk_sp<SkData> data = SkData::MakeFromFileName(path.c_str());
        if (!data) {
            return nullptr;
        }

        sk_sp<SkImage> image = SkImages::DeferredFromEncodedData(data);
        cache[path] = image;
        return image;
    }

    static sk_sp<SkImage> resizeImage(sk_sp<SkImage> original, int targetWidth, int targetHeight) {
        if (!original) return nullptr;

        // If same size, return original
        if (original->width() == targetWidth && original->height() == targetHeight) {
            return original;
        }

        // Create surface for resizing
        sk_sp<SkSurface> surface = SkSurfaces::Raster(SkImageInfo::MakeN32Premul(targetWidth, targetHeight));

        if (!surface) return nullptr;

        SkCanvas* canvas = surface->getCanvas();
        SkRect destRect = SkRect::MakeWH(targetWidth, targetHeight);

        canvas->drawImageRect(original, destRect, SkSamplingOptions(SkFilterMode::kLinear));

        return surface->makeImageSnapshot();
    }

public:
    // Create texture with specific size
    static Texture create(const std::string& path, int width, int height) {
        Texture texture;
        texture.m_path = path;
        texture.m_width = width;
        texture.m_height = height;
        return texture;
    }

    void setPath(const std::string& path) { m_path = path; }

    void setSize(int width, int height) {
        m_width = width;
        m_height = height;
    }

    void clear() {
        m_path.clear();
        m_width = 0;
        m_height = 0;
    }

    const std::string& getPath() const { return m_path; }

    bool hasTexture() const { return !m_path.empty() && m_width > 0 && m_height > 0; }

    int getWidth() const { return m_width; }
    int getHeight() const { return m_height; }

    sk_sp<SkImage> getImage() const {
        if (!hasTexture()) return nullptr;

        TextureCacheKey key{ m_path, m_width, m_height };
        auto& textureCache = getTextureCache();

        // Check if resized texture exists in cache
        auto it = textureCache.find(key);
        if (it != textureCache.end()) {
            return it->second;
        }

        // Load original image
        sk_sp<SkImage> original = loadOriginalImage(m_path);
        if (!original) return nullptr;

        // Resize and cache
        sk_sp<SkImage> resized = resizeImage(original, m_width, m_height);
        textureCache[key] = resized;
        return resized;
    }

    // Clear caches
    static void clearTextureCache() { getTextureCache().clear(); }

    static void clearOriginalCache() { getOriginalCache().clear(); }

    static void clearAllCaches() {
        clearTextureCache();
        clearOriginalCache();
    }

    // Get cache statistics
    static size_t getTextureCacheSize() { return getTextureCache().size(); }

    static size_t getOriginalCacheSize() { return getOriginalCache().size(); }
};

class SkiaEllipse {
private:
    // Geometry properties
    float m_x = 0.0f;
    float m_y = 0.0f;
    float m_w = 100.0f;
    float m_h = 100.0f;
    float m_angle_start = 0.0f;
    float m_angle_end = 360.0f;
    int m_segments = -1;

    // Rendering resources
    Texture m_texture;
    mutable SkPaint m_paint;
    mutable bool m_initialized = false;

    // Constants
    static constexpr float FULL_CIRCLE_THRESHOLD = 0.01f;
    static constexpr float DEG_TO_RAD = static_cast<float>(M_PI) / 180.0f;

    void initialize() const {
        if (m_initialized) return;

        m_paint.setAntiAlias(true);
        m_paint.setStyle(SkPaint::kFill_Style);
        m_paint.setColor(SkColorSetARGB(255, 255, 255, 0));
        m_initialized = true;
    }

    struct EllipseGeometry {
        float centerX, centerY, radiusX, radiusY, angleDiff;
        SkRect bounds;
    };

    EllipseGeometry calculateGeometry() const {
        float radiusX = m_w * 0.5f;
        float radiusY = m_h * 0.5f;
        return {
            m_x + radiusX,                        // centerX
            m_y + radiusY,                        // centerY
            radiusX,                              // radiusX
            radiusY,                              // radiusY
            m_angle_end - m_angle_start,          // angleDiff
            SkRect::MakeXYWH(m_x, m_y, m_w, m_h)  // bounds
        };
    }

    bool isFullCircle(float angleDiff) const {
        return std::abs(std::abs(angleDiff) - 360.0f) < FULL_CIRCLE_THRESHOLD;
    }

    bool isPerfectCircle(const EllipseGeometry& geom) const {
        return m_w == m_h && isFullCircle(geom.angleDiff);
    }

    void drawTexturedShape(SkCanvas* canvas, const SkPath& clipPath, const SkRect& destRect) const {
        sk_sp<SkImage> image = m_texture.getImage();
        if (!image) return;

        canvas->save();
        canvas->clipPath(clipPath, true);

        // Flip Y-axis for texture
        SkMatrix flipMatrix;
        flipMatrix.setScale(1.0f, -1.0f, destRect.centerX(), destRect.centerY());
        canvas->concat(flipMatrix);

        canvas->drawImageRect(image, destRect, SkSamplingOptions(SkFilterMode::kLinear));
        canvas->restore();
    }

    void renderCircle(SkCanvas* canvas, const EllipseGeometry& geom) const {
        if (m_texture.hasTexture()) {
            SkPath circlePath = SkPath::Circle(geom.centerX, geom.centerY, geom.radiusX);
            drawTexturedShape(canvas, circlePath, geom.bounds);
        }
        else {
            canvas->drawCircle(geom.centerX, geom.centerY, geom.radiusX, m_paint);
        }
    }

    void renderEllipse(SkCanvas* canvas, const EllipseGeometry& geom) const {
        if (m_texture.hasTexture()) {
            SkPath ovalPath = SkPath::Oval(geom.bounds);
            drawTexturedShape(canvas, ovalPath, geom.bounds);
        }
        else {
            canvas->drawOval(geom.bounds, m_paint);
        }
    }

    void renderArc(SkCanvas* canvas, const EllipseGeometry& geom) const {
        if (m_texture.hasTexture()) {
            // Build arc path with SkPathBuilder for complex shapes
            SkPathBuilder builder;
            builder.arcTo(geom.bounds, m_angle_start, geom.angleDiff, false);
            builder.lineTo(geom.centerX, geom.centerY);
            builder.close();
            SkPath arcPath = builder.detach();

            drawTexturedShape(canvas, arcPath, geom.bounds);
        }
        else {
            canvas->drawArc(geom.bounds, m_angle_start, geom.angleDiff, true, m_paint);
        }
    }

    void renderCustomSegments(SkCanvas* canvas, const EllipseGeometry& geom) const {
        const float angleStart = m_angle_start * DEG_TO_RAD;
        const float angleStep = (geom.angleDiff * DEG_TO_RAD) / m_segments;
        const float cosStep = std::cos(angleStep);
        const float sinStep = std::sin(angleStep);

        float cosAngle = std::cos(angleStart);
        float sinAngle = std::sin(angleStart);

        // Build points array for polygon
        std::vector<SkPoint> points;
        points.reserve(m_segments + 2);

        // Add center point
        points.push_back(SkPoint::Make(geom.centerX, geom.centerY));

        // Add arc points
        for (int i = 0; i <= m_segments; ++i) {
            points.push_back(SkPoint::Make(
                geom.centerX + geom.radiusX * cosAngle,
                geom.centerY + geom.radiusY * sinAngle
            ));

            if (i < m_segments) {
                // Rotation matrix optimization
                const float newCosAngle = cosAngle * cosStep - sinAngle * sinStep;
                const float newSinAngle = sinAngle * cosStep + cosAngle * sinStep;
                cosAngle = newCosAngle;
                sinAngle = newSinAngle;
            }
        }

        // Create immutable path using Polygon factory
        SkPath polygonPath = SkPath::Polygon(
            SkSpan<const SkPoint>(points.data(), points.size()),
            true,
            SkPathFillType::kWinding,
            false
        );

        if (m_texture.hasTexture()) {
            drawTexturedShape(canvas, polygonPath, geom.bounds);
        }
        else {
            canvas->drawPath(polygonPath, m_paint);
        }
    }

public:
    void setTexture(const std::string& path, int width = -1, int height = -1) {
        if (width <= 0) width = static_cast<int>(m_w);
        if (height <= 0) height = static_cast<int>(m_h);

        m_texture = Texture::create(path, width, height);
    }

    void clearTexture() { m_texture.clear(); }

    const std::string& getTexture() const { return m_texture.getPath(); }

    void setGeometryAttrs(float x, float y, float w, float h, float angle_start, float angle_end, int segments = -1) {
        m_x = x;
        m_y = y;
        m_w = w;
        m_h = h;
        m_angle_start = angle_start;
        m_angle_end = angle_end;
        m_segments = segments;

        // Update texture size if exists
        if (m_texture.hasTexture()) {
            m_texture.setSize(static_cast<int>(w), static_cast<int>(h));
        }
    }

    void renderOnCanvas(SkCanvas* canvas) const {
        initialize();

        const EllipseGeometry geom = calculateGeometry();

        // Use custom segments if specified
        if (m_segments > 0) {
            renderCustomSegments(canvas, geom);
            return;
        }

        // Optimized rendering paths
        if (isPerfectCircle(geom)) {
            renderCircle(canvas, geom);
        }
        else if (isFullCircle(geom.angleDiff)) {
            renderEllipse(canvas, geom);
        }
        else {
            renderArc(canvas, geom);
        }
    }
};

//////////////////////////// Lottie ////////////////////////////

sk_sp<skottie::Animation> animation;
SkRect destRect = SkRect::MakeXYWH(100, 150, 200, 200);
SkMatrix transformMatrix;
SkPaint debugPaint;

void drawLottie(SkCanvas* canvas, sk_sp<GrDirectContext> context, const char* animation_path) {
    sk_sp<SkData> data = SkData::MakeFromFileName(animation_path);
    if (!data) {
        SkDebugf("Failure loading Lottie file: %s\n", animation_path);
        return;
    }

    animation = skottie::Animation::Make(reinterpret_cast<const char*>(data->data()), data->size());

    if (!animation) {
        SkDebugf("Failure creating Skottie animation\n");
        return;
    }

    SkRect srcRect = SkRect::MakeSize(animation->size());

    transformMatrix = SkMatrix::RectToRect(srcRect, destRect, SkMatrix::kCenter_ScaleToFit);

    SkMatrix flip;
    flip.setScale(1, -1);
    flip.postTranslate(0, destRect.height() + destRect.y() * 2.0f);
    transformMatrix.postConcat(flip);

    debugPaint.setColor(SK_ColorBLUE);
    debugPaint.setAlpha(0x20);
    debugPaint.setStyle(SkPaint::kFill_Style);
}

void updateLottiePosAndSize(float x, float y, float width, float height) {
    SkRect srcRect = SkRect::MakeSize(animation->size());
    destRect = SkRect::MakeXYWH(x, y, width, height);

    transformMatrix = SkMatrix::RectToRect(srcRect, destRect, SkMatrix::kCenter_ScaleToFit);

    SkMatrix flip;
    flip.setScale(1, -1);
    flip.postTranslate(0, destRect.height() + destRect.y() * 2.0f);
    transformMatrix.postConcat(flip);
}

void drawLottieNextFrame(SkCanvas* canvas, sk_sp<GrDirectContext> context, float t) {
    animation->seek(t);

    canvas->save();
    canvas->resetMatrix();
    canvas->drawRect(destRect, debugPaint);

    debugPaint.setColor(SK_ColorRED);
    debugPaint.setStyle(SkPaint::kStroke_Style);
    debugPaint.setStrokeWidth(2.0f);
    canvas->drawRect(destRect, debugPaint);
    canvas->restore();

    canvas->save();
    canvas->concat(transformMatrix);
    animation->render(canvas);
    canvas->restore();
}
