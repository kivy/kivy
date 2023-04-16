from kivy.core.textinput import TextInputBase

from pyobjus import autoclass, protocol

class TextInputiOS(TextInputBase):

    _focused_textinput = None

    def start(self):
        if TextInputiOS._focused_textinput is not None:
            TextInputiOS._focused_textinput.pause()
        TextInputiOS._focused_textinput = self

        super().start()

        self._textfield = autoclass('KivyTextInput').alloc()
        self._textfield.initWithDelegate_(TextInputiOS._focused_textinput)
        self._textfield.setText_(self.text)
        self._textfield.startEditing()

        self.focus = True

    def select(self, start, end):
        self._textfield.selectTextFrom_end_(start, end)

    def pause(self):
        self._textfield.stopEditing()
        super().pause()

    # textField:(UITextField *)textField shouldChangeCharactersInRange:(NSRange)range replacementString:(NSString *)string
    @protocol('KivyTextInputDelegate')
    def shouldChangeCharactersFromLocation_withLength_andString_(self, location, length, string):
        safe_string = string.UTF8String()
        print("we should change characters from {} to {} with {}".format(location, location+length, safe_string))
        start = location
        end = location + length
        if string.length() == 0:
            # If the string is empty, that means we have to delete something instead.
            # So, start and end indexes should be reversed.
            end, start = start, end
        self.target.replace_text(safe_string, start, end)
        return True

    @protocol('KivyTextInputDelegate')
    def textFieldDidChangedSelectionFromStart_toEnd_(self, start, end):
        cursor = self.target.get_cursor_from_index(end)
        if cursor != self.target.cursor:
            print("The TextInput provider asked to change the cursor position")
            self.target.cursor = cursor
