# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup


Builder.load_string(
'''
#: import resource_find kivy.resources
#: import utils kivy
#: import os os
<Unicode_TextInput>
    orientation: 'vertical'
    txt_input: unicode_txt
    ScrollView:
        size_hint: 1, .9
        TextInput:
            id: unicode_txt
            text: root.unicode_string
            size_hint: 1, None
            height: 1364
            on_touch_down:
                print (self.line_height-1+self.padding_y)*(len(self._lines)-1)
    BoxLayout:
        size_hint: 1, .05
        Label:
            text: 'current font: ' + unicode_txt.font_name
        Button:
            size_hint: .15, 1
            text: 'change Font ...'
            valign: 'middle'
            halign: 'center'
            text_size: self.size
            on_release: root.show_load()

<LoadDialog>:
    BoxLayout:
        size: root.size
        pos: root.pos
        BoxLayout:
            orientation: "vertical"
            size_hint: .2, 1
            Button:
                size_hint: 1, .2
                text: 'User font directory\\n'
                valign: 'middle'
                halign: 'center'
                text_size: self.size
                on_release:
                    _platform = utils.platform()
                    filechooser.path = os.path.expanduser('~/.fonts')\
if _platform in ('linux', 'android') else os.path.expanduser('~/Library/Fonts')\
if _platform == 'macosx' else os.environ['WINDIR'] + '\Fonts\'
            Button:
                size_hint: 1, .2
                text: 'System Font directory'
                valign: 'middle'
                halign: 'center'
                text_size: self.size
                on_release:
                    _platform = utils.platform()
                    filechooser.path = '/usr/share/fonts' \
if _platform in ('linux', 'android') else os.path.expanduser\
('/System/Library/Fonts') if _platform == 'macosx' else os.environ['WINDIR']\
+ "\Fonts\"
            Label:
                text: 'BookMarks'
        BoxLayout:
            orientation: "vertical"
            FileChooserListView:
                id: filechooser
                filters: ['*.ttf']
            BoxLayout:
                size_hint_y: None
                height: 30
                Button:
                    text: "cancel"
                    on_release: root.cancel()
                Button:
                    text: "load"
                    on_release: filechooser.selection != [] and root.load\
(filechooser.path, filechooser.selection)
''')


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


class Unicode_TextInput(BoxLayout):

    txt_input = ObjectProperty(None)
    unicode_string = StringProperty(u'''Latin-1 suppliment: éé çç ßß''')

    def dismiss_popup(self):
        self._popup.dismiss()

    def load(self, _path, _fname):
        self.txt_input.font_name = _fname[0]
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="load file", content=content, \
            size_hint=(0.9, 0.9))
        self._popup.open()


class unicode_app(App):

    def build(self):
        return Unicode_TextInput()


if __name__ == '__main__':

    unicode_app().run()
