/*
 * Camera base implementation for OSX / iOS
 * derivated from cap_avfoundation.mm of OpenCV
 * by Mathieu Virbel
 *
 * TODO:
 * - enable the provider for iOS, and test it!
 * - add interface for setting some capabilities as focus/exposure/...
 *
 * I've let the code concerning caps, even if it's not yet used. uncomment
 * WITH_CAMERA_CAPS to compile with it.
 */

//#define WITH_CAMERA_CAPS

#import <AVFoundation/AVFoundation.h>
#import <Foundation/NSException.h>

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


class Camera {

public:
    Camera(int cameraNum, int width, int height);
    ~Camera();
    bool grabFrame(double timeOut);
    CameraFrame* retrieveFrame();
    int startCaptureDevice();
    void stopCaptureDevice();

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
    stopCaptureDevice();
}

bool Camera::grabFrame(double timeOut) {

    NSAutoreleasePool* localpool = [[NSAutoreleasePool alloc] init];
    double sleepTime = 0.005;
    double total = 0;
    NSDate *loopUntil = [NSDate dateWithTimeIntervalSinceNow:sleepTime];
    [capture updateImage];
    while (![capture updateImage] && (total += sleepTime)<=timeOut &&
            [[NSRunLoop currentRunLoop] runMode: NSDefaultRunLoopMode
            beforeDate:loopUntil])
        loopUntil = [NSDate dateWithTimeIntervalSinceNow:sleepTime];

    [localpool drain];

    return total <= timeOut;
}

CameraFrame* Camera::retrieveFrame() {
    return [capture getOutput];
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

        mCaptureDecompressedVideoOutput = [[AVCaptureVideoDataOutput alloc] init];

        dispatch_queue_t queue = dispatch_queue_create("cameraQueue", NULL);
        [mCaptureDecompressedVideoOutput setSampleBufferDelegate:capture queue:queue];
        dispatch_release(queue);


        NSDictionary *pixelBufferOptions ;
        if (width > 0 && height > 0) {
            pixelBufferOptions = [NSDictionary dictionaryWithObjectsAndKeys:
                [NSNumber numberWithDouble:1.0*width], (id)kCVPixelBufferWidthKey,
                [NSNumber numberWithDouble:1.0*height], (id)kCVPixelBufferHeightKey,
                [NSNumber numberWithUnsignedInt:kCVPixelFormatType_32BGRA],
                (id)kCVPixelBufferPixelFormatTypeKey,
                nil];
        } else {
            pixelBufferOptions = [NSDictionary dictionaryWithObjectsAndKeys:
                [NSNumber numberWithUnsignedInt:kCVPixelFormatType_32BGRA],
                (id)kCVPixelBufferPixelFormatTypeKey,
                nil];
        }

        //TODO: add new interface for setting fps and capturing resolution.
        [mCaptureDecompressedVideoOutput setVideoSettings:pixelBufferOptions];
        mCaptureDecompressedVideoOutput.alwaysDiscardsLateVideoFrames = YES;

#if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
        mCaptureDecompressedVideoOutput.minFrameDuration = CMTimeMake(1, 30);
#endif

        //Slow. 1280*720 for iPhone4, iPod back camera. 640*480 for front camera
        //mCaptureSession.sessionPreset = AVCaptureSessionPresetHigh; // fps ~= 5 slow for OpenCV

        mCaptureSession.sessionPreset = AVCaptureSessionPresetMedium; //480*360
        if (width == 0) width = 480;
        if (height == 0) height = 360;

        [mCaptureSession addInput:mCaptureDeviceInput];
        [mCaptureSession addOutput:mCaptureDecompressedVideoOutput];
        [mCaptureSession startRunning];
        [localpool drain];

        started = 1;
        return 1;
    }

    [localpool drain];
    return 0;
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

    //NSLog(@"updateImage() ! width=%lu height=%lu rowsize=%lu\n",
    //        width, height, rowsize);

    if (rowsize != 0) {

        if (image == NULL)
            image = new CameraFrame((int)width, (int)height);

        if (image->datasize != width * height * sizeof(char) * 4) {
            image->datasize = (unsigned int)(width * height * sizeof(char) * 4);
            if (image->data != NULL)
                free(image->data);
            image->data = (char *)malloc(image->datasize);
            image->rowsize = (unsigned int)rowsize;
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

void avf_camera_update(camera_t camera) {
    ((Camera *)camera)->grabFrame(0);
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

