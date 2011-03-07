import glob
import random
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image


class Picture(Image):
    pass

class PicturesApp(App):
    def build(self):
        for filename in glob.glob('images/*'):
            picture = Picture(source=filename)
            self.add_picture(picture)

    def add_picture(self, picture):
        scatter = Scatter()
        scatter.size = picture.size
        scatter.center = Window.center
        scatter.rotation = random.randint(-30,30)
        scatter.add_widget(picture)
        self.root.add_widget(scatter)

if __name__ in ('__main__', '__android__'):
    PicturesApp().run()

