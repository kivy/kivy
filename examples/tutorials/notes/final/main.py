'''
Notes
=====

Simple application for reading/writing notes.

'''

__version__ = '1.0'

import json
from os.path import join, exists
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.properties import ListProperty, StringProperty, \
        NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock


class MutableTextInput(FloatLayout):

    text = StringProperty()
    multiline = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(MutableTextInput, self).__init__(**kwargs)
        Clock.schedule_once(self.prepare, 0)

    def prepare(self, *args):
        self.w_textinput = self.ids.w_textinput.__self__
        self.w_label = self.ids.w_label.__self__
        self.view()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.is_double_tap:
            self.edit()
            return True
        return super(MutableTextInput, self).on_touch_down(touch)

    def edit(self):
        self.clear_widgets()
        self.add_widget(self.w_textinput)
        self.w_textinput.focus = True

    def view(self):
        self.clear_widgets()
        self.add_widget(self.w_label)

    def check_focus_and_view(self, textinput):
        if not textinput.focus:
            self.text = textinput.text
            self.view()



class NoteView(Screen):

    note_index = NumericProperty()
    note_title = StringProperty()
    note_content = StringProperty()


class NoteListItem(BoxLayout):

    note_title = StringProperty()
    note_index = NumericProperty()


class Notes(Screen):

    data = ListProperty()

    def args_converter(self, row_index, item):
        return {
            'note_index': row_index,
            'note_content': item['content'],
            'note_title': item['title']}


class NoteApp(App):

    def build(self):
        self.notes = Notes(name='notes')
        self.load_notes()

        self.transition = SlideTransition(duration=.35)
        root = ScreenManager(transition=self.transition)
        root.add_widget(self.notes)
        return root

    def load_notes(self):
        if not exists(self.notes_fn):
            return
        with open(self.notes_fn, 'rb') as fd:
            data = json.load(fd)
        self.notes.data = data

    def save_notes(self):
        with open(self.notes_fn, 'wb') as fd:
            json.dump(self.notes.data, fd)

    def del_note(self, note_index):
        del self.notes.data[note_index]
        self.save_notes()
        self.refresh_notes()
        self.go_notes()

    def edit_note(self, note_index):
        note = self.notes.data[note_index]
        name = 'note{}'.format(note_index)

        if self.root.has_screen(name):
            self.root.remove_widget(self.root.get_screen(name))

        view = NoteView(
            name=name,
            note_index=note_index,
            note_title=note.get('title'),
            note_content=note.get('content'))

        self.root.add_widget(view)
        self.transition.direction = 'left'
        self.root.current = view.name

    def add_note(self):
        self.notes.data.append({'title': 'New note', 'content': ''})
        note_index = len(self.notes.data) - 1
        self.edit_note(note_index)

    def set_note_content(self, note_index, note_content):
        self.notes.data[note_index]['content'] = note_content
        data = self.notes.data
        self.notes.data = []
        self.notes.data = data
        self.save_notes()
        self.refresh_notes()

    def set_note_title(self, note_index, note_title):
        self.notes.data[note_index]['title'] = note_title
        self.save_notes()
        self.refresh_notes()

    def refresh_notes(self):
        data = self.notes.data
        self.notes.data = []
        self.notes.data = data

    def go_notes(self):
        self.transition.direction = 'right'
        self.root.current = 'notes'

    @property
    def notes_fn(self):
        return join(self.user_data_dir, 'notes.json')

if __name__ == '__main__':
    NoteApp().run()
