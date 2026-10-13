#import <AVFoundation/AVFoundation.h>
#import <Foundation/NSException.h>

#if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
#import <UIKit/UIKit.h>
#endif


#ifdef WITH_CAMERA_CAPS
typedef enum {
    CAM_FRAME_WIDTH,
    CAM_FRAME_HEIGHT,
    CAM_IOS_DEVICE_FOCUS,
    CAM_IOS_DEVICE_EXPOSURE,
    CAM_IOS_DEVICE_FLASH,
    CAM_IOS_DEVICE_WHITEBALANCE,
    CAM_IOS_DEVICE_TORCH
} caps_t;
#endif

class CameraFrame {
public:
    CameraFrame(int width, int height);
    ~CameraFrame();
    char *data;
    unsigned int datasize;
    unsigned int rowsize;
    int width;
    int height;
};

class CameraMetadata {
public:
    CameraMetadata();
    ~CameraMetadata();
    char *type;
    char *data;
};

@interface KivyCaptureDelegate : NSObject <AVCaptureVideoDataOutputSampleBufferDelegate>
{
    int newFrame;
    CVImageBufferRef  mCurrentImageBuffer;
    CameraFrame* image;
}

- (void)captureOutput:(AVCaptureOutput *)captureOutput
  didOutputSampleBuffer:(CMSampleBufferRef)sampleBuffer
  fromConnection:(AVCaptureConnection *)connection;


- (int)updateImage;
- (CameraFrame*)getOutput;

@end

#if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR

@interface PhotoAppDelegate : NSObject {}
- (void) thisImage:(UIImage *)image photoAppCallback:(NSError *)error usingContextInfo:(void*)ctxInfo;
@end

@implementation PhotoAppDelegate
- (void) thisImage:(UIImage *)image photoAppCallback:(NSError *)error usingContextInfo:(void*)ctxInfo {
    free(ctxInfo);
}
@end

/* AVCaptureMetadataOutput is not available on MacOS */
@interface MetadataDelegate : NSObject <AVCaptureMetadataOutputObjectsDelegate>
{
    CameraMetadata* metadata;
    int newMetadata;
}
- (void)captureOutput:(AVCaptureOutput *)output
didOutputMetadataObjects:(NSArray<__kindof AVMetadataObject *> *)metadataObjects
       fromConnection:(AVCaptureConnection *)connection;
- (CameraMetadata*)getOutput;
- (bool)haveNewMetadata;
- (void)setNewMetadata:(bool)newMetadata;
@end
#endif

class Camera {

public:
    Camera(int cameraNum, int width, int height);
    ~Camera();
    static int getDeviceOrientation();
    static char* getDocumentsDirectory();
    bool grabFrame(double timeOut);
    CameraFrame* retrieveFrame();
    CameraMetadata* retrieveMetadata();
    int startCaptureDevice();
    void stopCaptureDevice();
    bool attemptFrameRateSelection(int desiredFrameRate);
    bool attemptCapturePreset(char* preset);
    bool attemptStartMetadataAnalysis();
    bool haveNewMetadata();
    void setVideoOrientation(int orientation);
    void changeCameraInput(int _cameraNum);
    void zoomLevel(float zoomLevel);
    void savePixelsToFile(unsigned char *pixels, int width, int height, char *path, float quality);
#if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
    PhotoAppDelegate             *photoapp;
#endif
#ifdef WITH_CAMERA_CAPS
    double getProperty(int property_id);
    bool setProperty(int property_id, double value);
    void setWidthHeight();
#endif

private:
    AVCaptureSession            *mCaptureSession;
    AVCaptureDeviceInput        *mCaptureDeviceInput;
    AVCaptureVideoDataOutput    *mCaptureDecompressedVideoOutput;
    AVCaptureDevice             *mCaptureDevice;
    KivyCaptureDelegate             *capture;
    #if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
    /* AVCaptureMetadataOutput is not available on MacOS */
    AVCaptureMetadataOutput     *mMetadataOutput;
    MetadataDelegate            *metadata;
    #endif

    int cameraNum;
    int width;
    int height;
    int settingWidth;
    int settingHeight;
    int started;
};