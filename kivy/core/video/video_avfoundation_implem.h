/*
 * Video provider implementation for macOS / iOS using AVFoundation.
 *
 * Architecture mirrors kivy/core/camera/camera_avfoundation_implem.{h,mm}:
 * an Objective-C++ wrapper around AVPlayer / AVPlayerItemVideoOutput that
 * exposes a plain C++ class to Cython.
 *
 * Pixel pipeline: zero-copy IOSurface -> ANGLE pbuffer -> GL_TEXTURE_2D.
 * The CVPixelBufferRef's IOSurface is wrapped via
 * EGL_ANGLE_iosurface_client_buffer and bound to a persistent GL texture;
 * the GL texture id is surfaced through VideoFrame::gl_texture_id and the
 * Cython layer wraps it in a Kivy Texture with nofree=True (no
 * Texture.blit_buffer per frame). This requires Kivy's ANGLE GL backend
 * (the only supported macOS / iOS backend in Kivy 3.0).
 *
 * Thumbnails (VideoPlayer::generateThumbnail) still produce CPU-copy
 * BGRA bytes from AVAssetImageGenerator + CGImage; that path is
 * one-shot and never on the per-frame hot path.
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

    // CPU-copy BGRA pixel bytes (used only by VideoPlayer::generateThumbnail;
    // playback frames leave these NULL / zero and deliver pixels via the
    // zero-copy GL texture below).
    char *data;
    unsigned int datasize;
    unsigned int rowsize;

    int width;
    int height;
    double pts;

    // Zero-copy delivery: externally-owned GL texture id whose backing
    // store is the CVPixelBuffer's IOSurface, wrapped via ANGLE's
    // EGL_ANGLE_iosurface_client_buffer. Zero for thumbnail frames.
    unsigned int gl_texture_id;
    unsigned int gl_target;       // GL_TEXTURE_2D for playback
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

    // Frame staging: latest decoded frame, protected by mFrameLock.
    std::mutex mFrameLock;
    VideoFrame *mCurrentFrame;
    bool mHasFrame;

    bool mItemPrepared;
    bool mObserversInstalled;
    // Set true once we have decided this player can't produce frames
    // (probe failed, or the first zero-copy bind didn't take). Triggers
    // a one-shot EOS dispatch so the widget surfaces a clean failure
    // instead of a stuck black screen.
    std::atomic<bool> mZeroCopyFailed;

    // Zero-copy state. EGL handles are held as void* so this header
    // doesn't pull in EGL/egl.h into Cython-generated translation units.
    bool mZeroCopyProbed;
    bool mZeroCopyAvailable;
    void *mEGLDisplay;
    void *mEGLConfig;
    void *mEGLPbuffer;
    CVPixelBufferRef mBoundPixelBuffer;
    unsigned int mGLTexture;
    int mGLTextureWidth;
    int mGLTextureHeight;

    void _applyBufferConfig();
    void _stageFrameFromBuffer(CVPixelBufferRef pb, double pts);
    void _installObservers();
    void _removeObservers();

    // Zero-copy helpers. _probeZeroCopy() runs lazily on the first
    // decoded frame so the GL context is guaranteed to be current.
    void _probeZeroCopy();
    bool _bindFrameZeroCopy(CVPixelBufferRef pb, double pts);
    void _releaseZeroCopyBinding();
    void _teardownZeroCopy();
};

#endif  /* KIVY_VIDEO_AVFOUNDATION_IMPLEM_H */
