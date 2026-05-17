/*
 * Video provider implementation for macOS / iOS using AVFoundation.
 *
 * Architecture mirrors kivy/core/camera/camera_avfoundation_implem.{h,mm}:
 * an Objective-C++ wrapper around AVPlayer / AVPlayerItemVideoOutput that
 * exposes a plain C++ class to Cython.
 *
 * Phase 1 (CPU copy): pixel buffers are memcpy'd into VideoFrame::data and
 * blit_buffer'd into a Kivy Texture on the Python side.
 *
 * Phase 2 (zero-copy, ANGLE/Metal backend only): the CVPixelBufferRef's
 * IOSurface is wrapped via EGL_ANGLE_iosurface_client_buffer and bound to
 * a GL texture; the GL texture id is surfaced through
 * VideoFrame::gl_texture_id and the Cython layer skips blit_buffer.
 */

#ifndef KIVY_VIDEO_AVFOUNDATION_IMPLEM_H
#define KIVY_VIDEO_AVFOUNDATION_IMPLEM_H

#import <AVFoundation/AVFoundation.h>
#import <CoreMedia/CoreMedia.h>
#import <CoreVideo/CoreVideo.h>

#if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
#import <UIKit/UIKit.h>
#endif

#include <atomic>
#include <mutex>

class VideoFrame {
public:
    VideoFrame();
    ~VideoFrame();

    // CPU-copy path: BGRA pixel bytes (NULL when zero-copy is used).
    char *data;
    unsigned int datasize;
    unsigned int rowsize;

    int width;
    int height;
    double pts;

    // Zero-copy path: externally-owned GL texture id (0 when CPU-copy).
    unsigned int gl_texture_id;
    unsigned int gl_target;       // GL_TEXTURE_2D when zero-copy
};

class VideoPlayer;

@interface KivyAVDelegate : NSObject {
    VideoPlayer *mOwner;
}
- (id)initWithOwner:(VideoPlayer *)owner;
- (void)observeValueForKeyPath:(NSString *)keyPath
                      ofObject:(id)object
                        change:(NSDictionary<NSKeyValueChangeKey, id> *)change
                       context:(void *)context;
- (void)playbackEnded:(NSNotification *)notification;
- (void)detachOwner;
@end

class VideoPlayer {
public:
    VideoPlayer(const char *url);
    ~VideoPlayer();

    void load();
    void play();
    void pause();
    void stop();
    void unload();
    void seek(double seconds, bool precise);

    double position();
    double duration();
    void setVolume(double v);

    bool hasNewFrame();
    VideoFrame *retrieveFrame();

    bool isEOS();

    // True while playback is delayed/stalled while trying to satisfy
    // [player play] -- driven directly by AVPlayer.timeControlStatus ==
    // .waitingToPlayAtSpecifiedRate.
    bool isBuffering();

    // Forwarded from VideoBase.options. Both must be set before load()
    // to take effect at AVPlayer / AVPlayerItem construction time.
    //
    // ``setAutomaticallyWaitsToMinimizeStalling(false)`` translates to
    // the AVPlayer property of the same name -- when false, AVPlayer
    // starts playback as soon as the first decodable frame is available
    // rather than buffering ahead. The default (true) matches AVPlayer's
    // own default and favors uninterrupted playback at the cost of
    // start-up latency.
    void setAutomaticallyWaitsToMinimizeStalling(bool wait);
    void setForceCPUCopy(bool forced);

    // Thumbnails: produces a CPU-copy VideoFrame; caller owns it and must
    // delete it. Returns NULL on error.
    static VideoFrame *generateThumbnail(const char *url, double t,
                                         int w, int h);

    // Called by KivyAVDelegate from KVO / notification callbacks.
    void _onTimeControlStatusChanged();
    void _onPlaybackEnded();

private:
    NSString *mUrl;
    AVPlayer *mPlayer;
    AVPlayerItem *mPlayerItem;
    AVPlayerItemVideoOutput *mVideoOutput;
    KivyAVDelegate *mDelegate;

    double mVolume;
    std::atomic<bool> mWantPlay;
    std::atomic<bool> mIsEOS;
    std::atomic<bool> mBuffering;

    bool mAutomaticallyWaitsToMinimizeStalling;
    bool mForceCPUCopy;

    // Frame staging: latest decoded frame, protected by mFrameLock.
    std::mutex mFrameLock;
    VideoFrame *mCurrentFrame;
    bool mHasFrame;
    // Previously-delivered pixel buffer kept alive one frame so any GL
    // read against its IOSurface (zero-copy path) is safe to complete.
    CVPixelBufferRef mPreviousPixelBuffer;

    bool mItemPrepared;
    bool mObserversInstalled;

    // Phase 2: zero-copy state. mEGLDisplay / mEGLConfig / mEGLPbuffer
    // are held as void* so this header doesn't pull in EGL/egl.h (which
    // is only available when ANGLE is configured at build time). The
    // members beyond the probe flags are only referenced when
    // KIVY_VIDEO_AVF_HAS_ANGLE is defined; gating their declarations
    // suppresses unused-private-field warnings on stub builds.
    bool mZeroCopyProbed;
    bool mZeroCopyAvailable;
    // One-shot flag so the "using CPU-copy path" diagnostic only fires
    // on the first frame, not on every decoded frame.
    bool mCPUCopyLogged;
#ifdef KIVY_VIDEO_AVF_HAS_ANGLE
    void *mEGLDisplay;
    void *mEGLConfig;
    void *mEGLPbuffer;
    CVPixelBufferRef mBoundPixelBuffer;
    unsigned int mGLTexture;
    int mGLTextureWidth;
    int mGLTextureHeight;
#endif

    void _applyBufferConfig();
    void _stageFrameFromBuffer(CVPixelBufferRef pb, double pts);
    void _releasePreviousPixelBuffer();
    void _installObservers();
    void _removeObservers();

    // Phase 2 helpers. _probeZeroCopy() is a no-op (returning false)
    // when the implementation is built without ANGLE support.
    void _probeZeroCopy();
    bool _bindFrameZeroCopy(CVPixelBufferRef pb, double pts);
    void _releaseZeroCopyBinding();
    void _teardownZeroCopy();
};

#endif  /* KIVY_VIDEO_AVFOUNDATION_IMPLEM_H */
