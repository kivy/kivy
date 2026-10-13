/*
 * Camera base implementation for OSX / iOS
 * derivated from cap_avfoundation.mm of OpenCV
 * by Mathieu Virbel
 *
 * TODO:
 * - add iOS native photo and video capture
 * - add support for telephoto and wide angle lenses
 *     needs iOS10 AVCaptureDeviceDiscoverySession   discoverySessionWithDeviceTypes:mediaType:position: 
 * I've let the code concerning caps, even if it's not yet used. uncomment
 * WITH_CAMERA_CAPS to compile with it.
 */

//#define WITH_CAMERA_CAPS

#include "camera_avfoundation_implem.h"


#if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
@implementation MetadataDelegate

- (id)init {
    [super init];
    metadata = new CameraMetadata();
    newMetadata = 0;
    return self;
}

- (void)captureOutput:(AVCaptureOutput *)captureOutput
didOutputMetadataObjects:(NSArray<__kindof AVMetadataObject *> *)metadataObjects
fromConnection:(AVCaptureConnection *)connection{
    for (AVMetadataObject *metadataResult in metadataObjects) {
        if ([metadataResult.type isEqualToString:AVMetadataObjectTypeQRCode]){
            AVMetadataMachineReadableCodeObject *codeObject = (AVMetadataMachineReadableCodeObject *)metadataResult;
            NSString *stringValue = codeObject.stringValue ? codeObject.stringValue : @"Unable to decode";
            NSLog(@"Code: %@", stringValue);

            if (metadata->type != NULL){
                free(metadata->type);
            }
            if (metadata->data != NULL){
                free(metadata->data);
            }
            metadata->type = (char *)malloc(sizeof(char) * (strlen([metadataResult.type UTF8String]) + 1));
            metadata->data = (char *)malloc(sizeof(char) * (strlen([stringValue UTF8String]) + 1));

            strcpy(metadata->type, [metadataResult.type UTF8String]);
            strcpy(metadata->data, [stringValue UTF8String]);

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

int Camera::getDeviceOrientation() {
    #if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
        return (int)[[UIDevice currentDevice] orientation];
    #else
        return 0;
    #endif
}

char* Camera::getDocumentsDirectory() {
    #if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
        NSArray *paths = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES);
        NSString *basePath = paths.firstObject;
        return (char *)[basePath UTF8String];
    #else
        return "";
    #endif
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

bool Camera::attemptCapturePreset(char* preset){
    NSString *capture_preset = [NSString stringWithUTF8String:preset];
    NSLog(@"Preset: %@", capture_preset);
    // See available presets: https://developer.apple.com/documentation/avfoundation/avcapturesessionpreset
    if([mCaptureSession canSetSessionPreset: capture_preset]){
        [mCaptureSession setSessionPreset: capture_preset];
        return true;
    }
    NSLog(@"Selected preset (%@) not available on this platform", capture_preset);
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

    capture = [[KivyCaptureDelegate alloc] init];

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
        photoapp = [[PhotoAppDelegate alloc] init];
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
        attemptCapturePreset("AVCaptureSessionPresetHigh");

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

void Camera::setVideoOrientation(int orientation) {
    AVCaptureConnection *conn = [mCaptureDecompressedVideoOutput connectionWithMediaType:AVMediaTypeVideo];
    if([conn isVideoOrientationSupported]){
        [conn setVideoOrientation:(AVCaptureVideoOrientation) orientation];
    }
}

void Camera::changeCameraInput(int _cameraNum) {
    #if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
    NSError* error;
    NSArray *devices;
    AVCaptureDevice *device;

    devices = [AVCaptureDevice devicesWithMediaType:AVMediaTypeVideo];

    if (_cameraNum >= 0) {
        int camNum = _cameraNum % [devices count];
        if (camNum != _cameraNum) {
            NSLog(@"Warning: Max Camera Num is %lu; Using camera %d\n",
                  (unsigned long)([devices count] - 1), camNum);
        }
        device = [devices objectAtIndex:camNum];
        cameraNum = _cameraNum;
    } else {
        device = [AVCaptureDevice defaultDeviceWithMediaType:AVMediaTypeVideo]  ;
        cameraNum = 0;
    }

    if (device) {
        [mCaptureSession beginConfiguration];
        [mCaptureSession removeInput:mCaptureDeviceInput];
        mCaptureDeviceInput = [[AVCaptureDeviceInput alloc] initWithDevice:device error:&error];
        [mCaptureSession addInput:mCaptureDeviceInput];
        [mCaptureSession commitConfiguration];
        setVideoOrientation([[UIDevice currentDevice] orientation]);
    }
    #endif
}

void Camera::zoomLevel(float zoomLevel) {
    #if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
    // iOS 7.x+ with compatible hardware
    if ([mCaptureDevice respondsToSelector:@selector(setVideoZoomFactor:)]
        && mCaptureDevice.activeFormat.videoMaxZoomFactor >= zoomLevel) {
       if ([mCaptureDevice lockForConfiguration:nil]) {
           [mCaptureDevice setVideoZoomFactor:zoomLevel];
           [mCaptureDevice unlockForConfiguration];
       }
   }
   #endif
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

void Camera::savePixelsToFile(unsigned char *pixels, int width, int height, char *path, float quality) {
    #if TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR
        int size = width * height * 4;
        if (strcmp(path,"") == 0) {
            unsigned char *local_pixels = pixels;
            pixels = (unsigned char *)malloc(size);
            memcpy(pixels, local_pixels, size*sizeof(char));
        }
        CGDataProviderRef provider = CGDataProviderCreateWithData(NULL, pixels, size, NULL);
        int bitsPerComponent = 8;
        int bitsPerPixel = 32;
        int bytesPerRow = 4*width;
        CGColorSpaceRef colorSpaceRef = CGColorSpaceCreateDeviceRGB();
        CGBitmapInfo bitmapInfo = kCGBitmapByteOrder32Big|kCGImageAlphaLast;
        CGColorRenderingIntent renderingIntent = kCGRenderingIntentDefault;
        CGImageRef imageRef = CGImageCreate(width,
                                            height,
                                            8,
                                            32,
                                            4*width,colorSpaceRef,
                                            bitmapInfo,
                                            provider,NULL,NO,renderingIntent);
        UIImage *newImage = [UIImage imageWithCGImage:imageRef];

        if (strcmp(path,"") == 0) {

            UIImageWriteToSavedPhotosAlbum(newImage, this->photoapp,
                                        @selector(thisImage:photoAppCallback:usingContextInfo:), pixels);
        } else {
            NSString* filePath = @(path);
            [UIImageJPEGRepresentation(newImage, quality) writeToFile:filePath atomically:YES];
        }

        CGColorSpaceRelease(colorSpaceRef);
        CGDataProviderRelease(provider);
        CGImageRelease(imageRef);
    #endif
}

@implementation KivyCaptureDelegate

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