# AN APP BY THE ONE AND ONLY,
# THE LEGEND,
# COCO DE VIENNE.

try:
    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.widget import Widget
    from kivy.uix.textinput import TextInput
    from kivy.uix.button import Button
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.popup import Popup
except Exception as error:
    exit()

def displaytext(string):
    test_title = string.split(" ")[0]
    popup = Popup(title=test_title,content=Label(text=string),size_hint=(None, None), size=(400, 400))
    popup.open()

def displayinfo():
    info = "INFO"
    string = "This app was written by Coco de Vienne.\n This app utilizes the Kivy UI Kit to render a smooth UI.\n If you like what you see, follow me on my social media!\n You can visit my website here: cocodevienne.github.io\n"
    popup = Popup(title=info,content=Label(text=string),size_hint=(None, None), size=(400, 400))
    popup.open()

def displaylicense():
    gpl = "LICENSE AGREEMENT"
    string = "This software is licensed under the GNU GPL V3.0!\n You can view license on the website of the FSF!\n"
    popup = Popup(title=gpl,content=Label(text=string),size_hint=(None, None), size=(400, 400))
    popup.open()

class SimpleDisplayWindow(GridLayout):
    def __init__(self):
        super(SimpleDisplayWindow, self).__init__()
        self.cols = 1
        self.add_widget(Label(text="TEXT:"))
        text_string = TextInput(multiline=True)
        self.add_widget(text_string)
        display_button = (Button(text="DISPLAY"))
        self.add_widget(display_button)
        display_button.bind(on_press=lambda*args:displaytext(text_string.text))
        self.add_widget(Label(text="FURTHER INFO"))
        about_button = (Button(text="ABOUT"))
        self.add_widget(about_button)
        about_button.bind(on_press=lambda*args:displayinfo())
        license_button = (Button(text="LICENSE"))
        self.add_widget(license_button)
        license_button.bind(on_press=lambda*args:displaylicense())




class SD(App):
    def build(self):
        return SimpleDisplayWindow()

if __name__ == "__main__":
    SD().run()
