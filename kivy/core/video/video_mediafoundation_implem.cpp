/*
 * Video provider implementation for Windows using Media Foundation.
 * See video_mediafoundation_implem.h for the architecture summary and
 * why this is a genuinely separate compiled translation unit.
 *
 * Two design rules the code below relies on:
 *
 *   1. Never block the calling (Kivy main) thread. Playback does only
 *      cheap non-blocking polls (GetReadyState/OnVideoStreamTick/
 *      isBuffering) once per hasNewFrame()/retrieveFrame() call, which
 *      the Cython layer calls once per Kivy Clock tick. generateThumbnail()
 *      is the one deliberate exception: it is a synchronous, one-shot API
 *      by design (same as the other providers' thumbnail paths), so a
 *      short bounded blocking wait there is correct, not an oversight.
 *   2. No window/context of our own. This class runs on the Kivy main
 *      thread, where Kivy's GL context (WGL or ANGLE/EGL) is already
 *      current, so GL/EGL calls here use that context directly: no
 *      wglCreateContext, and for EGL, the display SDL reports as current
 *      rather than a newly created one. That is also what makes the
 *      EGL_ANGLE_device_d3d query return ANGLE's *real* in-use device
 *      rather than a second, independent one.
 */

#define _CRT_SECURE_NO_WARNINGS
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX

#include <windows.h>
#include <d3d11.h>
#include <dxgi.h>
#include <mfapi.h>
#include <mfidl.h>
#include <mfmediaengine.h>
#include <mferror.h>
#include <wincodec.h>
#include <GL/gl.h>

#include <atomic>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "video_mediafoundation_implem.h"

// ---------------------------------------------------------------------
// WGL_NV_DX_interop2 -- hand-declared: the Windows SDK has no header for
// this Khronos/OpenGL-registry extension.
// ---------------------------------------------------------------------
typedef HANDLE(WINAPI* PFNWGLDXOPENDEVICENVPROC)(void* dxDevice);
typedef BOOL(WINAPI* PFNWGLDXCLOSEDEVICENVPROC)(HANDLE hDevice);
typedef HANDLE(WINAPI* PFNWGLDXREGISTEROBJECTNVPROC)(
    HANDLE hDevice, void* dxObject, GLuint name, GLenum type, GLenum access);
typedef BOOL(WINAPI* PFNWGLDXUNREGISTEROBJECTNVPROC)(HANDLE hDevice, HANDLE hObject);
typedef BOOL(WINAPI* PFNWGLDXLOCKOBJECTSNVPROC)(HANDLE hDevice, GLint count, HANDLE* hObjects);
typedef BOOL(WINAPI* PFNWGLDXUNLOCKOBJECTSNVPROC)(HANDLE hDevice, GLint count, HANDLE* hObjects);
#define WGL_ACCESS_READ_ONLY_NV 0x0000
#ifndef GL_CLAMP_TO_EDGE
#define GL_CLAMP_TO_EDGE 0x812F
#endif

// ---------------------------------------------------------------------
// EGL / EGL_ANGLE_d3d_texture_client_buffer -- hand-declared, so the
// build needs no EGL headers. GL* types (GLenum, GLuint, ...) come from
// <GL/gl.h> above, already included for the WGL path -- only the
// EGL-specific types need declaring here.
// ---------------------------------------------------------------------
typedef void* EGLDisplay;
typedef void* EGLSurface;
typedef void* EGLConfig;
typedef void* EGLClientBuffer;
typedef void* EGLDeviceEXT;
typedef int32_t EGLint;
typedef unsigned int EGLBoolean;
typedef unsigned int EGLenum;
typedef intptr_t EGLAttrib;

#define EGL_NO_SURFACE          ((EGLSurface)0)
#define EGL_SUCCESS             0x3000
#define EGL_SURFACE_TYPE        0x3033
#define EGL_PBUFFER_BIT         0x0001
#define EGL_RENDERABLE_TYPE     0x3040
#define EGL_OPENGL_ES2_BIT      0x0004
#define EGL_RED_SIZE            0x3024
#define EGL_GREEN_SIZE          0x3023
#define EGL_BLUE_SIZE           0x3022
#define EGL_ALPHA_SIZE          0x3021
#define EGL_TEXTURE_FORMAT      0x3080
#define EGL_TEXTURE_RGBA        0x305E
#define EGL_TEXTURE_TARGET      0x3081
#define EGL_TEXTURE_2D_ATTR     0x305F  // EGL_TEXTURE_2D attrib value (distinct from GL_TEXTURE_2D)
#define EGL_BACK_BUFFER         0x3084
#define EGL_DEVICE_EXT          0x322C  // EGL_EXT_device_query
#define EGL_D3D11_DEVICE_ANGLE  0x33A1  // EGL_ANGLE_device_d3d
#define EGL_D3D_TEXTURE_ANGLE   0x33A3  // EGL_ANGLE_d3d_texture_client_buffer
#define EGL_NONE                0x3038

typedef EGLDisplay (WINAPI *PFNEGLGETCURRENTDISPLAYPROC)(void);
typedef EGLint (WINAPI *PFNEGLGETERRORPROC)(void);
typedef void* (WINAPI *PFNEGLGETPROCADDRESSPROC)(const char*);
typedef EGLBoolean (WINAPI *PFNEGLCHOOSECONFIGPROC)(EGLDisplay, const EGLint*, EGLConfig*, EGLint, EGLint*);
typedef EGLBoolean (WINAPI *PFNEGLQUERYDISPLAYATTRIBEXTPROC)(EGLDisplay, EGLint, EGLAttrib*);
typedef EGLBoolean (WINAPI *PFNEGLQUERYDEVICEATTRIBEXTPROC)(EGLDeviceEXT, EGLint, EGLAttrib*);
typedef EGLSurface (WINAPI *PFNEGLCREATEPBUFFERFROMCLIENTBUFFERPROC)(EGLDisplay, EGLenum, EGLClientBuffer, EGLConfig, const EGLint*);
typedef EGLBoolean (WINAPI *PFNEGLBINDTEXIMAGEPROC)(EGLDisplay, EGLSurface, EGLint);
typedef EGLBoolean (WINAPI *PFNEGLRELEASETEXIMAGEPROC)(EGLDisplay, EGLSurface, EGLint);
typedef EGLBoolean (WINAPI *PFNEGLDESTROYSURFACEPROC)(EGLDisplay, EGLSurface);

// GL entry points this file calls, resolved through SDL_GL_GetProcAddress
// so they always reach whatever GL implementation Kivy's context
// actually belongs to. Calling opengl32.dll's exports directly only
// works for a WGL context: under ANGLE (an EGL context, not WGL)
// opengl32 has no current context, so its glGenTextures silently
// returns 0 and the EGL bridge ends up with nothing to bind to.
typedef void (APIENTRY *GenTexturesFn)(GLsizei, GLuint*);
typedef void (APIENTRY *BindTextureFn)(GLenum, GLuint);
typedef void (APIENTRY *DeleteTexturesFn)(GLsizei, const GLuint*);
typedef void (APIENTRY *TexParameteriFn)(GLenum, GLenum, GLint);
typedef void (APIENTRY *GetIntegervFn)(GLenum, GLint*);
#ifndef GL_TEXTURE_BINDING_2D
#define GL_TEXTURE_BINDING_2D 0x8069
#endif
typedef void* (__cdecl *SDLGLGetProcAddressFn)(const char*);

// ---------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------

static std::wstring utf8_to_wide(const char *s) {
    if (!s || !*s) return std::wstring();
    int len = MultiByteToWideChar(CP_UTF8, 0, s, -1, nullptr, 0);
    std::vector<wchar_t> buf(len);
    MultiByteToWideChar(CP_UTF8, 0, s, -1, buf.data(), len);
    return std::wstring(buf.data());
}

// If `url` looks like an existing local path (no "://"), convert it to
// a file:/// URI the way IMFMediaEngine::SetSource expects; otherwise
// pass it through untouched (already a URL, e.g. http(s)://).
static std::wstring to_source_uri(const std::wstring &url) {
    if (url.find(L"://") != std::wstring::npos) return url;
    wchar_t fullPath[MAX_PATH];
    if (!GetFullPathNameW(url.c_str(), MAX_PATH, fullPath, nullptr)) return url;
    std::wstring uri = L"file:///";
    for (wchar_t *p = fullPath; *p; p++) uri += (*p == L'\\') ? L'/' : *p;
    return uri;
}

// Process-wide COM/MF runtime lifecycle, reference-counted across
// however many VideoPlayer instances exist over the session. All
// construction/destruction happens on the Kivy main thread, so a plain
// counter (no locking) is sufficient.
static int g_mf_runtime_refcount = 0;

static bool g_com_initialized_by_us = false;

// The Kivy main thread is already a single-threaded apartment by the
// time this runs (SDL3 initializes COM as STA), so request the same
// model: it then just bumps COM's own refcount (S_FALSE). CoUninitialize
// must only balance a CoInitializeEx that *succeeded* -- calling it after
// RPC_E_CHANGED_MODE would strip one of SDL3's own initializations each
// time, eventually tearing COM down underneath it.
static void mf_runtime_acquire() {
    if (g_mf_runtime_refcount++ == 0) {
        HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
        g_com_initialized_by_us = SUCCEEDED(hr);
        MFStartup(MF_VERSION);
    }
}

static void mf_runtime_release() {
    if (--g_mf_runtime_refcount == 0) {
        MFShutdown();
        if (g_com_initialized_by_us) {
            CoUninitialize();
            g_com_initialized_by_us = false;
        }
    }
}

// IMFMediaEngineNotify implementation. Fires on an MF-internal thread;
// only ever touches atomics, never calls back into Python/Cython -- so,
// unlike video_android.py's jnius callbacks, nothing here needs a
// mainthread-style trampoline.
class EngineNotify : public IMFMediaEngineNotify {
public:
    std::atomic<ULONG> ref{1};
    std::atomic<bool> ended{false};
    // True from WAITING until the next PLAYING/CANPLAYTHROUGH --
    // matches VideoBase.buffering's documented semantics.
    std::atomic<bool> buffering{false};
    // MF_MEDIA_ENGINE_EVENT_ERROR: the MF_MEDIA_ENGINE_ERR code and the
    // HRESULT behind it. errCode is written before `errored` is set, so
    // a reader that sees `errored` also sees both values.
    std::atomic<DWORD> errCode{0};
    std::atomic<HRESULT> errHr{S_OK};
    std::atomic<bool> errored{false};

    STDMETHODIMP QueryInterface(REFIID riid, void **ppv) override {
        if (riid == __uuidof(IMFMediaEngineNotify) || riid == IID_IUnknown) {
            *ppv = static_cast<IMFMediaEngineNotify*>(this);
            AddRef();
            return S_OK;
        }
        *ppv = nullptr;
        return E_NOINTERFACE;
    }
    STDMETHODIMP_(ULONG) AddRef() override { return ++ref; }
    STDMETHODIMP_(ULONG) Release() override {
        ULONG r = --ref;
        if (r == 0) delete this;
        return r;
    }
    STDMETHODIMP EventNotify(DWORD event, DWORD_PTR param1, DWORD param2) override {
        switch (event) {
            case MF_MEDIA_ENGINE_EVENT_ERROR:
                errCode = (DWORD)param1;
                errHr = (HRESULT)param2;
                errored = true;
                break;
            case MF_MEDIA_ENGINE_EVENT_ENDED:
                ended = true;
                break;
            case MF_MEDIA_ENGINE_EVENT_WAITING:
                buffering = true;
                break;
            case MF_MEDIA_ENGINE_EVENT_PLAYING:
            case MF_MEDIA_ENGINE_EVENT_CANPLAYTHROUGH:
                buffering = false;
                break;
        }
        return S_OK;
    }
};

// ---------------------------------------------------------------------
// Source creation through the system source resolver.
//
// By default IMFMediaEngine only opens the formats an HTML5 <video>
// element would (CanPlayType answers "not supported" for MPEG-PS .mpg,
// WMV and AVI, among others), even when Windows has a source and decoder
// installed for them. Registering this IMFMediaEngineExtension makes the
// engine ask the system IMFSourceResolver for its media source instead,
// so any format with an installed Media Foundation source and decoder
// plays -- the same set Windows' own media apps can open. Resolution is
// asynchronous (the resolver's Begin/End pair), so a slow network URL
// never blocks the thread that called SetSource.
// ---------------------------------------------------------------------

// Completes one resolver request by invoking the engine's callback with
// the media source (or the resolver's failure) as the result object.
class ResolveCallback : public IMFAsyncCallback {
public:
    std::atomic<ULONG> ref{1};
    IMFSourceResolver *resolver;
    bool fromByteStream;
    IMFAsyncCallback *engineCb;
    IUnknown *engineState;

    ResolveCallback(IMFSourceResolver *r, bool bs, IMFAsyncCallback *cb, IUnknown *st)
        : resolver(r), fromByteStream(bs), engineCb(cb), engineState(st) {
        resolver->AddRef();
        engineCb->AddRef();
        if (engineState) engineState->AddRef();
    }
    virtual ~ResolveCallback() {
        resolver->Release();
        engineCb->Release();
        if (engineState) engineState->Release();
    }

    STDMETHODIMP QueryInterface(REFIID riid, void **ppv) override {
        if (riid == __uuidof(IMFAsyncCallback) || riid == IID_IUnknown) {
            *ppv = static_cast<IMFAsyncCallback*>(this);
            AddRef();
            return S_OK;
        }
        *ppv = nullptr;
        return E_NOINTERFACE;
    }
    STDMETHODIMP_(ULONG) AddRef() override { return ++ref; }
    STDMETHODIMP_(ULONG) Release() override {
        ULONG r = --ref;
        if (r == 0) delete this;
        return r;
    }
    STDMETHODIMP GetParameters(DWORD *, DWORD *) override { return E_NOTIMPL; }
    STDMETHODIMP Invoke(IMFAsyncResult *result) override {
        MF_OBJECT_TYPE type = MF_OBJECT_INVALID;
        IUnknown *source = nullptr;
        HRESULT hr = fromByteStream
            ? resolver->EndCreateObjectFromByteStream(result, &type, &source)
            : resolver->EndCreateObjectFromURL(result, &type, &source);
        IMFAsyncResult *out = nullptr;
        if (SUCCEEDED(MFCreateAsyncResult(source, engineCb, engineState, &out))) {
            out->SetStatus(hr);
            MFInvokeCallback(out);
            out->Release();
        }
        if (source) source->Release();
        Release();  // the reference taken for this request
        return S_OK;
    }
};

class SourceExtension : public IMFMediaEngineExtension {
public:
    std::atomic<ULONG> ref{1};

    STDMETHODIMP QueryInterface(REFIID riid, void **ppv) override {
        if (riid == __uuidof(IMFMediaEngineExtension) || riid == IID_IUnknown) {
            *ppv = static_cast<IMFMediaEngineExtension*>(this);
            AddRef();
            return S_OK;
        }
        *ppv = nullptr;
        return E_NOINTERFACE;
    }
    STDMETHODIMP_(ULONG) AddRef() override { return ++ref; }
    STDMETHODIMP_(ULONG) Release() override {
        ULONG r = --ref;
        if (r == 0) delete this;
        return r;
    }

    STDMETHODIMP CanPlayType(BOOL, BSTR, MF_MEDIA_ENGINE_CANPLAY *answer) override {
        // Whether it really plays depends on the installed sources and
        // decoders, which only resolving the actual file can tell.
        *answer = MF_MEDIA_ENGINE_CANPLAY_MAYBE;
        return S_OK;
    }

    STDMETHODIMP BeginCreateObject(BSTR url, IMFByteStream *byteStream,
                                   MF_OBJECT_TYPE type, IUnknown **cancelCookie,
                                   IMFAsyncCallback *callback, IUnknown *state) override {
        if (cancelCookie) *cancelCookie = nullptr;
        // Only the media source is ours to create; the engine opens the
        // byte stream itself and passes it back in here.
        if (type != MF_OBJECT_MEDIASOURCE) return MF_E_UNSUPPORTED_BYTESTREAM_TYPE;

        IMFSourceResolver *resolver = nullptr;
        HRESULT hr = MFCreateSourceResolver(&resolver);
        if (FAILED(hr)) return hr;
        const DWORD flags = MF_RESOLUTION_MEDIASOURCE |
            MF_RESOLUTION_CONTENT_DOES_NOT_HAVE_TO_MATCH_EXTENSION_OR_MIME_TYPE;
        ResolveCallback *cb = new ResolveCallback(resolver, byteStream != nullptr,
                                                  callback, state);
        hr = byteStream
            ? resolver->BeginCreateObjectFromByteStream(byteStream, url, flags, nullptr,
                                                        nullptr, cb, nullptr)
            : resolver->BeginCreateObjectFromURL(url, flags, nullptr, nullptr, cb, nullptr);
        resolver->Release();
        // On success cb's own reference is released in Invoke().
        if (FAILED(hr)) cb->Release();
        return hr;
    }

    STDMETHODIMP CancelObjectCreation(IUnknown *) override { return E_NOTIMPL; }

    STDMETHODIMP EndCreateObject(IMFAsyncResult *result, IUnknown **object) override {
        *object = nullptr;
        HRESULT hr = result->GetStatus();
        if (FAILED(hr)) return hr;
        return result->GetObject(object);
    }
};

// Creates a media engine for playback or thumbnails. With a DXGI device
// manager the engine decodes into D3D11 textures (the normal path).
// Without one (dxgiMgr == nullptr) it decodes in software and can only
// hand frames to a WIC bitmap -- the fallback for formats whose decoder
// has no Direct3D 11 support (see MFVideoPlayerImpl::hasError()).
static HRESULT create_engine(IMFDXGIDeviceManager *dxgiMgr, IMFMediaEngineNotify *notify,
                             IMFMediaEngine **engine) {
    *engine = nullptr;
    IMFAttributes *attrs = nullptr;
    HRESULT hr = MFCreateAttributes(&attrs, 4);
    if (FAILED(hr)) return hr;
    SourceExtension *ext = new SourceExtension();
    if (dxgiMgr) attrs->SetUnknown(MF_MEDIA_ENGINE_DXGI_MANAGER, dxgiMgr);
    attrs->SetUnknown(MF_MEDIA_ENGINE_CALLBACK, notify);
    attrs->SetUnknown(MF_MEDIA_ENGINE_EXTENSION, ext);
    attrs->SetUINT32(MF_MEDIA_ENGINE_VIDEO_OUTPUT_FORMAT, DXGI_FORMAT_B8G8R8A8_UNORM);
    ext->Release();  // the attribute store holds its own reference

    IMFMediaEngineClassFactory *factory = nullptr;
    hr = CoCreateInstance(CLSID_MFMediaEngineClassFactory, nullptr, CLSCTX_INPROC_SERVER,
                          __uuidof(IMFMediaEngineClassFactory), (void**)&factory);
    if (SUCCEEDED(hr)) {
        hr = factory->CreateInstance(0, attrs, engine);
        factory->Release();
    }
    attrs->Release();
    return hr;
}

static void set_engine_source(IMFMediaEngine *engine, const std::wstring &url) {
    std::wstring uri = to_source_uri(url);
    BSTR bstr = SysAllocString(uri.c_str());
    engine->SetSource(bstr);
    SysFreeString(bstr);
}

// Copies BGRA rows into a tightly packed RGBA buffer. Swizzled here
// rather than uploaded as colorfmt='bgra': not every GL backend this
// runs under accepts GL_BGRA uploads.
static void bgra_to_rgba(const uint8_t *src, size_t pitch, int w, int h, char *dst) {
    for (int y = 0; y < h; y++) {
        const uint8_t *s = src + (size_t)y * pitch;
        uint8_t *d = (uint8_t*)dst + (size_t)y * w * 4;
        for (int x = 0; x < w; x++) {
            d[x*4+0] = s[x*4+2];
            d[x*4+1] = s[x*4+1];
            d[x*4+2] = s[x*4+0];
            d[x*4+3] = s[x*4+3];
        }
    }
}

// Software-engine frame delivery: TransferVideoFrame into a w x h WIC
// bitmap (created on first use in *bmp), then copy it out as RGBA into
// dst, which must hold w * h * 4 bytes.
static bool transfer_to_wic(IMFMediaEngine *engine, IWICImagingFactory *wic,
                            IWICBitmap **bmp, int w, int h, char *dst) {
    if (!*bmp && FAILED(wic->CreateBitmap(w, h, GUID_WICPixelFormat32bppBGRA,
                                          WICBitmapCacheOnDemand, bmp)))
        return false;
    RECT destRect = {0, 0, w, h};
    MFARGB border = {0, 0, 0, 255};
    if (FAILED(engine->TransferVideoFrame(*bmp, nullptr, &destRect, &border))) return false;
    WICRect rc = {0, 0, w, h};
    IWICBitmapLock *lock = nullptr;
    if (FAILED((*bmp)->Lock(&rc, WICBitmapLockRead, &lock))) return false;
    UINT stride = 0, size = 0;
    BYTE *pixels = nullptr;
    bool ok = SUCCEEDED(lock->GetStride(&stride)) &&
              SUCCEEDED(lock->GetDataPointer(&size, &pixels));
    if (ok) bgra_to_rgba(pixels, stride, w, h, dst);
    lock->Release();
    return ok;
}

enum Bridge { BRIDGE_WGL, BRIDGE_EGL };

// ---------------------------------------------------------------------
// MFVideoPlayerImpl -- all real Windows/COM/D3D11/MF/GL state. Defined
// only here; VideoPlayer (the public, header-visible class) just owns a
// pointer to one of these and forwards every call.
// ---------------------------------------------------------------------
struct MFVideoPlayerImpl {
    std::wstring url;
    Bridge bridge;

    // D3D11 device MF decodes into. Owned (created by us) for the WGL
    // bridge; borrowed (ANGLE's own, queried, never released by us) for
    // the EGL bridge.
    ID3D11Device *device = nullptr;
    ID3D11DeviceContext *deviceCtx = nullptr;
    bool ownsDevice = false;

    IMFDXGIDeviceManager *dxgiMgr = nullptr;
    IMFMediaEngine *engine = nullptr;
    EngineNotify *notify = nullptr;

    // Decode target. Created lazily once the native video size is known;
    // reused for the life of the player (MF overwrites its contents
    // every TransferVideoFrame call).
    ID3D11Texture2D *destTex = nullptr;
    int texWidth = 0;
    int texHeight = 0;

    bool framePending = false;
    LONGLONG pendingPts = 0;

    // Zero-copy bridge state. Probed exactly once, lazily, on the first
    // successfully transferred frame.
    bool interopProbed = false;
    bool interopOk = false;
    GLuint glTex = 0;

    // Resolved in resolveGlFunctions() -- see the typedef comment above.
    GenTexturesFn pglGenTextures = nullptr;
    BindTextureFn pglBindTexture = nullptr;
    DeleteTexturesFn pglDeleteTextures = nullptr;
    TexParameteriFn pglTexParameteri = nullptr;
    GetIntegervFn pglGetIntegerv = nullptr;

    // WGL-specific
    PFNWGLDXOPENDEVICENVPROC pwglDXOpenDeviceNV = nullptr;
    PFNWGLDXCLOSEDEVICENVPROC pwglDXCloseDeviceNV = nullptr;
    PFNWGLDXREGISTEROBJECTNVPROC pwglDXRegisterObjectNV = nullptr;
    PFNWGLDXUNREGISTEROBJECTNVPROC pwglDXUnregisterObjectNV = nullptr;
    PFNWGLDXLOCKOBJECTSNVPROC pwglDXLockObjectsNV = nullptr;
    PFNWGLDXUNLOCKOBJECTSNVPROC pwglDXUnlockObjectsNV = nullptr;
    HANDLE wglDevice = nullptr;
    HANDLE wglObj = nullptr;
    bool wglLocked = false;

    // EGL-specific
    PFNEGLGETCURRENTDISPLAYPROC peglGetCurrentDisplay = nullptr;
    PFNEGLGETERRORPROC peglGetError = nullptr;
    PFNEGLGETPROCADDRESSPROC peglGetProcAddress = nullptr;
    PFNEGLCHOOSECONFIGPROC peglChooseConfig = nullptr;
    PFNEGLQUERYDISPLAYATTRIBEXTPROC peglQueryDisplayAttribEXT = nullptr;
    PFNEGLQUERYDEVICEATTRIBEXTPROC peglQueryDeviceAttribEXT = nullptr;
    PFNEGLCREATEPBUFFERFROMCLIENTBUFFERPROC peglCreatePbufferFromClientBuffer = nullptr;
    PFNEGLBINDTEXIMAGEPROC peglBindTexImage = nullptr;
    PFNEGLRELEASETEXIMAGEPROC peglReleaseTexImage = nullptr;
    PFNEGLDESTROYSURFACEPROC peglDestroySurface = nullptr;
    EGLDisplay eglDpy = nullptr;
    EGLConfig eglConfig = nullptr;
    EGLSurface eglClientBufSurf = EGL_NO_SURFACE;
    bool eglBound = false;

    // CPU-copy fallback
    ID3D11Texture2D *stagingTex = nullptr;
    std::vector<char> cpuBuf;

    // Software decode: set when the D3D11 engine rejected the source and
    // it was reopened on an engine without a DXGI device manager (see
    // hasError()). Frames then arrive through a WIC bitmap.
    bool softwareDecode = false;
    IWICImagingFactory *wic = nullptr;
    IWICBitmap *wicBmp = nullptr;
    // Replayed onto the software engine, which starts from scratch.
    bool wantPlay = false;
    double volume = 1.0;

    VideoFrame outFrame;
    // lastErrorBuf: hard failures (no playback). interopNoteBuf: why
    // zero-copy isn't in use -- an expected condition that just means
    // the CPU-copy fallback, not an error.
    char lastErrorBuf[256] = {0};
    char interopNoteBuf[256] = {0};

    explicit MFVideoPlayerImpl(const char *url_) : bridge(BRIDGE_WGL) {
        mf_runtime_acquire();
        url = utf8_to_wide(url_);
    }

    ~MFVideoPlayerImpl() {
        unload();
        mf_runtime_release();
    }

    void setError(const char *fmt, ...) {
        va_list args;
        va_start(args, fmt);
        vsnprintf(lastErrorBuf, sizeof(lastErrorBuf), fmt, args);
        va_end(args);
    }

    void setInteropNote(const char *fmt, ...) {
        va_list args;
        va_start(args, fmt);
        vsnprintf(interopNoteBuf, sizeof(interopNoteBuf), fmt, args);
        va_end(args);
    }

    bool loadWglInterop() {
        pwglDXOpenDeviceNV = (PFNWGLDXOPENDEVICENVPROC)wglGetProcAddress("wglDXOpenDeviceNV");
        pwglDXCloseDeviceNV = (PFNWGLDXCLOSEDEVICENVPROC)wglGetProcAddress("wglDXCloseDeviceNV");
        pwglDXRegisterObjectNV = (PFNWGLDXREGISTEROBJECTNVPROC)wglGetProcAddress("wglDXRegisterObjectNV");
        pwglDXUnregisterObjectNV = (PFNWGLDXUNREGISTEROBJECTNVPROC)wglGetProcAddress("wglDXUnregisterObjectNV");
        pwglDXLockObjectsNV = (PFNWGLDXLOCKOBJECTSNVPROC)wglGetProcAddress("wglDXLockObjectsNV");
        pwglDXUnlockObjectsNV = (PFNWGLDXUNLOCKOBJECTSNVPROC)wglGetProcAddress("wglDXUnlockObjectsNV");
        return pwglDXOpenDeviceNV && pwglDXCloseDeviceNV && pwglDXRegisterObjectNV &&
               pwglDXUnregisterObjectNV && pwglDXLockObjectsNV && pwglDXUnlockObjectsNV;
    }

    // Picks the bridge from the GL context that is actually current,
    // not from Kivy's backend name: "angle_sdl3" only *requests* an
    // OpenGL ES context, and SDL3 satisfies that with the driver's own
    // native ES profile over WGL when one exists (NVIDIA, for example),
    // loading ANGLE only when it doesn't, or when SDL_OPENGL_ES_DRIVER=1
    // forces it. So the same backend name can mean a WGL context (use
    // WGL_NV_DX_interop2) or an ANGLE EGL context (use
    // EGL_ANGLE_d3d_texture_client_buffer). SDL_EGL_GetCurrentDisplay()
    // answers exactly that: non-NULL only when SDL's current context is
    // an EGL one. Also resolves the few GL functions this file calls
    // through SDL_GL_GetProcAddress so they hit that same context.
    // Must run on the Kivy main thread with Kivy's context current.
    void detectBridgeAndResolveGl() {
        bridge = BRIDGE_WGL;
        HMODULE hSDL = GetModuleHandleW(L"SDL3.dll");
        if (hSDL) {
            peglGetCurrentDisplay = (PFNEGLGETCURRENTDISPLAYPROC)GetProcAddress(hSDL, "SDL_EGL_GetCurrentDisplay");
            if (peglGetCurrentDisplay && peglGetCurrentDisplay())
                bridge = BRIDGE_EGL;
            auto sdlGlGetProc = (SDLGLGetProcAddressFn)GetProcAddress(hSDL, "SDL_GL_GetProcAddress");
            if (sdlGlGetProc) {
                pglGenTextures = (GenTexturesFn)sdlGlGetProc("glGenTextures");
                pglBindTexture = (BindTextureFn)sdlGlGetProc("glBindTexture");
                pglDeleteTextures = (DeleteTexturesFn)sdlGlGetProc("glDeleteTextures");
                pglTexParameteri = (TexParameteriFn)sdlGlGetProc("glTexParameteri");
                pglGetIntegerv = (GetIntegervFn)sdlGlGetProc("glGetIntegerv");
            }
        }
        // Without SDL3 (not expected in a Kivy process, but harmless),
        // or if SDL couldn't resolve them, a WGL context can still use
        // opengl32's own exports. An EGL context can't -- the EGL
        // bridge then reports why and falls back to the CPU copy.
        if (bridge == BRIDGE_WGL &&
            (!pglGenTextures || !pglBindTexture || !pglDeleteTextures ||
             !pglTexParameteri || !pglGetIntegerv)) {
            pglGenTextures = glGenTextures;
            pglBindTexture = glBindTexture;
            pglDeleteTextures = glDeleteTextures;
            pglTexParameteri = glTexParameteri;
            pglGetIntegerv = glGetIntegerv;
        }
    }

    // Creates glTex with linear filtering and edge clamping. Kivy never
    // sets sampler state on a texture it only wraps by id, and GL's
    // default minification filter uses mipmaps this texture doesn't
    // have, so without this it is "incomplete" and ANGLE samples it as
    // black. Restores whatever texture Kivy had bound, so Kivy's own
    // view of the GL state stays correct.
    void createGlTexture() {
        GLint prev = 0;
        pglGetIntegerv(GL_TEXTURE_BINDING_2D, &prev);
        pglGenTextures(1, &glTex);
        pglBindTexture(GL_TEXTURE_2D, glTex);
        pglTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        pglTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        pglTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        pglTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        pglBindTexture(GL_TEXTURE_2D, (GLuint)prev);
    }

    // eglBindTexImage attaches to whatever texture is bound, so bind
    // glTex for the call and then put Kivy's binding back.
    bool eglBindToGlTex() {
        GLint prev = 0;
        pglGetIntegerv(GL_TEXTURE_BINDING_2D, &prev);
        pglBindTexture(GL_TEXTURE_2D, glTex);
        bool ok = peglBindTexImage(eglDpy, eglClientBufSurf, EGL_BACK_BUFFER) != 0;
        pglBindTexture(GL_TEXTURE_2D, (GLuint)prev);
        return ok;
    }

    // Resolves the EGL entry points through SDL3's own accessor
    // (SDL_EGL_GetProcAddress), so they come from the same libEGL that
    // SDL loaded for Kivy's context, and the display queried below is
    // the in-use one -- which is what makes EGL_ANGLE_device_d3d return
    // ANGLE's *real* D3D11 device rather than a second, independent one.
    // Only called once detectBridgeAndResolveGl() has seen an EGL
    // context, so peglGetCurrentDisplay is already set.
    bool loadEglInterop() {
        HMODULE hSDL = GetModuleHandleW(L"SDL3.dll");
        if (!hSDL || !peglGetCurrentDisplay) { setInteropNote("SDL3 EGL accessors unavailable"); return false; }
        peglGetProcAddress = (PFNEGLGETPROCADDRESSPROC)GetProcAddress(hSDL, "SDL_EGL_GetProcAddress");
        if (!peglGetProcAddress) {
            setInteropNote("SDL3.dll does not export SDL_EGL_GetProcAddress");
            return false;
        }
        if (!pglGenTextures || !pglBindTexture || !pglDeleteTextures ||
            !pglTexParameteri || !pglGetIntegerv) {
            setInteropNote("SDL_GL_GetProcAddress could not resolve the GL texture functions");
            return false;
        }
        peglGetError = (PFNEGLGETERRORPROC)peglGetProcAddress("eglGetError");
        peglChooseConfig = (PFNEGLCHOOSECONFIGPROC)peglGetProcAddress("eglChooseConfig");
        peglQueryDisplayAttribEXT = (PFNEGLQUERYDISPLAYATTRIBEXTPROC)peglGetProcAddress("eglQueryDisplayAttribEXT");
        peglQueryDeviceAttribEXT = (PFNEGLQUERYDEVICEATTRIBEXTPROC)peglGetProcAddress("eglQueryDeviceAttribEXT");
        peglCreatePbufferFromClientBuffer = (PFNEGLCREATEPBUFFERFROMCLIENTBUFFERPROC)peglGetProcAddress("eglCreatePbufferFromClientBuffer");
        peglBindTexImage = (PFNEGLBINDTEXIMAGEPROC)peglGetProcAddress("eglBindTexImage");
        peglReleaseTexImage = (PFNEGLRELEASETEXIMAGEPROC)peglGetProcAddress("eglReleaseTexImage");
        peglDestroySurface = (PFNEGLDESTROYSURFACEPROC)peglGetProcAddress("eglDestroySurface");
        if (!peglGetError || !peglChooseConfig || !peglQueryDisplayAttribEXT ||
            !peglQueryDeviceAttribEXT || !peglCreatePbufferFromClientBuffer ||
            !peglBindTexImage || !peglReleaseTexImage || !peglDestroySurface) {
            setInteropNote("one or more EGL entry points did not resolve via SDL_EGL_GetProcAddress");
            return false;
        }
        return true;
    }

    // Shared D3D11 setup: multithread-protect the device (MF's internal
    // decode threads and this thread both touch it) and bind it into an
    // IMFDXGIDeviceManager.
    bool finishDeviceSetup() {
        ID3D10Multithread *mt = nullptr;
        if (SUCCEEDED(deviceCtx->QueryInterface(__uuidof(ID3D10Multithread), (void**)&mt))) {
            mt->SetMultithreadProtected(TRUE);
            mt->Release();
        }
        UINT resetToken = 0;
        HRESULT hr = MFCreateDXGIDeviceManager(&resetToken, &dxgiMgr);
        if (FAILED(hr)) { setError("MFCreateDXGIDeviceManager failed: 0x%08lX", hr); return false; }
        hr = dxgiMgr->ResetDevice(device, resetToken);
        if (FAILED(hr)) { setError("IMFDXGIDeviceManager::ResetDevice failed: 0x%08lX", hr); return false; }
        return true;
    }

    // Creates our own independent D3D11 device on adapter 0, for Media
    // Foundation to decode into. Used directly by the WGL path, and as
    // the EGL path's fallback when ANGLE's own device can't be obtained
    // (in which case EGL zero-copy is unavailable for this player, but
    // decode + CPU-copy delivery still works correctly).
    bool createOwnDevice() {
        IDXGIFactory1 *factory = nullptr;
        HRESULT hr = CreateDXGIFactory1(__uuidof(IDXGIFactory1), (void**)&factory);
        if (FAILED(hr)) { setError("CreateDXGIFactory1 failed: 0x%08lX", hr); return false; }
        IDXGIAdapter1 *adapter = nullptr;
        // Adapter 0, not LUID-matched to the GL context's adapter: a
        // mismatch is detected cheaply and cleanly at the interop
        // registration call itself (wglDXOpenDeviceNV fails), so no
        // adapter-enumeration/matching logic is needed up front -- a
        // mismatch there just means this player runs CPU-copy fallback.
        hr = factory->EnumAdapters1(0, &adapter);
        factory->Release();
        if (FAILED(hr)) { setError("EnumAdapters1(0) failed: 0x%08lX", hr); return false; }

        D3D_FEATURE_LEVEL fl;
        hr = D3D11CreateDevice(adapter, D3D_DRIVER_TYPE_UNKNOWN, nullptr,
                                D3D11_CREATE_DEVICE_BGRA_SUPPORT | D3D11_CREATE_DEVICE_VIDEO_SUPPORT,
                                nullptr, 0, D3D11_SDK_VERSION, &device, &fl, &deviceCtx);
        adapter->Release();
        if (FAILED(hr)) { setError("D3D11CreateDevice failed: 0x%08lX", hr); return false; }
        ownsDevice = true;
        return true;
    }

    bool setupDeviceWgl() {
        if (!loadWglInterop()) {
            setInteropNote("WGL_NV_DX_interop2 not available on this GL context");
            // Still create a device for MF decode; interop probing will
            // simply fail later and the CPU-copy fallback takes over.
        }
        if (!createOwnDevice()) return false;
        return finishDeviceSetup();
    }

    // Attempts to obtain ANGLE's own device (required for true
    // zero-copy: a texture from a different device on the same adapter
    // is rejected by eglCreatePbufferFromClientBuffer). If any step fails, falls back to an
    // independent device so decode + CPU-copy delivery still works;
    // eglDpy/the EGL function pointers are left unset in that case, so
    // probeInterop()'s EGL branch cleanly no-ops rather than crashing.
    bool setupDeviceEgl() {
        if (loadEglInterop()) {
            eglDpy = peglGetCurrentDisplay();
            EGLAttrib eglDeviceAttrib = 0;
            EGLDeviceEXT eglDevice = nullptr;
            if (eglDpy) {
                peglQueryDisplayAttribEXT(eglDpy, EGL_DEVICE_EXT, &eglDeviceAttrib);
                eglDevice = (EGLDeviceEXT)eglDeviceAttrib;
            }
            EGLAttrib d3dDeviceAttrib = 0;
            if (eglDevice) {
                peglQueryDeviceAttribEXT(eglDevice, EGL_D3D11_DEVICE_ANGLE, &d3dDeviceAttrib);
                device = (ID3D11Device*)d3dDeviceAttrib;
            }
            if (device) {
                device->GetImmediateContext(&deviceCtx);
                ownsDevice = false;  // ANGLE owns this device; we only borrow it
            } else {
                setInteropNote("the EGL display does not expose a D3D11 device "
                               "(EGL_ANGLE_device_d3d), so it is not ANGLE on D3D11");
                eglDpy = nullptr;  // make sure probeInterop()'s EGL branch no-ops
            }
        }

        if (!device) {
            // Either loadEglInterop() failed outright, or it succeeded
            // but ANGLE's device still couldn't be obtained -- either
            // way, fall back to an independent device so MF can still
            // decode (just without the EGL zero-copy bridge).
            if (!createOwnDevice()) return false;
            return finishDeviceSetup();
        }

        // A valid EGLConfig is required by eglCreatePbufferFromClientBuffer
        // to validate the pbuffer's pixel format. This is a pure query against the current display; it doesn't create or
        // touch any live surface/context, so it's safe to do once here
        // regardless of how Kivy's own context was configured.
        EGLint cfgAttribs[] = {
            EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
            EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
            EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8,
            EGL_NONE
        };
        EGLint numConfigs = 0;
        if (!peglChooseConfig(eglDpy, cfgAttribs, &eglConfig, 1, &numConfigs) || numConfigs == 0) {
            // ANGLE's device is still fine to decode into; only the
            // zero-copy bridge is unusable, so fall back to the CPU copy.
            setInteropNote("eglChooseConfig found no matching config");
            eglDpy = nullptr;  // make sure probeInterop()'s EGL branch no-ops
        }

        return finishDeviceSetup();
    }

    bool setupEngine() {
        notify = new EngineNotify();
        HRESULT hr = create_engine(softwareDecode ? nullptr : dxgiMgr, notify, &engine);
        if (FAILED(hr)) { setError("IMFMediaEngine creation failed: 0x%08lX", hr); return false; }
        return true;
    }

    void load() {
        detectBridgeAndResolveGl();
        bool ok =(bridge == BRIDGE_EGL) ? setupDeviceEgl() : setupDeviceWgl();
        if (ok) ok = setupEngine();
        if (!ok) return;  // lastErrorBuf already set; engine stays NULL,
                           // every subsequent call below is then a no-op.

        set_engine_source(engine, url);
        // Non-blocking: readiness, native size, and frame availability
        // are all discovered later via hasNewFrame()/retrieveFrame(),
        // polled from the caller's own Clock-driven tick.
    }

    // Reopens the source on a software-decoding engine. Called once, when
    // the D3D11 engine reports MF_MEDIA_ENGINE_ERR_SRC_NOT_SUPPORTED:
    // with a DXGI device manager the engine only builds a pipeline from
    // decoders that support Direct3D 11, so a format whose only decoder
    // is software-only (MPEG-1, for example) is rejected there even
    // though Windows can play it. Every frame is then a CPU copy.
    void retryInSoftware() {
        if (engine) { engine->Shutdown(); engine->Release(); engine = nullptr; }
        if (notify) { notify->Release(); notify = nullptr; }
        softwareDecode = true;
        HRESULT hr = CoCreateInstance(CLSID_WICImagingFactory, nullptr, CLSCTX_INPROC_SERVER,
                                      IID_PPV_ARGS(&wic));
        if (FAILED(hr)) { setError("WIC imaging factory creation failed: 0x%08lX", hr); return; }
        if (!setupEngine()) return;
        // No GL bridge applies to WIC frames; mark it settled so
        // usingCpuFallback() reports the CPU copy with this reason.
        interopProbed = true;
        interopOk = false;
        setInteropNote("this format has no Direct3D 11 decoder, so it is decoded in software");
        engine->SetVolume(volume);
        set_engine_source(engine, url);
        if (wantPlay) engine->Play();
    }

    bool ensureDestTexture() {
        if (destTex || (softwareDecode && texWidth)) return true;
        DWORD cx = 0, cy = 0;
        if (FAILED(engine->GetNativeVideoSize(&cx, &cy)) || cx == 0 || cy == 0) return false;
        if (softwareDecode) {
            // Frames go through a WIC bitmap; only the size is needed.
            texWidth = (int)cx;
            texHeight = (int)cy;
            return true;
        }
        D3D11_TEXTURE2D_DESC td = {};
        td.Width = cx; td.Height = cy; td.MipLevels = 1; td.ArraySize = 1;
        td.Format = DXGI_FORMAT_B8G8R8A8_UNORM;
        td.SampleDesc.Count = 1;
        td.Usage = D3D11_USAGE_DEFAULT;
        td.BindFlags = D3D11_BIND_RENDER_TARGET | D3D11_BIND_SHADER_RESOURCE;
        HRESULT hr = device->CreateTexture2D(&td, nullptr, &destTex);
        if (FAILED(hr)) { setError("CreateTexture2D(dest) failed: 0x%08lX", hr); return false; }
        texWidth = (int)cx;
        texHeight = (int)cy;
        return true;
    }

    // One-time bridge registration, called lazily on the first
    // successfully transferred frame (destTex must already exist).
    void probeInterop() {
        if (bridge == BRIDGE_WGL) {
            if (!pwglDXOpenDeviceNV) return;  // loadWglInterop already failed
            wglDevice = pwglDXOpenDeviceNV(device);
            if (!wglDevice) { setInteropNote("wglDXOpenDeviceNV failed (adapter mismatch)"); return; }
            createGlTexture();
            wglObj =pwglDXRegisterObjectNV(wglDevice, destTex, glTex, GL_TEXTURE_2D, WGL_ACCESS_READ_ONLY_NV);
            if (!wglObj) {
                setInteropNote("wglDXRegisterObjectNV failed");
                pwglDXCloseDeviceNV(wglDevice);
                wglDevice = nullptr;
                pglDeleteTextures(1, &glTex);
                glTex = 0;
                return;
            }
            interopOk = true;
        } else {
            if (!eglDpy || !peglCreatePbufferFromClientBuffer) return;  // setupDeviceEgl already fell back to CPU-copy
            createGlTexture();
            if (!glTex) { setInteropNote("glGenTextures returned 0 on the EGL context"); return; }
            EGLint attribs[] = { EGL_TEXTURE_FORMAT, EGL_TEXTURE_RGBA,
                                 EGL_TEXTURE_TARGET, EGL_TEXTURE_2D_ATTR, EGL_NONE };
            eglClientBufSurf = peglCreatePbufferFromClientBuffer(
                eglDpy, EGL_D3D_TEXTURE_ANGLE, (EGLClientBuffer)destTex, eglConfig, attribs);
            if (eglClientBufSurf == EGL_NO_SURFACE) {
                setInteropNote("eglCreatePbufferFromClientBuffer failed: 0x%04X", peglGetError());
                pglDeleteTextures(1, &glTex);
                glTex = 0;
                return;
            }
            // Bind once now, so a failure here still falls back to the
            // CPU copy instead of handing Kivy an empty texture.
            if (!eglBindToGlTex()) {
                setInteropNote("eglBindTexImage failed: 0x%04X", peglGetError());
                peglDestroySurface(eglDpy, eglClientBufSurf);
                eglClientBufSurf = EGL_NO_SURFACE;
                pglDeleteTextures(1, &glTex);
                glTex = 0;
                return;
            }
            eglBound = true;
            interopOk = true;
        }
    }

    // Refreshes the zero-copy GL texture after a TransferVideoFrame call.
    // WGL: lock for GL access (stays locked until the next transfer, so
    // Kivy's own render pass -- which happens after this tick -- safely
    // samples it; unlocked right before the next TransferVideoFrame).
    // EGL: the same shape with eglReleaseTexImage/eglBindTexImage --
    // released right before the next TransferVideoFrame, re-bound right
    // after it. EGL rejects binding a surface that is already bound
    // (EGL_BAD_ACCESS), so the release is what makes the re-bind legal.
    void refreshZeroCopy() {
        if (bridge == BRIDGE_WGL) {
            pwglDXLockObjectsNV(wglDevice, 1, &wglObj);
            wglLocked = true;
        } else if (!eglBound) {
            eglBound = eglBindToGlTex();
        }
    }

    // Counterpart of refreshZeroCopy(), called before each transfer.
    void releaseZeroCopy() {
        if (!interopOk) return;
        if (bridge == BRIDGE_WGL) {
            if (wglLocked) { pwglDXUnlockObjectsNV(wglDevice, 1, &wglObj); wglLocked = false; }
        } else if (eglBound) {
            peglReleaseTexImage(eglDpy, eglClientBufSurf, EGL_BACK_BUFFER);
            eglBound = false;
        }
    }

    void copyToCpu() {
        if (!stagingTex) {
            D3D11_TEXTURE2D_DESC td = {};
            destTex->GetDesc(&td);
            td.Usage = D3D11_USAGE_STAGING;
            td.BindFlags = 0;
            td.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
            if (FAILED(device->CreateTexture2D(&td, nullptr, &stagingTex))) {
                setError("CreateTexture2D(staging) failed");
                return;
            }
        }
        deviceCtx->CopyResource(stagingTex, destTex);
        D3D11_MAPPED_SUBRESOURCE mapped;
        if (FAILED(deviceCtx->Map(stagingTex, 0, D3D11_MAP_READ, 0, &mapped))) {
            setError("Map(staging) failed");
            return;
        }
        cpuBuf.resize((size_t)texWidth * 4 * texHeight);
        bgra_to_rgba((const uint8_t*)mapped.pData, mapped.RowPitch, texWidth, texHeight,
                     cpuBuf.data());
        deviceCtx->Unmap(stagingTex, 0);
    }

    bool hasNewFrame() {
        if (!engine) return false;
        LONGLONG pts = 0;
        if (engine->OnVideoStreamTick(&pts) == S_OK) {
            pendingPts = pts;
            framePending = true;
        }
        return framePending;
    }

    VideoFrame *retrieveFrame() {
        if (!framePending || !engine) return nullptr;
        framePending = false;

        if (!ensureDestTexture()) return nullptr;

        if (softwareDecode) {
            cpuBuf.resize((size_t)texWidth * 4 * texHeight);
            if (!transfer_to_wic(engine, wic, &wicBmp, texWidth, texHeight, cpuBuf.data()))
                return nullptr;
            outFrame.pts = pendingPts / 1.0e7;
            outFrame.width = texWidth;
            outFrame.height = texHeight;
            outFrame.gl_texture_id = 0;
            outFrame.gl_target = 0;
            outFrame.data = cpuBuf.data();
            outFrame.datasize = (unsigned int)cpuBuf.size();
            outFrame.rowsize = (unsigned int)texWidth * 4;
            return &outFrame;
        }

        releaseZeroCopy();

        if (FAILED(engine->TransferVideoFrame(destTex, nullptr, nullptr, nullptr))) return nullptr;

        if (!interopProbed) {
            interopProbed = true;
            probeInterop();
        }

        outFrame.pts = pendingPts / 1.0e7;
        outFrame.width = texWidth;
        outFrame.height = texHeight;

        if (interopOk) {
            refreshZeroCopy();
            outFrame.gl_texture_id = glTex;
            outFrame.gl_target = GL_TEXTURE_2D;
            outFrame.data = nullptr;
            outFrame.datasize = 0;
            outFrame.rowsize = 0;
        } else {
            copyToCpu();
            outFrame.gl_texture_id = 0;
            outFrame.gl_target = 0;
            outFrame.data = cpuBuf.data();
            outFrame.datasize = (unsigned int)cpuBuf.size();
            outFrame.rowsize = (unsigned int)texWidth * 4;
        }
        return &outFrame;
    }

    void unload() {
        if (bridge == BRIDGE_WGL) {
            if (wglDevice) {
                if (wglLocked) { pwglDXUnlockObjectsNV(wglDevice, 1, &wglObj); wglLocked = false; }
                if (wglObj) pwglDXUnregisterObjectNV(wglDevice, wglObj);
                pwglDXCloseDeviceNV(wglDevice);
                wglDevice = nullptr;
                wglObj = nullptr;
            }
        } else {
            if (eglClientBufSurf != EGL_NO_SURFACE) {
                if (eglBound) peglReleaseTexImage(eglDpy, eglClientBufSurf, EGL_BACK_BUFFER);
                eglBound = false;
                peglDestroySurface(eglDpy, eglClientBufSurf);
                eglClientBufSurf = EGL_NO_SURFACE;
            }
        }
        if (glTex) { pglDeleteTextures(1, &glTex); glTex = 0; }
        interopProbed = false;
        interopOk = false;

        if (stagingTex) { stagingTex->Release(); stagingTex = nullptr; }
        if (destTex) { destTex->Release(); destTex = nullptr; }
        if (wicBmp) { wicBmp->Release(); wicBmp = nullptr; }
        if (wic) { wic->Release(); wic = nullptr; }
        softwareDecode = false;
        texWidth = texHeight = 0;
        framePending = false;

        if (engine) { engine->Shutdown(); engine->Release(); engine = nullptr; }
        if (notify) { notify->Release(); notify = nullptr; }
        if (dxgiMgr) { dxgiMgr->Release(); dxgiMgr = nullptr; }
        if (deviceCtx) { deviceCtx->Release(); deviceCtx = nullptr; }
        if (device && ownsDevice) { device->Release(); }
        device = nullptr;
    }

    void play()   { wantPlay = true; if (engine) engine->Play(); }
    void pause()  { wantPlay = false; if (engine) engine->Pause(); }
    void stop()   { wantPlay = false; if (engine) { engine->Pause(); engine->SetCurrentTime(0.0); } }
    void seek(double seconds, bool /*precise -- see header note*/) {
        if (engine) engine->SetCurrentTime(seconds);
    }
    double position() { return engine ? engine->GetCurrentTime() : 0.0; }
    double duration() { return engine ? engine->GetDuration() : 0.0; }
    void setVolume(double v) { volume = v; if (engine) engine->SetVolume(v); }
    bool isEOS() { return notify && notify->ended.load(); }
    bool isBuffering() { return notify && notify->buffering.load(); }

    // True once setup failed or the engine reported an error (for
    // example a format with no installed decoder). Copies the engine's
    // error into lastErrorBuf the first time it is seen. A source the
    // D3D11 engine rejects is first retried in software (see
    // retryInSoftware()); only a failure there is reported.
    bool hasError() {
        if (lastErrorBuf[0]) return true;
        if (!notify || !notify->errored.load()) return false;
        if (!softwareDecode &&
            notify->errCode.load() == MF_MEDIA_ENGINE_ERR_SRC_NOT_SUPPORTED) {
            retryInSoftware();
            return lastErrorBuf[0] != 0;
        }
        const char *what = "unknown error";
        switch (notify->errCode.load()) {
            case MF_MEDIA_ENGINE_ERR_ABORTED: what = "aborted"; break;
            case MF_MEDIA_ENGINE_ERR_NETWORK: what = "network error"; break;
            case MF_MEDIA_ENGINE_ERR_DECODE: what = "decode error"; break;
            case MF_MEDIA_ENGINE_ERR_SRC_NOT_SUPPORTED:
                what = "format not supported (no Media Foundation source or "
                       "decoder installed for it)";
                break;
            case MF_MEDIA_ENGINE_ERR_ENCRYPTED: what = "encrypted media"; break;
        }
        setError("playback failed: %s (HRESULT 0x%08lX)", what,
                 (unsigned long)notify->errHr.load());
        return true;
    }
};

// ---------------------------------------------------------------------
// VideoFrame
// ---------------------------------------------------------------------
VideoFrame::VideoFrame()
    : data(nullptr), datasize(0), rowsize(0), width(0), height(0), pts(0.0),
      gl_texture_id(0), gl_target(0) {}
VideoFrame::~VideoFrame() {}

// ---------------------------------------------------------------------
// VideoPlayer -- thin forwarding layer onto MFVideoPlayerImpl
// ---------------------------------------------------------------------
VideoPlayer::VideoPlayer(const char *url) {
    impl = new MFVideoPlayerImpl(url);
}
VideoPlayer::~VideoPlayer() { delete impl; }

void VideoPlayer::load() { impl->load(); }
void VideoPlayer::play() { impl->play(); }
void VideoPlayer::pause() { impl->pause(); }
void VideoPlayer::stop() { impl->stop(); }
void VideoPlayer::unload() { impl->unload(); }
void VideoPlayer::seek(double seconds, bool precise) { impl->seek(seconds, precise); }
double VideoPlayer::position() { return impl->position(); }
double VideoPlayer::duration() { return impl->duration(); }
void VideoPlayer::setVolume(double v) { impl->setVolume(v); }
bool VideoPlayer::hasNewFrame() { return impl->hasNewFrame(); }
VideoFrame *VideoPlayer::retrieveFrame() { return impl->retrieveFrame(); }
bool VideoPlayer::isEOS() { return impl->isEOS(); }
bool VideoPlayer::isBuffering() { return impl->isBuffering(); }
bool VideoPlayer::hasError() { return impl->hasError(); }
const char *VideoPlayer::lastError() { return impl->lastErrorBuf; }
const char *VideoPlayer::interopNote() { return impl->interopNoteBuf; }
bool VideoPlayer::usingCpuFallback() { return impl->interopProbed && !impl->interopOk; }

// Sleeps ~ms milliseconds while pumping this thread's message queue.
// generateThumbnail() runs on the Kivy main thread, which is a COM STA
// (SDL3 initializes it that way) and owns the app window; an STA that
// blocks must keep pumping, and doing so also keeps the window from
// being flagged "(Not Responding)" during the wait.
static void PumpAndSleep(DWORD ms) {
    MSG msg;
    DWORD start = GetTickCount();
    do {
        while (PeekMessageW(&msg, nullptr, 0, 0, PM_REMOVE)) {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
        Sleep(1);
    } while (GetTickCount() - start < ms);
}

// ---------------------------------------------------------------------
// generateThumbnail -- synchronous, one-shot, always CPU-copy. Unlike
// live playback this is explicitly allowed to block the calling thread
// briefly (same contract as the other providers' thumbnail paths).
// ---------------------------------------------------------------------

// Polls `done` while pumping messages, for at most ms milliseconds.
// Returns false on timeout or as soon as the engine reports an error.
template <typename Pred>
static bool wait_for(EngineNotify *notify, DWORD ms, Pred done) {
    ULONGLONG start = GetTickCount64();
    while (!done()) {
        if (notify->errored.load() || GetTickCount64() - start > ms) return false;
        PumpAndSleep(10);
    }
    return true;
}

// One thumbnail attempt. With a DXGI device manager the frame is
// decoded into a D3D11 texture on `device` and read back through a
// staging copy; without one (software decode) it comes out through a
// WIC bitmap. *unsupported is set when the engine rejected the source,
// which is the case the software retry covers.
static VideoFrame *thumbnail_attempt(const std::wstring &url, double t, int w, int h,
                                     IMFDXGIDeviceManager *dxgiMgr, ID3D11Device *device,
                                     ID3D11DeviceContext *ctx, bool *unsupported) {
    *unsupported = false;
    VideoFrame *result = nullptr;
    EngineNotify *notify = new EngineNotify();
    IMFMediaEngine *engine = nullptr;
    IWICImagingFactory *wic = nullptr;
    IWICBitmap *bmp = nullptr;
    ID3D11Texture2D *tex = nullptr;
    ID3D11Texture2D *staging = nullptr;
    DWORD cx = 0, cy = 0;
    int dstW = 0, dstH = 0;

    if (FAILED(create_engine(dxgiMgr, notify, &engine))) goto cleanup;
    set_engine_source(engine, url);

    if (!wait_for(notify, 8000, [&] {
            return engine->GetReadyState() >= MF_MEDIA_ENGINE_READY_HAVE_CURRENT_DATA; })) {
        *unsupported = notify->errored.load() &&
            notify->errCode.load() == MF_MEDIA_ENGINE_ERR_SRC_NOT_SUPPORTED;
        goto cleanup;
    }

    if (t > 0.0) {
        engine->SetCurrentTime(t);
        // No dedicated "seeked" flag on this short-lived EngineNotify;
        // GetCurrentTime converging near the target is a sufficient,
        // simple readiness signal for a one-shot thumbnail. A seek that
        // doesn't converge still yields the nearest frame below.
        wait_for(notify, 8000, [&] { return engine->GetCurrentTime() >= t - 0.25; });
    }

    {
        LONGLONG pts = 0;
        if (!wait_for(notify, 8000, [&] { return engine->OnVideoStreamTick(&pts) == S_OK; }))
            goto cleanup;
    }

    if (FAILED(engine->GetNativeVideoSize(&cx, &cy)) || cx == 0 || cy == 0) goto cleanup;
    dstW = (w > 0) ? w : (int)cx;
    dstH = (h > 0) ? h : (int)cy;

    result = new VideoFrame();
    result->width = dstW;
    result->height = dstH;
    result->rowsize = dstW * 4;
    result->datasize = result->rowsize * dstH;
    result->data = (char*)malloc(result->datasize);

    if (!dxgiMgr) {
        if (FAILED(CoCreateInstance(CLSID_WICImagingFactory, nullptr, CLSCTX_INPROC_SERVER,
                                    IID_PPV_ARGS(&wic))) ||
            !transfer_to_wic(engine, wic, &bmp, dstW, dstH, result->data)) {
            free(result->data);
            delete result;
            result = nullptr;
        }
        goto cleanup;
    }

    {
        D3D11_TEXTURE2D_DESC td = {};
        td.Width = dstW; td.Height = dstH; td.MipLevels = 1; td.ArraySize = 1;
        td.Format = DXGI_FORMAT_B8G8R8A8_UNORM;
        td.SampleDesc.Count = 1;
        td.Usage = D3D11_USAGE_DEFAULT;
        td.BindFlags = D3D11_BIND_RENDER_TARGET | D3D11_BIND_SHADER_RESOURCE;
        bool ok = SUCCEEDED(device->CreateTexture2D(&td, nullptr, &tex));
        RECT destRect = {0, 0, dstW, dstH};
        ok = ok && SUCCEEDED(engine->TransferVideoFrame(tex, nullptr, &destRect, nullptr));
        td.Usage = D3D11_USAGE_STAGING;
        td.BindFlags = 0;
        td.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
        ok = ok && SUCCEEDED(device->CreateTexture2D(&td, nullptr, &staging));
        D3D11_MAPPED_SUBRESOURCE mapped;
        if (ok) {
            ctx->CopyResource(staging, tex);
            ok = SUCCEEDED(ctx->Map(staging, 0, D3D11_MAP_READ, 0, &mapped));
        }
        if (ok) {
            bgra_to_rgba((const uint8_t*)mapped.pData, mapped.RowPitch, dstW, dstH,
                         result->data);
            ctx->Unmap(staging, 0);
        } else {
            free(result->data);
            delete result;
            result = nullptr;
        }
    }

cleanup:
    if (staging) staging->Release();
    if (tex) tex->Release();
    if (bmp) bmp->Release();
    if (wic) wic->Release();
    if (engine) { engine->Shutdown(); engine->Release(); }
    notify->Release();
    return result;
}

VideoFrame *VideoPlayer::generateThumbnail(const char *url, double t, int w, int h) {
    mf_runtime_acquire();
    VideoFrame *result = nullptr;
    std::wstring wurl = utf8_to_wide(url);

    IDXGIFactory1 *factory = nullptr;
    IDXGIAdapter1 *adapter = nullptr;
    ID3D11Device *device = nullptr;
    ID3D11DeviceContext *ctx = nullptr;
    IMFDXGIDeviceManager *dxgiMgr = nullptr;
    D3D_FEATURE_LEVEL fl;
    UINT resetToken = 0;
    bool unsupported = false;

    if (FAILED(CreateDXGIFactory1(__uuidof(IDXGIFactory1), (void**)&factory))) goto cleanup;
    if (FAILED(factory->EnumAdapters1(0, &adapter))) goto cleanup;
    if (FAILED(D3D11CreateDevice(adapter, D3D_DRIVER_TYPE_UNKNOWN, nullptr,
            D3D11_CREATE_DEVICE_BGRA_SUPPORT | D3D11_CREATE_DEVICE_VIDEO_SUPPORT,
            nullptr, 0, D3D11_SDK_VERSION, &device, &fl, &ctx))) goto cleanup;
    // Required before sharing the device with Media Foundation, exactly
    // as finishDeviceSetup() does for playback: MF's worker threads use
    // this device's immediate context concurrently with this thread.
    // Without it, the first thumbnail reproducibly hung forever between
    // reaching HAVE_CURRENT_DATA and the first OnVideoStreamTick frame.
    {
        ID3D10Multithread *mt = nullptr;
        if (SUCCEEDED(ctx->QueryInterface(__uuidof(ID3D10Multithread), (void**)&mt))) {
            mt->SetMultithreadProtected(TRUE);
            mt->Release();
        }
    }
    if (FAILED(MFCreateDXGIDeviceManager(&resetToken, &dxgiMgr))) goto cleanup;
    if (FAILED(dxgiMgr->ResetDevice(device, resetToken))) goto cleanup;

    result = thumbnail_attempt(wurl, t, w, h, dxgiMgr, device, ctx, &unsupported);
    // Same fallback as playback (MFVideoPlayerImpl::retryInSoftware()):
    // a source the D3D11 engine rejects is retried in software.
    if (!result && unsupported)
        result = thumbnail_attempt(wurl, t, w, h, nullptr, nullptr, nullptr, &unsupported);

cleanup:
    if (dxgiMgr) dxgiMgr->Release();
    if (ctx) ctx->Release();
    if (device) device->Release();
    if (adapter) adapter->Release();
    if (factory) factory->Release();
    mf_runtime_release();
    return result;
}
