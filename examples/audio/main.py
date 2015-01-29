'''
Audio example
=============

Chip sounds are from the http://woolyss.com/chipmusic-samples.php
"THE FREESOUND PROJECT", Under Creative Commons Sampling Plus 1.0 License.

Piano sounds are from https://archive.org/details/Piano_804, Internet Archive,
placed into the public domain.

'''

import kivy
kivy.require('1.0.8')

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.core.audio import SoundLoader
from kivy.properties import StringProperty, ObjectProperty, NumericProperty
from glob import glob
from os.path import dirname, join, basename
from kivy import Logger

class AudioButton(Button):
    filename = StringProperty(None)
    sound = ObjectProperty(None, allownone=True)
    volume = NumericProperty(1.0)

    def on_press(self):
        """ Load and play sound on button press.  Restart if playing.
        """
        if self.sound is None:
            self.sound = SoundLoader.load(self.filename)
            if self.sound is None:
                Logger.error("demo: Unable get SoundLoader for %s",
                             self.filename)
                return
        # stop the sound if it's currently playing
        if self.sound.status != 'stop':
            self.sound.stop()
        self.sound.volume = self.volume
        self.sound.play()

    def release_audio(self):
        if self.sound:
            self.sound.stop()
            self.sound.unload()
            self.sound = None

    def set_volume(self, volume):
        self.volume = volume
        if self.sound:
            self.sound.volume = volume


class AudioBackground(BoxLayout):
    pass


class AudioApp(App):

    def build(self):
        root = AudioBackground(spacing=5)
        filenames = []
        for ext in ['wav', 'mp3', 'ogg']:
            found = glob(join(dirname(__file__), '*.'+ext))
            filenames.extend(found)

        for fn in sorted(filenames):
            btn = AudioButton(
                text=basename(fn[:-4]).replace('_', ' '), filename=fn,
                size_hint=(None, None), halign='center',
                size=(128, 64), text_size=(118, None))
            root.ids.sl.add_widget(btn)

        return root

    def release_audio(self):
        for audiobutton in self.root.ids.sl.children:
            audiobutton.release_audio()

    def set_volume(self, value):
        for audiobutton in self.root.ids.sl.children:
            audiobutton.set_volume(value)

if __name__ == '__main__':
    AudioApp().run()
