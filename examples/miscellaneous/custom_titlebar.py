from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.lang.builder import Builder
from kivy.core.window import Window
from kivy.logger import Logger
kv = """
#:import rgba kivy.utils.rgba
<TitleBar>:
    id:title_bar
    size_hint: 1,0.1
    pos_hint : {'top':0.5}
    BoxLayout:
        orientation:"vertical"
        BoxLayout:
            Button:
                text: "Click-able"
                draggable:False
            Button:
                text: "non Click-able"
            Button:
                text: "non Click-able"
        BoxLayout:
            draggable:False
            Button:
                text: "Click-able"
            Button:
                text: "click-able"
            Button:
                text: "Click-able"

FloatLayout:
"""


class TitleBar(BoxLayout):
    pass


class CustomTitleBar(App):

    def build(self):
        root = Builder.load_string(kv)
        Window.custom_titlebar = True
        title_bar = TitleBar()
        root.add_widget(title_bar)
        if Window.set_custom_titlebar(title_bar):
            Logger.info("Window: setting custom titlebar successful")
        else:
            Logger.info("Window: setting custom titlebar "
                        "Not allowed on this system ")
        self.title = "MyApp"
        return root


if __name__ == "__main__":
    CustomTitleBar().run()
