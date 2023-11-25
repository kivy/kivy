//
//  textinput_ios.m
//  kivy-textinput-providers
//
//  Created by Mirko Galimberti on 17/04/23.
//

#import <Foundation/Foundation.h>

#include <UIKit/UIKit.h>

@protocol KivyTextInputDelegate <NSObject>

-(id) shouldChangeCharactersFromLocation:(long)location withLength:(long)length andString:(NSString *) string;
-(id) textFieldDidChangedSelectionFromStart:(long)start toEnd:(long)end;

@end

@interface KivyTextInputDelegateConsumer : NSObject <KivyTextInputDelegate>

@end

@implementation KivyTextInputDelegateConsumer

- (id) shouldChangeCharactersFromLocation:location withLength:length andString:(NSString *)string {
    
}

- (id) textFieldDidChangedSelectionFromStart:(long)start toEnd:(long)end {
    
}

@end


@interface KivyTextInput : NSObject <UITextFieldDelegate>

@property(nonatomic, strong)id <KivyTextInputDelegate> delegate;

@end

@implementation KivyTextInput
UITextField *textField;
-(id) initWithDelegate:(id<KivyTextInputDelegate>) delegate {
    self.delegate = delegate;

    textField = [[UITextField alloc] initWithFrame:CGRectZero];
    textField.delegate = self;

    /* set UITextInputTrait properties, mostly to defaults */
    //textField.autocapitalizationType = UITextAutocapitalizationTypeNone;
    // textField.autocorrectionType = UITextAutocorrectionTypeNo;
    //textField.enablesReturnKeyAutomatically = NO;
    textField.autocorrectionType = UITextAutocorrectionTypeDefault;
    textField.keyboardAppearance = UIKeyboardAppearanceDefault;
    textField.keyboardType = UIKeyboardTypeDefault;
    textField.returnKeyType = UIReturnKeyDefault;
    textField.hidden = YES;
    textField.secureTextEntry = NO;
    
    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(textUpdated:)
            name: UITextFieldTextDidChangeNotification
            object:nil];

}

- (void)textUpdated:(NSNotification*)notification
{
    UITextField *textField = (UITextField *)[notification object];
    NSLog(@"%@", textField.text);
}

- (void) setText:(const char*)text {
    textField.text = [[NSString alloc] initWithUTF8String: text];
}

- (void) startEditing {
    NSLog(@"startEditing");
    UIWindow *window = [[[UIApplication sharedApplication] delegate] window];
    [window.rootViewController.view addSubview:textField];
    [textField becomeFirstResponder];
}

- (void) stopEditing {
    [textField resignFirstResponder];
    UIWindow *window = [[[UIApplication sharedApplication] delegate] window];
    [window.rootViewController.view willRemoveSubview: textField];
    [textField removeFromSuperview];
}

- (void) selectTextFrom:(int)start end: (int)end {
    UITextPosition *firstCharacterPosition = [textField beginningOfDocument];
    UITextPosition *positionStart = [textField positionFromPosition:firstCharacterPosition offset:start];
    UITextPosition *positionEnd = [textField positionFromPosition:firstCharacterPosition offset:end];
    UITextRange *selectionRange = [textField textRangeFromPosition:positionStart toPosition:positionEnd];

    textField.selectedTextRange = selectionRange;
}

/*
- (void)textFieldTextDidChange:(NSNotification *)notification {
    
    NSLog(
    
}
*/

- (BOOL)textField:(UITextField *)textField shouldChangeCharactersInRange:(NSRange)range replacementString:(NSString *)string {
    [self.delegate shouldChangeCharactersFromLocation: range.location withLength: range.length andString: string ];
    return YES;
}

- (void) textFieldDidChangeSelection:(UITextField *)textField{
    NSLog(@"textFieldDidChangeSelection");
    
    NSInteger start = [textField offsetFromPosition:textField.beginningOfDocument toPosition:textField.selectedTextRange.start];
    NSInteger end = [textField offsetFromPosition:textField.beginningOfDocument toPosition:textField.selectedTextRange.end];
    
    [self.delegate textFieldDidChangedSelectionFromStart: start toEnd: end];
}

 
@end


