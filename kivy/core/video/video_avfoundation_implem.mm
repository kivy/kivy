/*
 * Video provider implementation for macOS / iOS using AVFoundation.
 *
 * Pixel pipeline: the CVPixelBufferRef's underlying IOSurface is wrapped
 * as an ANGLE EGL pbuffer via EGL_ANGLE_iosurface_client_buffer and
 * bound to a persistent GL_TEXTURE_2D whose id is surfaced through
 * VideoFrame::gl_texture_id. The Cython layer wraps that id directly
 * into a kivy.graphics.Texture (with nofree=True) -- no per-frame
 * memcpy, no Texture.blit_buffer.
 *
 * Zero-copy is probed lazily on the first decoded frame (the Kivy GL
 * context isn't necessarily current at VideoPlayer construction time).
 * If the probe fails -- which on Kivy 3.0 macOS / iOS only happens when
 * something is fundamentally wrong (no ANGLE display, IOSurface
 * extension missing, eglChooseConfig fails, eglCreatePbufferFromClient-
 * Buffer fails on a known-good frame) -- the player gives up cleanly
 * and dispatches an EOS so the widget surfaces a clear failure instead
 * of a stuck black screen.
 *
 * Thumbnails (generateThumbnail) still use a CPU-copy CGImage -> BGRA
 * path; that's a one-shot read, not the per-frame hot path.
 */

#include "video_avfoundation_implem.h"

#include <string.h>
#include <stdlib.h>

#include <EGL/egl.h>
#include <EGL/eglext.h>
#if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
#  include <OpenGLES/ES2/gl.h>
#  include <OpenGLES/ES2/glext.h>
#else
#  include <GLES2/gl2.h>
#  include <GLES2/gl2ext.h>
#endif
#ifndef GL_BGRA_EXT
#  define GL_BGRA_EXT 0x80E1
#endif
#ifndef EGL_IOSURFACE_ANGLE
#  define EGL_IOSURFACE_ANGLE             0x3454
#endif
#ifndef EGL_IOSURFACE_PLANE_ANGLE
#  define EGL_IOSURFACE_PLANE_ANGLE       0x345A
#endif
#ifndef EGL_TEXTURE_TYPE_ANGLE
#  define EGL_TEXTURE_TYPE_ANGLE          0x345C
#endif
#ifndef EGL_TEXTURE_INTERNAL_FORMAT_ANGLE
#  define EGL_TEXTURE_INTERNAL_FORMAT_ANGLE 0x345D
#endif
#ifndef EGL_BIND_TO_TEXTURE_TARGET_ANGLE
#  define EGL_BIND_TO_TEXTURE_TARGET_ANGLE 0x348D
#endif


#if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
/* =====================================================================
 * GL entry-point resolution via eglGetProcAddress (iOS only).
 *
 * kivy-ios's ``ios`` recipe declares ``OpenGLES.framework`` in its
 * pbx_frameworks list, so any kivy-ios host project links Apple's
 * native OpenGL ES framework alongside ANGLE's
 * ``libGLESv2.xcframework`` (Kivy 3.0's actual GL provider on iOS).
 * Both export the same core GL symbols (glGenTextures, glBindTexture,
 * glTexParameteri, glDeleteTextures, glGetError, ...). At final link
 * time the linker resolves those names to ``OpenGLES.framework``,
 * whose implementations target ``EAGLContext`` -- Apple's native ES
 * context type, completely separate from the ``EGLContext`` that
 * ANGLE creates and Kivy currents on the main thread.
 *
 * With no ``EAGLContext`` bound, Apple's ``glGenTextures`` silently
 * returns 0 and leaves ``glGetError() == GL_NO_ERROR`` -- so the
 * zero-copy probe in ``_probeZeroCopy`` fails with no actionable
 * signal even though the ANGLE EGL context is healthy. We confirmed
 * this end-to-end during iOS bring-up (real A15 GPU and simulator
 * both, see kivy/kivy PR thread for the diagnostic traces).
 *
 * Fix: resolve the GL entry points we use through ``eglGetProcAddress``
 * against ANGLE's libEGL. Per EGL spec the returned pointer comes
 * from the same provider whose display is current, so this is robust
 * to any future change in the linked-frameworks list (including
 * ``OpenGLES.framework`` being removed from the kivy-ios template).
 *
 * macOS has no ``OpenGLES.framework`` available to link, so on that
 * platform the linker resolves directly to ANGLE's ``libGLESv2`` and
 * no indirection is required -- this block is iOS-only.
 * ===================================================================== */
typedef void (*_KivyGLGenTexturesProc)(GLsizei, GLuint *);
typedef void (*_KivyGLBindTextureProc)(GLenum, GLuint);
typedef void (*_KivyGLTexParameteriProc)(GLenum, GLenum, GLint);
typedef void (*_KivyGLDeleteTexturesProc)(GLsizei, const GLuint *);
typedef GLenum (*_KivyGLGetErrorProc)(void);

static _KivyGLGenTexturesProc _kivy_glGenTextures = NULL;
static _KivyGLBindTextureProc _kivy_glBindTexture = NULL;
static _KivyGLTexParameteriProc _kivy_glTexParameteri = NULL;
static _KivyGLDeleteTexturesProc _kivy_glDeleteTextures = NULL;
static _KivyGLGetErrorProc _kivy_glGetError = NULL;

static bool _kivyResolveANGLEGL(void) {
    if (_kivy_glGenTextures != NULL) {
        return true;
    }
    _kivy_glGenTextures = (_KivyGLGenTexturesProc)
        eglGetProcAddress("glGenTextures");
    _kivy_glBindTexture = (_KivyGLBindTextureProc)
        eglGetProcAddress("glBindTexture");
    _kivy_glTexParameteri = (_KivyGLTexParameteriProc)
        eglGetProcAddress("glTexParameteri");
    _kivy_glDeleteTextures = (_KivyGLDeleteTexturesProc)
        eglGetProcAddress("glDeleteTextures");
    _kivy_glGetError = (_KivyGLGetErrorProc)
        eglGetProcAddress("glGetError");
    if (_kivy_glGenTextures == NULL || _kivy_glBindTexture == NULL ||
        _kivy_glTexParameteri == NULL || _kivy_glDeleteTextures == NULL ||
        _kivy_glGetError == NULL) {
        // Partial resolve. Reset so the next probe retries; we'd rather
        // try again on the next decoded frame than commit to a half-
        // bound state.
        _kivy_glGenTextures = NULL;
        _kivy_glBindTexture = NULL;
        _kivy_glTexParameteri = NULL;
        _kivy_glDeleteTextures = NULL;
        _kivy_glGetError = NULL;
        return false;
    }
    return true;
}

// Shadow the standard GL names with our ANGLE-resolved pointers so the
// call sites below stay readable. The macros only affect this
// translation unit and do not leak through the header.
#define glGenTextures    _kivy_glGenTextures
#define glBindTexture    _kivy_glBindTexture
#define glTexParameteri  _kivy_glTexParameteri
#define glDeleteTextures _kivy_glDeleteTextures
#define glGetError       _kivy_glGetError
#endif  /* TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR */


// KVO context tag for the single observer we install (timeControlStatus).
static char kTimeControlStatusContext;


#if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
/* =====================================================================
 * iOS audio session setup.
 *
 * AVAudioSession is iOS-only -- macOS has no equivalent and routes
 * AVPlayer audio without app involvement. On iOS, without an active
 * AVAudioSession the AVPlayer audio output is silent (the device's
 * silent switch also forces audio off under the default category),
 * which makes a working video pipeline look broken.
 *
 * We activate the shared session lazily on the first VideoPlayer::load()
 * rather than at module import time so:
 *   - Importing Kivy or the video provider has no audio side effect
 *     for apps that never instantiate a video player.
 *   - An app that has already configured AVAudioSession before the
 *     first video loads keeps its choices; we only override the
 *     category if the session is still on iOS's default
 *     (``AVAudioSessionCategorySoloAmbient``).
 *
 * Policy when we do override: ``.playback`` + ``.moviePlayback``.
 * Canonical for a video player and matches user expectation -- audio
 * continues even when the device's silent switch is engaged. Apps
 * that want different semantics (e.g. ``.ambient`` to mix with other
 * audio, or ``.playAndRecord`` to also use the mic) should set the
 * category themselves before loading a video; we'll then see a
 * non-default category and leave it alone.
 *
 * Interruption / route-change handling is deliberately not done here.
 * AVPlayer handles route changes transparently (continues playback on
 * the new output), and apps that want explicit pause-on-interruption
 * can observe AVAudioSessionInterruptionNotification themselves.
 * ===================================================================== */
static dispatch_once_t _kivyAudioSessionOnce;
static void _kivyEnsureAudioSession() {
    dispatch_once(&_kivyAudioSessionOnce, ^{
        AVAudioSession *session = [AVAudioSession sharedInstance];
        NSError *err = nil;
        if ([session.category isEqualToString:
                AVAudioSessionCategorySoloAmbient]) {
            [session setCategory:AVAudioSessionCategoryPlayback
                            mode:AVAudioSessionModeMoviePlayback
                         options:0
                           error:&err];
            if (err != nil) {
                NSLog(@"VideoAVFoundation: failed to set AVAudioSession "
                      @"category: %@", err);
                err = nil;
            }
        }
        if (![session setActive:YES error:&err]) {
            NSLog(@"VideoAVFoundation: failed to activate "
                  @"AVAudioSession: %@", err);
        }
    });
}
#endif


/* =====================================================================
 * VideoFrame
 * ===================================================================== */

VideoFrame::VideoFrame()
    : data(NULL), datasize(0), rowsize(0),
      width(0), height(0), pts(0.0),
      gl_texture_id(0), gl_target(0) {}

VideoFrame::~VideoFrame() {
    if (data != NULL) {
        free(data);
        data = NULL;
    }
}


/* =====================================================================
 * KivyAVDelegate
 * ===================================================================== */

@implementation KivyAVDelegate

- (id)initWithOwner:(VideoPlayer *)owner {
    self = [super init];
    if (self) {
        mOwner = owner;
    }
    return self;
}

- (void)detachOwner {
    mOwner = NULL;
}

- (void)observeValueForKeyPath:(NSString *)keyPath
                      ofObject:(id)object
                        change:(NSDictionary<NSKeyValueChangeKey, id> *)change
                       context:(void *)context {
    if (mOwner == NULL) {
        return;
    }
    if (context == &kTimeControlStatusContext) {
        mOwner->_onTimeControlStatusChanged();
    } else {
        [super observeValueForKeyPath:keyPath
                             ofObject:object
                               change:change
                              context:context];
    }
}

- (void)playbackEnded:(NSNotification *)notification {
    if (mOwner != NULL) {
        mOwner->_onPlaybackEnded();
    }
}

@end


/* =====================================================================
 * VideoPlayer
 * ===================================================================== */

VideoPlayer::VideoPlayer(const char *url)
    : mUrl(nil), mPlayer(nil), mPlayerItem(nil), mVideoOutput(nil),
      mDelegate(nil),
      mVolume(1.0),
      mWantPlay(false), mIsEOS(false), mBuffering(false),
      mAutomaticallyWaitsToMinimizeStalling(true),
      mCurrentFrame(NULL), mHasFrame(false),
      mItemPrepared(false), mObserversInstalled(false),
      mZeroCopyFailed(false),
      mZeroCopyProbed(false), mZeroCopyAvailable(false),
      mEGLDisplay(NULL), mEGLConfig(NULL), mEGLPbuffer(NULL),
      mBoundPixelBuffer(NULL),
      mGLTexture(0), mGLTextureWidth(0), mGLTextureHeight(0)
{
    if (url != NULL) {
        mUrl = [[NSString alloc] initWithUTF8String:url];
    }
}

VideoPlayer::~VideoPlayer() {
    unload();
    if (mUrl != nil) {
        [mUrl release];
        mUrl = nil;
    }
}

void VideoPlayer::setAutomaticallyWaitsToMinimizeStalling(bool wait) {
    mAutomaticallyWaitsToMinimizeStalling = wait;
    if (mItemPrepared) {
        _applyBufferConfig();
    }
}

void VideoPlayer::_applyBufferConfig() {
    if (mPlayerItem == nil || mPlayer == nil) {
        return;
    }
    // Pass through to AVPlayer.automaticallyWaitsToMinimizeStalling.
    // YES (default) favors uninterrupted playback at the cost of
    // start-up latency; NO favors immediate playback start. See
    // ``options['automatically_waits_to_minimize_stalling']`` on
    // ``VideoAVFoundation``.
    if ([mPlayer respondsToSelector:
            @selector(setAutomaticallyWaitsToMinimizeStalling:)]) {
        mPlayer.automaticallyWaitsToMinimizeStalling =
            mAutomaticallyWaitsToMinimizeStalling ? YES : NO;
    }
}

void VideoPlayer::load() {
    if (mUrl == nil) {
        return;
    }
    unload();
    // Fresh load: re-arm zero-copy state. unload() already cleared the
    // probe and texture; clear the one-shot failure latch so a brand
    // new load gets a clean shot at the probe.
    mZeroCopyFailed = false;

#if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
    // First-load-wins activation of the iOS audio session. No-op on
    // every subsequent call (dispatch_once) and on macOS (compiled out).
    _kivyEnsureAudioSession();
#endif

    @autoreleasepool {
        // Accept both bare file paths and full URI strings.
        NSURL *nsurl = nil;
        if ([mUrl rangeOfString:@"://"].location == NSNotFound) {
            nsurl = [NSURL fileURLWithPath:mUrl];
        } else {
            nsurl = [NSURL URLWithString:mUrl];
        }
        if (nsurl == nil) {
            NSLog(@"VideoAVFoundation: invalid URL %@", mUrl);
            return;
        }

        AVAsset *asset = [AVAsset assetWithURL:nsurl];
        mPlayerItem = [[AVPlayerItem alloc] initWithAsset:asset];

        // Configure pixel output as BGRA with IOSurface backing so the
        // Phase 2 zero-copy path can wrap the IOSurface as a GL texture.
        NSDictionary *pixelBufferAttributes = @{
            (id)kCVPixelBufferPixelFormatTypeKey :
                @(kCVPixelFormatType_32BGRA),
            (id)kCVPixelBufferIOSurfacePropertiesKey : @{},
        };
        mVideoOutput = [[AVPlayerItemVideoOutput alloc]
            initWithPixelBufferAttributes:pixelBufferAttributes];
        [mPlayerItem addOutput:mVideoOutput];

        mPlayer = [[AVPlayer alloc] initWithPlayerItem:mPlayerItem];
        mPlayer.volume = (float)mVolume;

        mDelegate = [[KivyAVDelegate alloc] initWithOwner:this];
        _installObservers();
        _applyBufferConfig();

        mItemPrepared = true;
        mIsEOS = false;
    }
}

void VideoPlayer::_installObservers() {
    if (mObserversInstalled || mPlayerItem == nil ||
        mPlayer == nil || mDelegate == nil) {
        return;
    }
    // ``timeControlStatus`` lives on AVPlayer (not AVPlayerItem) and is
    // Apple's canonical signal for "I want to play but I'm stalled"
    // (.waitingToPlayAtSpecifiedRate) vs. "I'm actually playing"
    // (.playing) vs. "I'm paused" (.paused). It toggles deterministically
    // across play/pause/seek/stop cycles, including HLS streams. We use
    // it to drive the public ``buffering`` boolean.
    [mPlayer addObserver:mDelegate
              forKeyPath:@"timeControlStatus"
                 options:NSKeyValueObservingOptionNew
                 context:&kTimeControlStatusContext];
    [[NSNotificationCenter defaultCenter]
        addObserver:mDelegate
           selector:@selector(playbackEnded:)
               name:AVPlayerItemDidPlayToEndTimeNotification
             object:mPlayerItem];
    mObserversInstalled = true;
}

void VideoPlayer::_removeObservers() {
    if (!mObserversInstalled) {
        return;
    }
    if (mPlayer != nil && mDelegate != nil) {
        @try {
            [mPlayer removeObserver:mDelegate
                         forKeyPath:@"timeControlStatus"];
        }
        @catch (NSException *) { /* ignore double-remove */ }
    }
    if (mPlayerItem != nil && mDelegate != nil) {
        [[NSNotificationCenter defaultCenter]
            removeObserver:mDelegate
                      name:AVPlayerItemDidPlayToEndTimeNotification
                    object:mPlayerItem];
    }
    mObserversInstalled = false;
}

void VideoPlayer::unload() {
    @autoreleasepool {
        _removeObservers();

        if (mDelegate != nil) {
            [mDelegate detachOwner];
            [mDelegate release];
            mDelegate = nil;
        }
        if (mPlayer != nil) {
            [mPlayer pause];
            [mPlayer release];
            mPlayer = nil;
        }
        if (mVideoOutput != nil) {
            [mVideoOutput release];
            mVideoOutput = nil;
        }
        if (mPlayerItem != nil) {
            [mPlayerItem release];
            mPlayerItem = nil;
        }

        {
            std::lock_guard<std::mutex> lock(mFrameLock);
            if (mCurrentFrame != NULL) {
                delete mCurrentFrame;
                mCurrentFrame = NULL;
            }
            mHasFrame = false;
            _teardownZeroCopy();
        }

        mItemPrepared = false;
        mIsEOS = false;
        mWantPlay = false;
        mBuffering = false;
    }
}

void VideoPlayer::play() {
    mWantPlay = true;
    if (mPlayer != nil) {
        [mPlayer play];
    }
}

void VideoPlayer::pause() {
    mWantPlay = false;
    if (mPlayer != nil) {
        [mPlayer pause];
    }
}

void VideoPlayer::stop() {
    pause();
    if (mPlayer != nil) {
        [mPlayer seekToTime:kCMTimeZero];
    }
}

void VideoPlayer::seek(double seconds, bool precise) {
    if (mPlayer == nil) {
        return;
    }
    if (seconds < 0.0) {
        seconds = 0.0;
    }
    CMTime t = CMTimeMakeWithSeconds(seconds, NSEC_PER_SEC);
    if (precise) {
        [mPlayer seekToTime:t
            toleranceBefore:kCMTimeZero
             toleranceAfter:kCMTimeZero];
    } else {
        [mPlayer seekToTime:t];
    }
    mIsEOS = false;
}

double VideoPlayer::position() {
    if (mPlayer == nil) {
        return 0.0;
    }
    CMTime t = [mPlayer currentTime];
    if (CMTIME_IS_INDEFINITE(t) || CMTIME_IS_INVALID(t)) {
        return 0.0;
    }
    return CMTimeGetSeconds(t);
}

double VideoPlayer::duration() {
    if (mPlayerItem == nil) {
        return 0.0;
    }
    CMTime d = mPlayerItem.duration;
    if (!CMTIME_IS_INDEFINITE(d) && !CMTIME_IS_INVALID(d)) {
        return CMTimeGetSeconds(d);
    }
    // HLS streams (and a few other live / unknown-length sources)
    // report ``kCMTimeIndefinite`` for ``AVPlayerItem.duration`` per
    // Apple's documented behavior — callers that want a timeline are
    // expected to read ``seekableTimeRanges`` instead. Fall back to
    // the furthest seekable second so the seek bar still tracks.
    double maxEnd = 0.0;
    NSArray *seekable = mPlayerItem.seekableTimeRanges;
    for (NSValue *v in seekable) {
        CMTimeRange r = [v CMTimeRangeValue];
        if (!CMTIME_IS_VALID(r.start) || !CMTIME_IS_VALID(r.duration)) {
            continue;
        }
        double end = CMTimeGetSeconds(r.start) + CMTimeGetSeconds(r.duration);
        if (end > maxEnd) {
            maxEnd = end;
        }
    }
    return maxEnd;
}

void VideoPlayer::setVolume(double v) {
    if (v < 0.0) v = 0.0;
    if (v > 1.0) v = 1.0;
    mVolume = v;
    if (mPlayer != nil) {
        mPlayer.volume = (float)v;
    }
}

bool VideoPlayer::hasNewFrame() {
    if (mVideoOutput == nil || mPlayer == nil) {
        return false;
    }
    CMTime itemTime = [mPlayer currentTime];
    if (CMTIME_IS_INVALID(itemTime)) {
        return false;
    }
    if (![mVideoOutput hasNewPixelBufferForItemTime:itemTime]) {
        // Stage may still hold a previously-grabbed frame the Python
        // side hasn't consumed yet; surface that too.
        std::lock_guard<std::mutex> lock(mFrameLock);
        return mHasFrame;
    }
    CVPixelBufferRef pb = [mVideoOutput copyPixelBufferForItemTime:itemTime
                                                 itemTimeForDisplay:NULL];
    if (pb == NULL) {
        std::lock_guard<std::mutex> lock(mFrameLock);
        return mHasFrame;
    }
    _stageFrameFromBuffer(pb, CMTimeGetSeconds(itemTime));
    // _stageFrameFromBuffer takes ownership of pb (or releases it).
    return true;
}

void VideoPlayer::_stageFrameFromBuffer(CVPixelBufferRef pb, double pts) {
    if (pb == NULL) {
        return;
    }

    // The probe is lazy because the VideoPlayer can be constructed
    // before Kivy's GL context exists; by the time the first frame is
    // decoded the context is live.
    if (!mZeroCopyProbed) {
        _probeZeroCopy();
    }
    if (mZeroCopyAvailable && _bindFrameZeroCopy(pb, pts)) {
        // _bindFrameZeroCopy took ownership of pb on success.
        return;
    }

    // Zero-copy can't deliver this frame. The only situations this
    // happens in a Kivy 3.0 macOS / iOS build are:
    //   - Kivy isn't actually on the ANGLE GL backend, so
    //     eglGetCurrentDisplay() returned EGL_NO_DISPLAY.
    //   - The IOSurface client_buffer extension is missing.
    //   - eglChooseConfig / eglCreatePbufferFromClientBuffer failed.
    //   - The decoded CVPixelBuffer has no IOSurface (e.g. software
    //     decoder for an unsupported codec).
    //
    // All of these are unrecoverable for this player: every subsequent
    // frame will hit the same failure. Drop the pixel buffer, latch a
    // one-shot failure flag, log a clear diagnostic, and dispatch EOS
    // so the widget surfaces a clean failure rather than a stuck
    // black screen.
    CVPixelBufferRelease(pb);
    if (!mZeroCopyFailed.exchange(true)) {
        NSLog(@"VideoAVFoundation: zero-copy delivery failed; this "
              @"build requires the ANGLE GL backend with the "
              @"EGL_ANGLE_iosurface_client_buffer extension. "
              @"Dispatching EOS.");
        mIsEOS = true;
        if (mDelegate != nil) {
            [mDelegate performSelectorOnMainThread:@selector(playbackEnded:)
                                        withObject:nil
                                     waitUntilDone:NO];
        }
    }
}

VideoFrame *VideoPlayer::retrieveFrame() {
    std::lock_guard<std::mutex> lock(mFrameLock);
    if (!mHasFrame) {
        return NULL;
    }
    // The Python side reads the frame data into a Kivy Texture; we keep
    // ownership and reuse the VideoFrame for the next staging. Clear
    // mHasFrame so a subsequent hasNewFrame() poll won't double-deliver
    // the same frame.
    mHasFrame = false;
    return mCurrentFrame;
}


bool VideoPlayer::isEOS() {
    return mIsEOS.load();
}

bool VideoPlayer::isBuffering() {
    return mBuffering.load();
}

void VideoPlayer::_onTimeControlStatusChanged() {
    if (mPlayer == nil) {
        return;
    }
    // Apple's documented signal for "trying to play but stalled":
    //   - .paused        -> not buffering (explicit user/stop state)
    //   - .playing       -> not buffering (frames are flowing)
    //   - .waitingToPlay -> buffering (player wants to play but cannot
    //                       keep up, e.g. network underrun, initial
    //                       buffer fill, or asset not yet ready).
    // This is the same KVO key Apple recommends in "Controlling the
    // transport behavior of a player" for driving loading indicators.
    AVPlayerTimeControlStatus tcs = mPlayer.timeControlStatus;
    mBuffering =
        (tcs == AVPlayerTimeControlStatusWaitingToPlayAtSpecifiedRate);
}

void VideoPlayer::_onPlaybackEnded() {
    mIsEOS = true;
    mWantPlay = false;
    mBuffering = false;
}


/* ---------------- Thumbnails ---------------- */

VideoFrame *VideoPlayer::generateThumbnail(const char *url, double t,
                                           int w, int h) {
    if (url == NULL) {
        return NULL;
    }
    @autoreleasepool {
        NSString *s = [NSString stringWithUTF8String:url];
        NSURL *nsurl = nil;
        if ([s rangeOfString:@"://"].location == NSNotFound) {
            nsurl = [NSURL fileURLWithPath:s];
        } else {
            nsurl = [NSURL URLWithString:s];
        }
        if (nsurl == nil) {
            return NULL;
        }

        AVAsset *asset = [AVAsset assetWithURL:nsurl];
        AVAssetImageGenerator *gen =
            [[AVAssetImageGenerator alloc] initWithAsset:asset];
        gen.appliesPreferredTrackTransform = YES;
        gen.requestedTimeToleranceBefore = kCMTimeZero;
        gen.requestedTimeToleranceAfter = kCMTimeZero;
        if (w > 0 && h > 0) {
            gen.maximumSize = CGSizeMake((CGFloat)w, (CGFloat)h);
        }

        CMTime when = CMTimeMakeWithSeconds(t < 0.0 ? 0.0 : t,
                                            NSEC_PER_SEC);
        NSError *err = nil;
        CGImageRef img = [gen copyCGImageAtTime:when
                                     actualTime:NULL
                                          error:&err];
        if (img == NULL) {
            // Don't NSLog the AVFoundation error here. Failure is
            // already communicated to the caller via the NULL return
            // (which Python's Video.generate_thumbnail surfaces as
            // None), and AVAssetImageGenerator is allowed to fail
            // legitimately on assets it can't decode (HLS streams,
            // protected content, exotic codecs). Logging from native
            // code via NSLog would make those expected failures look
            // like real errors in the user's stderr.
            [gen release];
            return NULL;
        }

        size_t cgw = CGImageGetWidth(img);
        size_t cgh = CGImageGetHeight(img);
        size_t rowOut = cgw * 4;
        size_t total = rowOut * cgh;
        unsigned char *buf = (unsigned char *)malloc(total);
        if (buf == NULL) {
            CGImageRelease(img);
            [gen release];
            return NULL;
        }
        CGColorSpaceRef cs = CGColorSpaceCreateDeviceRGB();
        // Draw into a BGRA bitmap (premultiplied first byte = B for
        // little-endian platforms when using kCGBitmapByteOrder32Little).
        CGBitmapInfo bi =
            kCGBitmapByteOrder32Little |
            (CGBitmapInfo)kCGImageAlphaPremultipliedFirst;
        CGContextRef ctx = CGBitmapContextCreate(buf,
                                                 cgw, cgh,
                                                 8, rowOut, cs,
                                                 bi);
        CGColorSpaceRelease(cs);
        if (ctx == NULL) {
            free(buf);
            CGImageRelease(img);
            [gen release];
            return NULL;
        }
        CGContextDrawImage(ctx, CGRectMake(0, 0, cgw, cgh), img);
        CGContextRelease(ctx);
        CGImageRelease(img);
        [gen release];

        VideoFrame *frame = new VideoFrame();
        frame->data = (char *)buf;
        frame->datasize = (unsigned int)total;
        frame->rowsize = (unsigned int)rowOut;
        frame->width = (int)cgw;
        frame->height = (int)cgh;
        frame->pts = t;
        frame->gl_texture_id = 0;
        frame->gl_target = 0;
        return frame;
    }
}


/* =====================================================================
 * Zero-copy IOSurface -> GL_TEXTURE_2D via ANGLE.
 *
 * ANGLE is the only supported GL backend on macOS / iOS in Kivy 3.0, so
 * this path is compiled in unconditionally. Probe failure at runtime
 * (no ANGLE display, missing IOSurface extension, ...) is treated as a
 * load failure in _stageFrameFromBuffer rather than silently falling
 * back to a CPU-copy path.
 * ===================================================================== */

static bool _eglDisplayHasIOSurfaceExt(EGLDisplay display) {
    const char *exts = eglQueryString(display, EGL_EXTENSIONS);
    if (exts == NULL) {
        return false;
    }
    return strstr(exts, "EGL_ANGLE_iosurface_client_buffer") != NULL;
}

void VideoPlayer::_probeZeroCopy() {
    mZeroCopyProbed = true;
    mZeroCopyAvailable = false;

    EGLDisplay display = eglGetCurrentDisplay();
    if (display == EGL_NO_DISPLAY) {
        // Kivy isn't on the ANGLE GL backend (or the context isn't
        // current yet). Leave mZeroCopyAvailable false -- the caller
        // will surface this as a load failure in _stageFrameFromBuffer.
        NSLog(@"VideoAVFoundation: no current EGL display "
              @"(ANGLE GL backend required)");
        return;
    }
    if (!_eglDisplayHasIOSurfaceExt(display)) {
        NSLog(@"VideoAVFoundation: EGL_ANGLE_iosurface_client_buffer "
              @"extension not present");
        return;
    }

#if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
    // Resolve ANGLE's GL entry points up front (see file-level comment
    // on the GL function pointer block). Must happen before any GL
    // call in this translation unit -- the #define-shadowed names
    // below all dispatch through these pointers.
    if (!_kivyResolveANGLEGL()) {
        NSLog(@"VideoAVFoundation: failed to resolve ANGLE GL entry "
              @"points via eglGetProcAddress");
        return;
    }
#endif

    const EGLint configAttribs[] = {
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
        EGL_RED_SIZE, 8,
        EGL_GREEN_SIZE, 8,
        EGL_BLUE_SIZE, 8,
        EGL_ALPHA_SIZE, 8,
        EGL_BIND_TO_TEXTURE_RGBA, EGL_TRUE,
        EGL_NONE
    };
    EGLConfig config = NULL;
    EGLint numConfigs = 0;
    if (!eglChooseConfig(display, configAttribs, &config, 1, &numConfigs)
        || numConfigs < 1) {
        NSLog(@"VideoAVFoundation: eglChooseConfig for IOSurface failed");
        return;
    }

    // Allocate a persistent GL texture id we'll bind every frame.
    GLuint tex = 0;
    glGenTextures(1, &tex);
    if (tex == 0) {
        NSLog(@"VideoAVFoundation: glGenTextures failed "
              @"(glGetError=0x%04x eglGetError=0x%04x)",
              glGetError(), eglGetError());
        return;
    }
    glBindTexture(GL_TEXTURE_2D, tex);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);

    mEGLDisplay = (void *)display;
    mEGLConfig = (void *)config;
    mGLTexture = (unsigned int)tex;
    mZeroCopyAvailable = true;
}

bool VideoPlayer::_bindFrameZeroCopy(CVPixelBufferRef pb, double pts) {
    if (pb == NULL || mEGLDisplay == NULL || mEGLConfig == NULL ||
        mGLTexture == 0) {
        return false;
    }

    IOSurfaceRef ioSurface = CVPixelBufferGetIOSurface(pb);
    if (ioSurface == NULL) {
        // Decoded into a non-IOSurface-backed CVPixelBuffer (e.g. a
        // software decoder for an unsupported codec). Every subsequent
        // frame from this AVPlayerItem will hit the same condition, so
        // _stageFrameFromBuffer treats this as an unrecoverable
        // failure.
        return false;
    }

    size_t w = CVPixelBufferGetWidth(pb);
    size_t h = CVPixelBufferGetHeight(pb);
    if (w == 0 || h == 0) {
        return false;
    }

    EGLDisplay display = (EGLDisplay)mEGLDisplay;
    EGLConfig config = (EGLConfig)mEGLConfig;

    const EGLint surfaceAttribs[] = {
        EGL_WIDTH,                              (EGLint)w,
        EGL_HEIGHT,                             (EGLint)h,
        EGL_IOSURFACE_PLANE_ANGLE,              0,
        EGL_TEXTURE_TARGET,                     EGL_TEXTURE_2D,
        EGL_TEXTURE_INTERNAL_FORMAT_ANGLE,      GL_BGRA_EXT,
        EGL_TEXTURE_FORMAT,                     EGL_TEXTURE_RGBA,
        EGL_TEXTURE_TYPE_ANGLE,                 GL_UNSIGNED_BYTE,
        EGL_NONE,                               EGL_NONE
    };

    EGLSurface pbuffer = eglCreatePbufferFromClientBuffer(
        display, EGL_IOSURFACE_ANGLE,
        (EGLClientBuffer)ioSurface, config, surfaceAttribs);
    if (pbuffer == EGL_NO_SURFACE) {
        return false;
    }

    glBindTexture(GL_TEXTURE_2D, (GLuint)mGLTexture);
    if (!eglBindTexImage(display, pbuffer, EGL_BACK_BUFFER)) {
        eglDestroySurface(display, pbuffer);
        return false;
    }

    {
        std::lock_guard<std::mutex> lock(mFrameLock);

        // Release whatever the texture was previously bound to. The
        // renderer has already consumed the prior frame by the time we
        // got here (Clock-driven _update has a 1-frame gap between
        // stages, see _stageFrameFromBuffer call site).
        _releaseZeroCopyBinding();

        mEGLPbuffer = (void *)pbuffer;
        mBoundPixelBuffer = pb;  // takes ownership of the CFRetain
        mGLTextureWidth = (int)w;
        mGLTextureHeight = (int)h;

        if (mCurrentFrame == NULL) {
            mCurrentFrame = new VideoFrame();
        }
        if (mCurrentFrame->data != NULL) {
            free(mCurrentFrame->data);
            mCurrentFrame->data = NULL;
        }
        mCurrentFrame->datasize = 0;
        mCurrentFrame->rowsize = (unsigned int)(w * 4);
        mCurrentFrame->width = (int)w;
        mCurrentFrame->height = (int)h;
        mCurrentFrame->pts = pts;
        mCurrentFrame->gl_texture_id = mGLTexture;
        mCurrentFrame->gl_target = GL_TEXTURE_2D;
        mHasFrame = true;
    }
    return true;
}

void VideoPlayer::_releaseZeroCopyBinding() {
    // Caller must hold mFrameLock.
    if (mEGLPbuffer != NULL && mEGLDisplay != NULL) {
        EGLDisplay display = (EGLDisplay)mEGLDisplay;
        EGLSurface pbuffer = (EGLSurface)mEGLPbuffer;
        eglReleaseTexImage(display, pbuffer, EGL_BACK_BUFFER);
        eglDestroySurface(display, pbuffer);
        mEGLPbuffer = NULL;
    }
    if (mBoundPixelBuffer != NULL) {
        CVPixelBufferRelease(mBoundPixelBuffer);
        mBoundPixelBuffer = NULL;
    }
}

void VideoPlayer::_teardownZeroCopy() {
    // Caller must hold mFrameLock.
    _releaseZeroCopyBinding();
    if (mGLTexture != 0) {
        GLuint t = (GLuint)mGLTexture;
        glDeleteTextures(1, &t);
        mGLTexture = 0;
    }
    mGLTextureWidth = 0;
    mGLTextureHeight = 0;
    // Keep mZeroCopyAvailable/mEGLDisplay/mEGLConfig so a subsequent
    // load() reuses the existing probe result and re-creates a texture
    // lazily on the next frame.
    mZeroCopyProbed = false;
    mZeroCopyAvailable = false;
    mEGLDisplay = NULL;
    mEGLConfig = NULL;
}
