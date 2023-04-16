from kivy.core.textinput import TextInputBase
from kivy.clock import mainthread

from jnius import autoclass, java_method, PythonJavaClass

from android.runnable import run_on_ui_thread


EditText = autoclass("android.widget.EditText")
InputMethodManager = autoclass("android.view.inputmethod.InputMethodManager")
Context = autoclass("android.content.Context")
PythonActivity = autoclass("org.kivy.android.PythonActivity")
RelativeLayoutLayoutParams = autoclass("android.widget.RelativeLayout$LayoutParams")


class TextWatcher(PythonJavaClass):
    __javainterfaces__ = ["android/text/TextWatcher"]
    __context__ = "app"

    def __init__(self, **kwargs):
        self.onTextChanged_cb = None
        super().__init__(**kwargs)

    @java_method("(Ljava/lang/CharSequence;III)V")
    def onTextChanged(self, text, start, lengthBefore, lengthAfter):
        if self.onTextChanged_cb:
            self.onTextChanged_cb(text, start, lengthBefore, lengthAfter)
        else:
            print("onTextChanged", text, start, lengthBefore, lengthAfter)

    # beforeTextChanged
    @java_method("(Ljava/lang/CharSequence;III)V")
    def beforeTextChanged(self, text, start, lengthBefore, lengthAfter):
        print("beforeTextChanged", text, start, lengthBefore, lengthAfter)

    # afterTextChanged
    @java_method("(Landroid/text/Editable;)V")
    def afterTextChanged(self, editable):
        print("afterTextChanged", editable)


class TextInputAndroid(TextInputBase):
    _focused_textinput = None
    _edittext = None

    @run_on_ui_thread
    def start(self):
        if TextInputAndroid._focused_textinput is not None:
            TextInputAndroid._focused_textinput.pause()
        TextInputAndroid._focused_textinput = self

        super().start()

        self._layout = PythonActivity.mActivity.getLayout()
        self._edittext = EditText(PythonActivity.mActivity)

        layoutParams = RelativeLayoutLayoutParams(10, 1)
        layoutParams.topMargin = 0
        layoutParams.leftMargin = 0
        # self._edittext.setLayoutParams(layoutParams)
        # self._edittext.onTextChanged = self.onTextChanged
        self._textwatcher = TextWatcher()
        self._textwatcher.onTextChanged_cb = self.onTextChanged
        self._edittext.addTextChangedListener(self._textwatcher)
        # self._edittext.onSelectionChanged = self.onSelectionChanged

        self._layout.addView(self._edittext, 0, layoutParams)

        # Ensure the TextView is focusable
        self._edittext.setFocusable(True)
        # Make the TextView hidden
        self._edittext.setVisibility(EditText.VISIBLE)

        # Set the TextView text to the one of the TextInput
        # setText(char[] text, int start, int len)
        self._edittext.setText(self.text, 0, len(self.text))

        # Force the TextView to get focus
        self._edittext.requestFocus()
        print("requestFocus", self._edittext.isFocused())

        imm = PythonActivity.mActivity.getSystemService(Context.INPUT_METHOD_SERVICE)
        imm.showSoftInput(self._edittext, 0)
        print("showSoftInput")
        self.focus = True

    @run_on_ui_thread
    def select(self, start, end):
        if not self._edittext:
            return
        self._edittext.setSelection(start, end)

    @run_on_ui_thread
    def pause(self):
        # Unfocus the TextView
        self._edittext.clearFocus()

        super().pause()

    # void onTextChanged(CharSequence text, int start, int lengthBefore, int lengthAfter
    # @java_method("(Ljava/lang/CharSequence;III)V")
    @mainthread
    def onTextChanged(self, text, start, lengthBefore, lengthAfter):
        # This method is called to notify you that, within s, the count characters
        # beginning at start have just replaced old text that had length before.
        print("onTextChanged", text, start, lengthBefore, lengthAfter)

        self.target.replace_text(
            text[start:start+lengthAfter],
            start,
            start + lengthBefore,
            move_cursor_at_end=False,
        )

        self.target.cursor = self.target.get_cursor_from_index(start + lengthAfter)

    # void onSelectionChanged(int selStart, int selEnd)
    @java_method("(II)V")
    def onSelectionChanged(self, selStart, selEnd):
        print("onSelectionChanged", selStart, selEnd)
