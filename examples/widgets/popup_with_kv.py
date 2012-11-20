'''
Example to show a Popup usage with the content from kv lang.
'''
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.app import App
from kivy.lang import Builder

Builder.load_string('''
<CustomPopup>:
    size_hint: .5, .5
    auto_dismiss: False
    title: 'Hello world'
    Button:
        text: 'Click me to dismiss'
        on_press: root.dismiss()

''')

class CustomPopup(Popup):
    pass

class TestApp(App):
    def build(self):
        b = Button(on_press=self.show_popup)
        return b

    def show_popup(self, b):
        p = CustomPopup()
        p.open()

TestApp().run()
