# encoding: utf8

from kivy.app import App
from kivy.core.audio import SoundLoader
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from sys import version_info


NOTES = (
    ("Do", 1),
    ("Ré", 9 / 8.0),
    ("Mi", 5 / 4.0),
    ("Fa", 4 / 3.0),
    ("Sol", 3 / 2.0),
    ("La", 5 / 3.0),
    ("Si", 15 / 8.0),
)


class Test(App):
    def build(self):
        self.sound = SoundLoader.load(
            "/usr/lib64/python{}.{}/test/audiodata/pluck-pcm32.wav".format(
                *version_info[0:2]
            )
        )
        root = BoxLayout()
        for octave in range(-2, 3):
            for note, pitch in NOTES:
                button = Button(text=note)
                button.pitch = pitch * 2 ** octave
                button.bind(on_release=self.play_note)
                root.add_widget(button)
        return root

    def play_note(self, button):
        self.sound.pitch = button.pitch
        self.sound.play()


Test().run()
