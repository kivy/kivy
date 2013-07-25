#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
from random import choice
from string import ascii_uppercase, digits

from kivy.app import App
from kivy.lang import Builder
from random import sample

from kivy.adapters.models import SelectableDataItem
from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.dictadapter import DictAdapter

from kivy.properties import ListProperty
from kivy.properties import StringProperty

from kivy.uix.listview import ListItemButton
from kivy.uix.listview import ListView
from kivy.uix.screenmanager import FadeTransition
from kivy.uix.screenmanager import Screen
from kivy.uix.screenmanager import ScreenManager


class KeyedListItemButton(ListItemButton):

    key = StringProperty('')

    def __init__(self, **kwargs):
        super(KeyedListItemButton, self).__init__(**kwargs)


class CustomDataItem(SelectableDataItem):

    def __init__(self, **kwargs):
        super(CustomDataItem, self).__init__(**kwargs)
        self.text = kwargs.get('text', '')


Builder.load_string('''
#:import choice random.choice
#:import sample random.sample
#:import Logger kivy.logger.Logger

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

            Button:
                pos_hint: {'center_x': .5}
                size_hint: None, None
                width: 200
                height: 30
                text: 'Load with String Data'
                on_release: app.list_adapter.args_converter = app.strings_args_converter; \
                            del app.list_adapter.data[0:len(app.list_adapter.data)]; \
                            [app.list_adapter.data.append(s) for s in app.string_data]

            Button:
                pos_hint: {'center_x': .5}
                size_hint: None, None
                width: 200
                height: 30
                text: 'Load with Object Data'
                on_release: app.set_object_data()

            Label:
                pos_hint: {'center_x': .5}
                size_hint: None, None
                width: 200
                height: 30
                text: 'TEST RecordingObservableList'

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
                                choice(app.nato_alphabet_words) \
                                if app.data_is_strings() \
                                else app.create_list_item_obj()

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
                                [choice(app.nato_alphabet_words)] * 3 \
                                if app.data_is_strings() \
                                else app.create_list_item_obj_list(3)

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
    # ROD object. So we will add labels instead of buttons for them for now.
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
                                    choice(app.nato_alphabet_words) \
                                        if app.data_is_strings() \
                                        else app.create_list_item_obj())

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
                                    choice(app.nato_alphabet_words) \
                                        if app.data_is_strings() \
                                        else app.create_list_item_obj())

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
                                    [choice(app.nato_alphabet_words)] * 3 \
                                        if app.data_is_strings() \
                                        else app.create_list_item_obj_list(3))

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'sort'
                    on_release: app.list_adapter.data.sort(key=lambda obj: obj.text) \
                                    if app.list_adapter.args_converter == app.objects_args_converter \
                                    else app.list_adapter.data.sort()

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'reverse'
                    on_release: app.list_adapter.data.reverse()

        BoxLayout:
            orientation: 'vertical'
            padding: 3
            spacing: 5

            Label:
                pos_hint: {'center_x': .5}
                size_hint: None, None
                width: 200
                height: 30
                text: 'TEST RecordingObservableDict'

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
                                     'value': ''.join(sample('abcdefghijklmnopqrstuvwxyz', 10))} \
                                if app.dict_adapter.selection \
                                else Logger.info('Testing: No selection. Cannot setitem set.')

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'setitem add'
                    on_release: k = ''.join(sample('abcdefghijklmnopqrstuvwxyz', 10)); \
                                app.dict_adapter.data[k] = {'key': k, 'value': k}

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
                                            app.dict_adapter.selection[0].index]) \
                                if app.dict_adapter.data.keys() \
                                else Logger.info('Testing: Data is empty. Cannot pop.')

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'popitem'
                    on_release: app.dict_adapter.data.popitem() \
                                if app.dict_adapter.data.keys() \
                                else Logger.info('Testing: Data is empty. Cannot popitem.')

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'setdefault'
                    on_release: k = ''.join(sample('abcdefghijklmnopqrstuvwxyz', 10)); \
                                app.dict_adapter.data.setdefault(k, {'key': k, 'value': k})

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'update (3)'
                    on_release: k1 = ''.join(sample('abcdefghijklmnopqrstuvwxyz', 10)); \
                                k2 = ''.join(sample('abcdefghijklmnopqrstuvwxyz', 10)); \
                                k3 = ''.join(sample('abcdefghijklmnopqrstuvwxyz', 10)); \
                                app.dict_adapter.data.update({k1: {'key': k1, 'value': k1}, \
                                                              k2: {'key': k2, 'value': k2}, \
                                                              k3: {'key': k3, 'value': k3}})

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'insert'
                    on_release: app.insert_into_dict(app.dict_adapter.selection[0].index)

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'sort'
                    on_release: app.dict_adapter.sorted_keys.sort(key=lambda k: k.lower())
''')


class ItemsScreen(Screen):
    pass


class Test(App):

    nato_alphabet_words = ListProperty([
        'Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo', 'Foxtrot', 'Golf',
        'Hotel', 'India', 'Juliet', 'Kilo', 'Lima', 'Mike', 'November',
        'Oscar', 'Papa', 'Quebec', 'Romeo', 'Sierra', 'Tango', 'Uniform',
        'Victor', 'Whiskey', 'X-ray', 'Yankee', 'Zulu'])

    string_data = ListProperty([
        'Delta', 'Oscar', 'Golf', 'Sierra',
        'Alpha', 'November', 'Delta',
        'Charlie', 'Alpha', 'Tango', 'Sierra'])

    object_data = ListProperty([])

    def create_list_item_obj(self):
        return CustomDataItem(text=choice(self.nato_alphabet_words))

    def create_list_item_obj_list(self, n):
        return [CustomDataItem(text=choice(self.nato_alphabet_words))] * n

    def strings_args_converter(self, row_index, value):
        return {"text": str(value),
                "size_hint_y": None,
                "height" : 25}

    def objects_args_converter(self, row_index, obj):
        print row_index, obj
        return {"text": obj.text,
                "size_hint_y": None,
                "height" : 25}

    def data_is_strings(self):
        if self.list_adapter.args_converter == self.strings_args_converter:
            return True
        return False

    def dict_args_converter(self, row_index, rec):
        return {"text": "{0} : {1}".format(rec['key'], rec['value']),
                "key": rec['key'],
                "size_hint_y": None,
                "height" : 25}

    def insert_into_dict(self, index):
        key = ''.join(sample('abcdefghijklmnopqrstuvwxyz', 10))
        self.dict_adapter.insert(index, key, {'key': key, 'value': key})

    def set_object_data(self):
        self.list_adapter.args_converter = self.objects_args_converter
        self.list_adapter.data = self.object_data

    def build(self):

        self.list_adapter = ListAdapter(data=self.string_data,
                                        cls=ListItemButton,
                                        selection_mode='single',
                                        allow_empty_selection=False,
                                        args_converter=self.strings_args_converter)

        self.dict_adapter = DictAdapter(data={k: {'key': k, 'value': k} for k in self.nato_alphabet_words},
                                        cls=KeyedListItemButton,
                                        selection_mode='single',
                                        allow_empty_selection=False,
                                        args_converter=self.dict_args_converter)

        for word in self.nato_alphabet_words:
            self.object_data.append(CustomDataItem(text=word))

        self._screen_manager = ScreenManager()

        self._screen_manager.add_widget(ItemsScreen(name="test_data_changes"))

        return self._screen_manager


if __name__ == '__main__':
    Test().run()
