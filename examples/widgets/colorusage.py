from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder

Builder.load_string("""
#:import hex kivy.utils.get_color_from_hex

<Root>:
    cols: 2
    canvas:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

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
    pass


class ColorusageApp(App):
    def build(self):
        return Root()


if __name__ == "__main__":
    ColorusageApp().run()
