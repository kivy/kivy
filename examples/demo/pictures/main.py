import kivy
kivy.require('1.0.6')

from glob import glob
from random import randint
from os.path import join, dirname
from kivy.app import App
from kivy.logger import Logger
from kivy.uix.scatter import Scatter
from kivy.properties import StringProperty
# FIXME this shouldn't be necessary
from kivy.core.window import Window


class Picture(Scatter):

    source = StringProperty(None)


class PicturesApp(App):

    def build(self):

        # the root is created in pictures.kv
        root = self.root

        # get any files into images directory
        curdir = dirname(__file__)
        for filename in glob(join(curdir, 'images', '*')):
            try:
                # load the image
                picture = Picture(source=filename, rotation=randint(-30,30))
                # add to the main field
                root.add_widget(picture)
            except Exception, e:
                Logger.exception('Pictures: Unable to load <%s>' % filename)


if __name__ in ('__main__', '__android__'):
    PicturesApp().run()

