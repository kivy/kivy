from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

Builder.load_string(''' #:import hex kivy.utils.get_color_from_hex

<Root>:
    orientation: 'vertical'
    canvas:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        Label:
            canvas.before:
                Color:
                    rgb: 205.0/255, 220.0/255, 57.0/255
                Rectangle:
                    pos: self.pos
                    size: self.size
            text: "rgb: 205.0/255, 220.0/255, 57.0/255"

        Label:
            canvas.before:
                Color:
                    rgba: 205.0/255, 220.0/255, 57.0/255, 0.8
                Rectangle:
                    pos: self.pos
                    size: self.size
            text: "rgba: 205.0/255, 220.0/255, 57.0/255, 0.8"

    BoxLayout:
        Label:
            canvas.before:
                Color:
                    hsv: 66.0/360, 0.741, 0.863  # rgb->hsv conversion required
                Rectangle:
                    pos: self.pos
                    size: self.size
            text: "hsv: 66.0/360, 0.741, 0.863"

        Label:
            canvas.before:
                Color:
                    rgba: hex('#CDDC39')
                Rectangle:
                    pos: self.pos
                    size: self.size
            text: "rgba: hex('#CDDC39')" ''')


class Root(BoxLayout):
    pass


class ColorusageApp(App):
    def build(self):
        return Root()

if __name__ == "__main__":
    ColorusageApp().run()
