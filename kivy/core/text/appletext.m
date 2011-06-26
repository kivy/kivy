#import "appletext.h"


CGSize getStringExtents(char *_string, char *_font, int size) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    NSString *string = [NSString stringWithUTF8String:_string];
    NSString *fontName = [NSString stringWithUTF8String:_font];
    NSFont *font = [NSFont fontWithName:fontName size:size];
    NSDictionary *attributes = [NSDictionary dictionaryWithObjectsAndKeys:font,
                                NSFontAttributeName, nil];
    NSSize exts = [[[NSAttributedString alloc] initWithString:string
                                            attributes:attributes] size];
    [pool drain];
    return CGSizeMake(exts.width, exts.height);
}