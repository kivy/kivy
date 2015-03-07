'''
Audio Playback Demonstration
=============================

This demonstration plays sounds of different formats. You should see a grid of
buttons labelled with file names. Clicking on the buttons will play, or
restart, each sound. If you start the piano sound, and quickly click another
sound, you will hear both sounds being played at once (mixed). The slider on
the left controls volume.

The program will attempt to play all sound files in the current directory,
but most platforms only a few formats.

Chip sounds are from http://woolyss.com/chipmusic-samples.php
"THE FREESOUND PROJECT", Under Creative Commons Sampling Plus 1.0 License.
The piano sound is downsampled from https://archive.org/details/Piano_804,
Internet Archive, placed into the public domain. You can convert to other
formats using http://www.online-convert.com.
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

extensions = '*.aac *.aiff *.flac *.m4a *.mp3 *.ogg *.opus *.wav *.wma'.split()


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
        filenames = []
        for extension in extensions:
            filenames.extend(glob(join(dirname(__file__), extension)))
        for fn in sorted(filenames):
            btn = AudioButton(
                text=basename(fn[:-4]).replace('_', ' ').strip('.'),
                filename=fn,
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
