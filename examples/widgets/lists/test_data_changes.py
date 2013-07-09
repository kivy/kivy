#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
from random import choice
from string import ascii_uppercase, digits

from kivy.app import App
from kivy.lang import Builder

from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.dictadapter import DictAdapter

from kivy.properties import ListProperty
from kivy.properties import StringProperty

from kivy.uix.listview import ListItemButton
from kivy.uix.listview import ListView
from kivy.uix.screenmanager import FadeTransition
from kivy.uix.screenmanager import Screen
from kivy.uix.screenmanager import ScreenManager


Builder.load_string('''
#:import choice random.choice
#:import sample random.sample

<ItemsScreen>:

    BoxLayout:
        pos_hint: {'center_x': .5, 'center_y': .5}
        size_hint: .9, .7
        padding: 3
        spacing: 5

        BoxLayout:
            orientation: 'vertical'
            padding: 3
            spacing: 5

            Label:
                pos_hint: {'center_x': .5}
                size_hint: None, None
                width: 200
                height: 30
                text: 'TEST ChangeRecordingObservableList'

            ListView:
                adapter: app.list_adapter

                canvas:
                    Color:
                        rgba: .4, .4, .4, .4
                    Rectangle:
                        pos: self.pos
                        size: self.size

            GridLayout:
                size_hint: .3, None
                cols: 3
                padding: 3
                spacing: 5

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'setitem'
                    on_release: app.list_adapter.data[ \
                            app.list_adapter.selection[0].index] = \
                            choice(app.nato_alphabet_words)

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'delitem'
                    on_release: del app.list_adapter.data[ \
                            app.list_adapter.selection[0].index]

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'setslice (3)'
                    on_release: app.list_adapter.data[ \
                            app.list_adapter.selection[0].index: \
                            app.list_adapter.selection[0].index + 3] = \
                            [choice(app.nato_alphabet_words)] * 3

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'delslice (3)'
                    on_release: del app.list_adapter.data[ \
                            app.list_adapter.selection[0].index: \
                            app.list_adapter.selection[0].index + 3]
    #
    # TODO: iadd and imul are getting a nonetype is not iterable error on the base
    # crod object. So we will add labels instead of buttons for them for now.
    #
    #            Button:
    #                size_hint: None, None
    #                width:80
    #                height: 30
    #                text: 'iadd'
    #                on_release: app.list_adapter.data += \
    #                        [choice(app.nato_alphabet_words)] * 3
    #
    #            Button:
    #                size_hint: None, None
    #                width:80
    #                height: 30
    #                text: 'imul'
    #                on_release: app.list_adapter.data *= 2
    #
                Label:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'iadd'

                Label:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'imul'

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'append'
                    on_release: app.list_adapter.data.append( \
                            choice(app.nato_alphabet_words))

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'remove'
                    on_release: app.list_adapter.data.remove( \
                            app.list_adapter.data[ \
                                app.list_adapter.selection[0].index])

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'insert'
                    on_release: app.list_adapter.data.insert( \
                            app.list_adapter.selection[0].index, \
                            choice(app.nato_alphabet_words))

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'pop()'
                    on_release: app.list_adapter.data.pop()

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'pop(i)'
                    on_release: app.list_adapter.data.pop( \
                                app.list_adapter.selection[0].index)

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'extend (3)'
                    on_release: app.list_adapter.data.extend( \
                            [choice(app.nato_alphabet_words)] * 3)

    # TODO: sort and reverse
    #
    #            Button:
    #                size_hint: None, None
    #                width:80
    #                height: 30
    #                text: 'sort'
    #
    #            Button:
    #                size_hint: None, None
    #                width:80
    #                height: 30
    #                text: 'reverse'

                Label:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'sort'

                Label:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'reverse'

        BoxLayout:
            orientation: 'vertical'
            padding: 3
            spacing: 5

            Label:
                pos_hint: {'center_x': .5}
                size_hint: None, None
                width: 200
                height: 30
                text: 'TEST ChangeRecordingObservableDict'

            ListView:
                adapter: app.dict_adapter

                canvas:
                    Color:
                        rgba: .4, .4, .4, .4
                    Rectangle:
                        pos: self.pos
                        size: self.size

            GridLayout:
                size_hint: .3, None
                cols: 3
                padding: 3
                spacing: 5

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'setitem set'
                    on_release: app.dict_adapter.data[ \
                            app.dict_adapter.selection[0].key] = \
                                {'key': app.dict_adapter.selection[0].key, \
                                 'value': ''.join(sample('abcdefghijklmnopqrstuvwxyz', 10))}

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'setitem add'
                    on_release: app.dict_adapter.data[ \
                            ''.join(sample('abcdefghijklmnopqrstuvwxyz', 10))] = \
                            ''.join(sample('abcdefghijklmnopqrstuvwxyz', 10))

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'setitem del'
                    on_release: \
                        app.dict_adapter.data[ \
                            app.dict_adapter.sorted_keys[ \
                                app.dict_adapter.selection[0].index]] = None

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'delitem'
                    on_release: del app.dict_adapter.data[ \
                                        app.dict_adapter.sorted_keys[ \
                                            app.dict_adapter.selection[0].index]]

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'clear'
                    on_release: app.dict_adapter.data.clear()

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'pop'
                    on_release: app.dict_adapter.data.pop( \
                                        app.dict_adapter.sorted_keys[ \
                                            app.dict_adapter.selection[0].index])

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'popitem'
                    on_release: app.dict_adapter.data.popitem()

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'setdefault'
                    on_release: k = ''.join(sample('abcdefghijklmnopqrstuvwxyz', 10)); \
                                app.dict_adapter.data.setdefault(k, {'key': k, 'value': k})

                Label:
#                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'update (3)'
#                    on_release: app.dict_adapter.data.update( \
#                            {''.join(sample('abcdefghijklmnopqrstuvwxyz', 26)): 'random letters', \
#                             ''.join(sample('abcdefghijklmnopqrstuvwxyz', 26)): 'random letters', \
#                             ''.join(sample('abcdefghijklmnopqrstuvwxyz', 26)): 'random letters'})

                Label:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: '[insert]'
''')


class ItemsScreen(Screen):
    pass


def list_args_converter(row_index, value):
    return {"text": str(value),
            "size_hint_y": None,
            "height" : 25}

def dict_args_converter(row_index, rec):
    return {"text": "{} : {}".format(rec['key'], rec['value']),
            "key": rec['key'],
            "size_hint_y": None,
            "height" : 25}


class KeyedListItemButton(ListItemButton):

    key = StringProperty('')

    def __init__(self, **kwargs):
        super(KeyedListItemButton, self).__init__(**kwargs)


class Test(App):

    nato_alphabet_words = ListProperty([
        'Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo', 'Foxtrot', 'Golf',
        'Hotel', 'India', 'Juliet', 'Kilo', 'Lima', 'Mike', 'November',
        'Oscar', 'Papa', 'Quebec', 'Romeo', 'Sierra', 'Tango', 'Uniform',
        'Victor', 'Whiskey', 'X-ray', 'Yankee', 'Zulu'])

    data = ListProperty([
        'Delta', 'Oscar', 'Golf', 'Sierra',
        'Alpha', 'November', 'Delta',
        'Charlie', 'Alpha', 'Tango', 'Sierra'])

    def build(self):

        self.list_adapter = ListAdapter(data=self.data,
                                        cls=ListItemButton,
                                        selection_mode='single',
                                        allow_empty_selection=False,
                                        args_converter=list_args_converter)

        self.dict_adapter = DictAdapter(data={k: {'key': k, 'value': k} for k in self.nato_alphabet_words},
                                        cls=KeyedListItemButton,
                                        selection_mode='single',
                                        allow_empty_selection=False,
                                        args_converter=dict_args_converter)

        self._screen_manager = ScreenManager()

        self._screen_manager.add_widget(ItemsScreen(name="test_data_changes"))

        return self._screen_manager


if __name__ == '__main__':
    Test().run()
