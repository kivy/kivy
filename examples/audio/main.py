'''
Audio Playback Demonstration
=============================

This demonstration plays sounds of different formats. You should see a grid of
buttons labelled with file names. Clicking on the buttons will play, or
restart, each sound. You can play multiple sounds at once, but not all sound
formats will play on all platforms. The slider on the left controls volume.

Chip sounds are from http://woolyss.com/chipmusic-samples.php
"THE FREESOUND PROJECT", Under Creative Commons Sampling Plus 1.0 License.
Piano sounds are from https://archive.org/details/Piano_804, Internet Archive,
placed into the public domain.  Beethoven sounds are from
https://archive.org/details/SymphonyNo.5, Internet Archive, placed into the
public domain.   Some free format conversions done by
http://www.online-convert.com.
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
from kivy.logger import Logger


class AudioButton(Button):

    filename = StringProperty(None)
    sound = ObjectProperty(None, allownone=True)
    volume = NumericProperty(1.0)

    def on_press(self):
        """ load and play on press, restarting if playing. """
        if self.sound is None:
            self.sound = SoundLoader.load(self.filename)
            if self.sound is None:
                Logger.error("audio-main.py: unable to get SoundLoader for %s",
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
        for fn in glob(join(dirname(__file__), '*.wav')):
            btn = AudioButton(
                text=basename(fn[:-4]).replace('_', ' '), filename=fn,
                size_hint=(None, None), halign='center',
                size=(128, 128), text_size=(118, None))
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
