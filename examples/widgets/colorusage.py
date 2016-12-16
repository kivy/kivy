from kivy.app import App
<<<<<<< HEAD
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

Builder.load_string(''' #:import hex kivy.utils.get_color_from_hex

<Root>:
    orientation: 'vertical'
=======
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder

Builder.load_string("""
#:import hex kivy.utils.get_color_from_hex

<Root>:
    cols: 2
>>>>>>> 1c94c9af439ae953d3c20de513e96691f2a09b37
    canvas:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

<<<<<<< HEAD
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
=======
    Label:
        canvas.before:
            Color:
                rgb: 39/255., 174/255., 96/255.
            Rectangle:
                pos: self.pos
                size: self.size
        text: "rgb: 39/255., 174/255., 96/255."
    Label:
        canvas.before:
            Color:
                rgba: 39/255., 174/255., 96/255., 1
            Rectangle:
                pos: self.pos
                size: self.size
        text: "rgba: 39/255., 174/255., 96/255., 1"
    Label:
        canvas.before:
            Color:
                hsv: 145/360., 77.6/100, 68.2/100
            Rectangle:
                pos: self.pos
                size: self.size
        text: "hsv: 145/360., 77.6/100, 68.2/100"
    Label:
        canvas.before:
            Color:
                rgba: hex('#27ae60')
            Rectangle:
                pos: self.pos
                size: self.size
        text: "rgba: hex('#27ae60')"
""")


class Root(GridLayout):
>>>>>>> 1c94c9af439ae953d3c20de513e96691f2a09b37
    pass


class ColorusageApp(App):
    def build(self):
        return Root()

<<<<<<< HEAD
=======

>>>>>>> 1c94c9af439ae953d3c20de513e96691f2a09b37
if __name__ == "__main__":
    ColorusageApp().run()
