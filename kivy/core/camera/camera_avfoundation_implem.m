/*
 * Camera base implementation for OSX / iOS
 * derivated from cap_avfoundation.mm of OpenCV
 * by Mathieu Virbel
 *
 * TODO:
 * - add interface for setting some capabilities as focus/exposure/...
 * I've let the code concerning caps, even if it's not yet used. uncomment
 * WITH_CAMERA_CAPS to compile with it.
 */

//#define WITH_CAMERA_CAPS


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


@interface CaptureDelegate : NSObject <AVCaptureVideoDataOutputSampleBufferDelegate>
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

@implementation MetadataDelegate

- (id)init {
    [super init];
    metadata = NULL;
    newMetadata = 0;
    return self;
}

- (void)captureOutput:(AVCaptureOutput *)captureOutput
didOutputMetadataObjects:(NSArray<__kindof AVMetadataObject *> *)metadataObjects
fromConnection:(AVCaptureConnection *)connection{
    for (AVMetadataObject *object in metadataObjects) {
        if ([object.type isEqualToString:AVMetadataObjectTypeQRCode]){
            AVMetadataMachineReadableCodeObject *codeObject = (AVMetadataMachineReadableCodeObject *)object;
            if (metadata == NULL)
            {
                metadata = new CameraMetadata();
            }
            NSString *stringValue = codeObject.stringValue ? codeObject.stringValue : @"Unable to decode";
            metadata->type = (char *)"AVMetadataMachineReadableCodeObject";
            metadata->data = (char *)[stringValue UTF8String];
            NSLog(@"Code: %@", stringValue);
            newMetadata = 1;
        }
    }
}

-(CameraMetadata*) getOutput {
    return metadata;
}

-(bool)haveNewMetadata {
    return newMetadata == 1;
}
-(void)setNewMetadata:(bool)status{
    newMetadata = status;
}

@end
#endif

class Camera {

public:
    Camera(int cameraNum, int width, int height);
    ~Camera();
    bool grabFrame(double timeOut);
    CameraFrame* retrieveFrame();
    CameraMetadata* retrieveMetadata();
    int startCaptureDevice();
    void stopCaptureDevice();
    bool attemptFrameRateSelection(int desiredFrameRate);
    bool attemptCapturePreset(NSString *preset);
    bool attemptStartMetadataAnalysis();
    bool haveNewMetadata();
    bool setVideoOrientation(int orientation);

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
    CaptureDelegate             *capture;
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


CameraFrame::CameraFrame(int _width, int _height) {
    data = NULL;
    rowsize = datasize = 0;
    width = _width;
    height = _height;
}

CameraFrame::~CameraFrame() {
    if (data != NULL) {
        free(data);
        data = NULL;
    }
}

CameraMetadata::CameraMetadata() {
    type = NULL;
    data = NULL;
}

CameraMetadata::~CameraMetadata() {
    if (type != NULL) {
        free(type);
        type = NULL;
    }
    if (data != NULL) {
        free(data);
        data = NULL;
    }
}

Camera::Camera(int _cameraNum, int _width, int _height) {
    mCaptureSession = nil;
    mCaptureDeviceInput = nil;
    mCaptureDecompressedVideoOutput = nil;
    capture = nil;

    width = _width;
    height = _height;
    settingWidth = 0;
    settingHeight = 0;
    cameraNum = _cameraNum;
    started = 0;

}

Camera::~Camera() {
    if(started){
        stopCaptureDevice();
    }
}

bool Camera::grabFrame(double timeOut) {
    
    NSAutoreleasePool* localpool = [[NSAutoreleasePool alloc] init];
    bool haveFrame = false;
    double sleepTime = 0.005;
    double total = 0;
    NSDate *loopUntil = [NSDate dateWithTimeIntervalSinceNow:sleepTime];
    haveFrame = [capture updateImage];
    while (!haveFrame && (total += sleepTime)<=timeOut &&
            [[NSRunLoop currentRunLoop] runMode: NSDefaultRunLoopMode
            beforeDate:loopUntil]){
        haveFrame = [capture updateImage];
        loopUntil = [NSDate dateWithTimeIntervalSinceNow:sleepTime];
    }

    [localpool drain];

    return haveFrame;
}

CameraFrame* Camera::retrieveFrame() {
    return [capture getOutput];
}

CameraMetadata* Camera::retrieveMetadata() {
    #if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
        [metadata setNewMetadata: 0];
        return [metadata getOutput];
    #else
        CameraMetadata* metadata = new CameraMetadata();
        metadata->type = (char*) "NoMetadata";
        metadata->data = (char*) "PlatformUnsupported";
        return metadata;
    #endif
}

bool Camera::haveNewMetadata() {
    #if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
        return [metadata haveNewMetadata];
    #else
        return false;
    #endif
}

void Camera::stopCaptureDevice() {
    NSAutoreleasePool* localpool = [[NSAutoreleasePool alloc] init];
    started = 0;

    [mCaptureSession stopRunning];

    [mCaptureSession release];
    [mCaptureDeviceInput release];

    [mCaptureDecompressedVideoOutput release];
    [capture release];
    [localpool drain];
}

bool Camera::attemptFrameRateSelection(int desiredFrameRate){
    bool isFPSSupported = NO;
    AVCaptureDeviceFormat *currentFormat = [mCaptureDevice activeFormat];
    for ( AVFrameRateRange *range in currentFormat.videoSupportedFrameRateRanges ) {
        if ( range.maxFrameRate >= desiredFrameRate && range.minFrameRate <= desiredFrameRate )        {
            isFPSSupported = YES;
            break;
        }
    }

    if( isFPSSupported ) {
        if ( [mCaptureDevice lockForConfiguration:NULL] ) {
            mCaptureDevice.activeVideoMaxFrameDuration = CMTimeMake( 1, desiredFrameRate );
            mCaptureDevice.activeVideoMinFrameDuration = CMTimeMake( 1, desiredFrameRate );
            [mCaptureDevice unlockForConfiguration];
        }
    } else {
        NSLog(@"Selected FPS (%d) not available on this platform.", desiredFrameRate);
    }
    return isFPSSupported;
}

bool Camera::attemptCapturePreset(NSString *preset){
    // See available presets: https://developer.apple.com/documentation/avfoundation/avcapturesessionpreset
    if([mCaptureSession canSetSessionPreset: preset]){
        [mCaptureSession setSessionPreset: preset];
        return true;
    }
    NSLog(@"Selected preset (%@) not available on this platform", preset);
    return false;
}

bool Camera::attemptStartMetadataAnalysis(){
    #if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
        /* AVCaptureMetadataOutput is not available on MacOS */
        [mCaptureSession addOutput:mMetadataOutput];
        [mMetadataOutput setMetadataObjectsDelegate:metadata
                             queue:dispatch_get_main_queue()];
        [mMetadataOutput setMetadataObjectTypes: @[AVMetadataObjectTypeQRCode]];
        return true;
    #else
        NSLog(@"Metadata Analysis not available on this platform.");
        return false;
    #endif
}

int Camera::startCaptureDevice() {
    NSError* error;
    NSArray *devices;
    AVCaptureDevice *device;
    NSAutoreleasePool* localpool = [[NSAutoreleasePool alloc] init];

    if (started == 1)
        return 1;

    capture = [[CaptureDelegate alloc] init];

    devices = [AVCaptureDevice devicesWithMediaType:AVMediaTypeVideo];

    if ([devices count] == 0) {
        NSLog(@"AV Foundation didn't find any attached Video Input Devices!\n");
        [localpool drain];
        return 0;
    }

    if (cameraNum >= 0) {
        int camNum = cameraNum % [devices count];
        if (camNum != cameraNum) {
            NSLog(@"Warning: Max Camera Num is %lu; Using camera %d\n",
                  (unsigned long)([devices count] - 1), camNum);
        }
        device = [devices objectAtIndex:camNum];
    } else {
        device = [AVCaptureDevice defaultDeviceWithMediaType:AVMediaTypeVideo]  ;
    }

    mCaptureDevice = device;

    if (device) {

        mCaptureDeviceInput = [[AVCaptureDeviceInput alloc] initWithDevice:device error:&error] ;
        mCaptureSession = [[AVCaptureSession alloc] init] ;

        #if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
        /* AVCaptureMetadataOutput is not available on MacOS */
        metadata = [[MetadataDelegate alloc] init];
        mMetadataOutput = [[AVCaptureMetadataOutput alloc] init];
        #endif

        mCaptureDecompressedVideoOutput = [[AVCaptureVideoDataOutput alloc] init];

        dispatch_queue_t queue = dispatch_queue_create("cameraQueue", NULL);
        [mCaptureDecompressedVideoOutput setSampleBufferDelegate:capture queue:queue];
        dispatch_release(queue);

        NSDictionary *pixelBufferOptions ;
        if (width > 0 && height > 0) {
            pixelBufferOptions = [NSDictionary dictionaryWithObjectsAndKeys:
                #if TARGET_OS_OSX
                // On MacOS, we have the chance to resize the image to the height + width the user provided.
                [NSNumber numberWithDouble:1.0*width], (id)kCVPixelBufferWidthKey,
                [NSNumber numberWithDouble:1.0*height], (id)kCVPixelBufferHeightKey,
                #endif
                [NSNumber numberWithUnsignedInt:kCVPixelFormatType_32BGRA],
                (id)kCVPixelBufferPixelFormatTypeKey,
                nil];
        } else {
            pixelBufferOptions = [NSDictionary dictionaryWithObjectsAndKeys:
                [NSNumber numberWithUnsignedInt:kCVPixelFormatType_32BGRA],
                (id)kCVPixelBufferPixelFormatTypeKey,
                nil];
        }
        [mCaptureDecompressedVideoOutput setVideoSettings:pixelBufferOptions];
        mCaptureDecompressedVideoOutput.alwaysDiscardsLateVideoFrames = YES;

        // Attempt to set framerate to 30 FPS
        attemptFrameRateSelection(30);

        /* By default, We're using the AVCaptureSessionPresetHigh preset for capturing frames on both iOS and MacOS.
           The user can override these settings by calling the attemptCapturePreset() function
        */
        attemptCapturePreset(@"AVCaptureSessionPresetHigh");

        [mCaptureSession addInput:mCaptureDeviceInput];
        [mCaptureSession addOutput:mCaptureDecompressedVideoOutput];

        AVCaptureConnection *conn = [mCaptureDecompressedVideoOutput connectionWithMediaType:AVMediaTypeVideo];

#if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
        /* By default, on iOS, We select the correct AVCaptureVideoOrientation based on device orientation */
        AVCaptureVideoOrientation default_orientation = (AVCaptureVideoOrientation)[[UIDevice currentDevice] orientation];
#else
        AVCaptureVideoOrientation default_orientation = AVCaptureVideoOrientationLandscapeRight;
#endif
        [conn setVideoOrientation:default_orientation];

        dispatch_async(dispatch_get_main_queue(), ^{
            [mCaptureSession startRunning];
        });
        [localpool drain];

        started = 1;
        return 1;
    }

    [localpool drain];
    return 0;
}

bool Camera::setVideoOrientation(int orientation) {
    AVCaptureConnection *conn = [mCaptureDecompressedVideoOutput connectionWithMediaType:AVMediaTypeVideo];
    if([conn isVideoOrientationSupported]){
        [conn setVideoOrientation:(AVCaptureVideoOrientation) orientation];
    }
}

#ifdef WITH_CAMERA_CAPS
void Camera::setWidthHeight() {
    NSAutoreleasePool* localpool = [[NSAutoreleasePool alloc] init];
    NSDictionary* pixelBufferOptions = [NSDictionary dictionaryWithObjectsAndKeys:
        [NSNumber numberWithDouble:1.0*width], (id)kCVPixelBufferWidthKey,
        [NSNumber numberWithDouble:1.0*height], (id)kCVPixelBufferHeightKey,
        [NSNumber numberWithUnsignedInt:kCVPixelFormatType_32BGRA],
        (id)kCVPixelBufferPixelFormatTypeKey,
        nil];

    [mCaptureDecompressedVideoOutput setVideoSettings:pixelBufferOptions];
    grabFrame(60);
    [localpool drain];
}

double Camera::getProperty(int property_id) {
    NSAutoreleasePool* localpool = [[NSAutoreleasePool alloc] init];

    NSArray* ports = mCaptureDeviceInput.ports;
    CMFormatDescriptionRef format = [[ports objectAtIndex:0] formatDescription];
    CGSize s1 = CMVideoFormatDescriptionGetPresentationDimensions(format, YES, YES);

    int width = (int)s1.width;
    int height = (int)s1.height;

    [localpool drain];

    switch (property_id) {
        case CAM_FRAME_WIDTH:
            return width;
        case CAM_FRAME_HEIGHT:
            return height;
        case CAM_IOS_DEVICE_FOCUS:
            return mCaptureDevice.focusMode;
        case CAM_IOS_DEVICE_EXPOSURE:
            return mCaptureDevice.exposureMode;
        case CAM_IOS_DEVICE_FLASH:
            return mCaptureDevice.flashMode;
        case CAM_IOS_DEVICE_WHITEBALANCE:
            return mCaptureDevice.whiteBalanceMode;
        case CAM_IOS_DEVICE_TORCH:
            return mCaptureDevice.torchMode;
        default:
            return 0;
    }


}

bool Camera::setProperty(int property_id, double value) {
    switch (property_id) {
        case CAM_FRAME_WIDTH:
            width = value;
            settingWidth = 1;
            if (settingWidth && settingHeight) {
                setWidthHeight();
                settingWidth =0;
                settingHeight = 0;
            }
            return true;

        case CAM_FRAME_HEIGHT:
            height = value;
            settingHeight = 1;
            if (settingWidth && settingHeight) {
                setWidthHeight();
                settingWidth =0;
                settingHeight = 0;
            }
            return true;

        case CAM_IOS_DEVICE_FOCUS:
            if ([mCaptureDevice isFocusModeSupported:(int)value]) {
                NSError* error = nil;
                [mCaptureDevice lockForConfiguration:&error];
                if (error) return false;
                [mCaptureDevice setFocusMode:(int)value];
                [mCaptureDevice unlockForConfiguration];
                return true;
            } else {
                return false;
            }

        case CAM_IOS_DEVICE_EXPOSURE:
            if ([mCaptureDevice isExposureModeSupported:(int)value]) {
                NSError* error = nil;
                [mCaptureDevice lockForConfiguration:&error];
                if (error) return false;
                [mCaptureDevice setExposureMode:(int)value];
                [mCaptureDevice unlockForConfiguration];
                return true;
            } else {
                return false;
            }

        case CAM_IOS_DEVICE_FLASH:
            if ( [mCaptureDevice hasFlash] && [mCaptureDevice isFlashModeSupported:(int)value]) {
                NSError* error = nil;
                [mCaptureDevice lockForConfiguration:&error];
                if (error) return false;
                [mCaptureDevice setFlashMode:(int)value];
                [mCaptureDevice unlockForConfiguration];
                return true;
            } else {
                return false;
            }

        case CAM_IOS_DEVICE_WHITEBALANCE:
            if ([mCaptureDevice isWhiteBalanceModeSupported:(int)value]) {
                NSError* error = nil;
                [mCaptureDevice lockForConfiguration:&error];
                if (error) return false;
                [mCaptureDevice setWhiteBalanceMode:(int)value];
                [mCaptureDevice unlockForConfiguration];
                return true;
            } else {
                return false;
            }

        case CAM_IOS_DEVICE_TORCH:
            if ([mCaptureDevice hasFlash] && [mCaptureDevice isTorchModeSupported:(int)value]) {
                NSError* error = nil;
                [mCaptureDevice lockForConfiguration:&error];
                if (error) return false;
                [mCaptureDevice setTorchMode:(int)value];
                [mCaptureDevice unlockForConfiguration];
                return true;
            } else {
                return false;
            }

        default:
            return false;
    }
}
#endif

@implementation CaptureDelegate

- (id)init {
    [super init];
    newFrame = 0;
    image = NULL;
    return self;
}


-(void)dealloc {
    delete image;
    [super dealloc];
}

- (void)captureOutput:(AVCaptureOutput *)captureOutput
didOutputSampleBuffer:(CMSampleBufferRef)sampleBuffer
fromConnection:(AVCaptureConnection *)connection{

    // Failed
    // connection.videoOrientation = AVCaptureVideoOrientationPortrait;

    CVImageBufferRef imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer);

    CVBufferRetain(imageBuffer);
    CVImageBufferRef imageBufferToRelease  = mCurrentImageBuffer;

    @synchronized (self) {

        mCurrentImageBuffer = imageBuffer;
        newFrame = 1;
    }

    CVBufferRelease(imageBufferToRelease);

}


-(CameraFrame*) getOutput {
    return image;
}

-(int) updateImage {
    CVPixelBufferRef pixels;

    if (newFrame == 0)
        return 0;

    @synchronized (self) {
        pixels = CVBufferRetain(mCurrentImageBuffer);
        newFrame = 0;
    }

    CVPixelBufferLockBaseAddress(pixels, 0);
    uint32_t* baseaddress = (uint32_t*)CVPixelBufferGetBaseAddress(pixels);

    size_t width = CVPixelBufferGetWidth(pixels);
    size_t height = CVPixelBufferGetHeight(pixels);
    size_t rowsize = CVPixelBufferGetBytesPerRow(pixels);

    /*
    NSLog(@"updateImage() ! width=%lu height=%lu rowsize=%lu\n",
            width, height, rowsize);
    */

    if (rowsize != 0) {

        if (image == NULL)
            image = new CameraFrame((int)width, (int)height);

        image->width = width;
        image->height = height;
        image->rowsize = (unsigned int)rowsize;

        if (image->datasize != width * height * sizeof(char) * 4) {
            image->datasize = (unsigned int)(width * height * sizeof(char) * 4);
            if (image->data != NULL)
                free(image->data);
            image->data = (char *)malloc(image->datasize);
        }

        if (image->rowsize == width * 4)
            memcpy(image->data, baseaddress, image->datasize);
        else {
            char *dstbuffer = image->data;
            char *srcbuffer = (char *)baseaddress;
            unsigned long width4 = width * 4;
            for (int y = 0; y < height; y++) {
                memcpy(dstbuffer, srcbuffer, rowsize);
                dstbuffer += width4;
                srcbuffer += rowsize;
            }
        }
    }

    CVPixelBufferUnlockBaseAddress(pixels, 0);
    CVBufferRelease(pixels);

    return 1;
}

@end


//
// C-like API for easier interaction with Cython
//

#include "camera_avfoundation_implem.h"

camera_t avf_camera_init(int index, int width, int height) {
    return new Camera(index, width, height);
}

void avf_camera_start(camera_t camera) {
    ((Camera *)camera)->startCaptureDevice();
}

void avf_camera_stop(camera_t camera) {
    ((Camera *)camera)->stopCaptureDevice();
}

void avf_camera_deinit(camera_t camera) {
    delete (Camera *)(camera);
}

bool avf_camera_update(camera_t camera) {
    return ((Camera *)camera)->grabFrame(0);
}

void avf_camera_get_image(camera_t camera, int *width, int *height, int *rowsize, char **data) {
    CameraFrame *frame = ((Camera *)camera)->retrieveFrame();
    *width = *height = *rowsize = 0;
    *data = nil;
    if (frame == nil)
        return;
    *width = frame->width;
    *height = frame->height;
    *rowsize = frame->rowsize;
    *data = frame->data;
}

bool avf_camera_attempt_framerate_selection(camera_t camera, int fps){
    return ((Camera *)camera)->attemptFrameRateSelection(fps);
}

bool avf_camera_attempt_capture_preset(camera_t camera, char *preset){
    NSString *capture_preset = [NSString stringWithUTF8String:preset];
    NSLog(@"Preset: %@", capture_preset);
    return ((Camera *)camera)->attemptCapturePreset(capture_preset);
}

bool avf_camera_attempt_start_metadata_analysis(camera_t camera){
    return ((Camera *)camera)->attemptStartMetadataAnalysis();
}

void avf_camera_get_metadata(camera_t camera, char **metatype, char **data) {
    CameraMetadata *metadata = ((Camera *)camera)->retrieveMetadata();
    *metatype = metadata->type;
    *data = metadata->data;
}

bool avf_camera_have_new_metadata(camera_t camera){
    return ((Camera *)camera)->haveNewMetadata();
}

bool avf_camera_set_video_orientation(camera_t camera, int orientation){
    return ((Camera *)camera)->setVideoOrientation(orientation);
}

