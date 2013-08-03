#!/usr/bin/env python
# -*- coding: utf-8 -*-

from random import choice

from kivy.app import App
from kivy.lang import Builder
from random import sample

from kivy.adapters.models import SelectableDataItem
from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.dictadapter import DictAdapter

from kivy.properties import ListProperty
from kivy.properties import StringProperty

from kivy.uix.listview import ListItemButton
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
                on_release: app.list_load_with_string_data()

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
                text: 'TEST OpObservableList'

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
                    on_release: app.list_setitem()

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'delitem'
                    on_release: app.list_delitem()

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'setslice (3)'
                    on_release: app.list_setslice()

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'delslice (3)'
                    on_release: app.list_setslice()
    #
    # TODO: iadd and imul are getting a nonetype is not iterable error.
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
                    on_release: app.list_append()

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'remove'
                    on_release: app.list_remove()

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'insert'
                    on_release: app.list_insert()

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'pop()'
                    on_release: app.list_pop()

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'pop(i)'
                    on_release: app.list_pop_i()

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'extend (3)'
                    on_release: app.list_extend()

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'sort'
                    on_release: app.list_sort()

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'reverse'
                    on_release: app.list_reverse()

        BoxLayout:
            orientation: 'vertical'
            padding: 3
            spacing: 5

            Label:
                pos_hint: {'center_x': .5}
                size_hint: None, None
                width: 200
                height: 30
                text: 'TEST OpObservableDict'

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
                    on_release: app.dict_setitem_set()

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'setitem add'
                    on_release: app.dict_setitem_add()

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'delitem'
                    on_release: app.dict_delitem()

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'clear'
                    on_release: app.dict_clear()

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'pop'
                    on_release: app.dict_pop()

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'popitem'
                    on_release: app.dict_popitem()

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'setdefault'
                    on_release: app.dict_setdefault()

                Button:
                    size_hint: None, None
                    width: 96
                    height: 30
                    text: 'update (3)'
                    on_release: app.dict_update()

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'insert'
                    on_release: app.dict_insert()

                Button:
                    size_hint: None, None
                    width:80
                    height: 30
                    text: 'sort'
                    on_release: app.dict_sort()
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
                "height": 25}

    def objects_args_converter(self, row_index, obj):
        print row_index, obj
        return {"text": obj.text,
                "size_hint_y": None,
                "height": 25}

    def data_is_strings(self):
        if self.list_adapter.args_converter == self.strings_args_converter:
            return True
        return False

    def dict_args_converter(self, row_index, rec):
        return {"text": "{0} : {1}".format(rec['key'], rec['value']),
                "key": rec['key'],
                "size_hint_y": None,
                "height": 25}

    def insert_into_dict(self, index):
        key = self.random_10()
        self.dict_adapter.insert(index, key, {'key': key, 'value': key})

    def set_object_data(self):
        self.list_adapter.args_converter = self.objects_args_converter
        self.list_adapter.data = self.object_data

    def random_10(self):
        return ''.join(sample('abcdefghijklmnopqrstuvwxyz', 10))

    def alphabet_dict(self):
        return {k: {'key': k, 'value': k} for k in self.nato_alphabet_words}

    def build(self):

        self.list_adapter = ListAdapter(
                data=self.string_data,
                cls=ListItemButton,
                selection_mode='single',
                allow_empty_selection=False,
                args_converter=self.strings_args_converter)

        self.dict_adapter = DictAdapter(
                data=self.alphabet_dict(),
                cls=KeyedListItemButton,
                selection_mode='single',
                allow_empty_selection=False,
                args_converter=self.dict_args_converter)

        for word in self.nato_alphabet_words:
            self.object_data.append(CustomDataItem(text=word))

        self._screen_manager = ScreenManager()

        self._screen_manager.add_widget(ItemsScreen(name="test_data_changes"))

        return self._screen_manager

    def list_load_with_string_data(self):
        self.list_adapter.args_converter = self.strings_args_converter
        del self.list_adapter.data[0:len(self.list_adapter.data)]
        [self.list_adapter.data.append(s) for s in self.string_data]

    def new_item(self):
        if self.data_is_strings():
            return choice(self.nato_alphabet_words)
        else:
            return self.create_list_item_obj()

    def new_data(self, how_many):
        if self.data_is_strings():
            return [choice(self.nato_alphabet_words)] * how_many
        else:
            return self.create_list_item_obj_list(how_many)

    def list_setitem(self):
        sel_index = self.list_adapter.selection[0].index

        self.list_adapter.data[sel_index] = self.new_item()

    def list_delitem(self):
        del self.list_adapter.data[self.list_adapter.selection[0].index]

    def list_setslice(self):
        sel_index = self.list_adapter.selection[0].index

        self.list_adapter.data[sel_index:sel_index + 3] = self.new_data(3)

    def list_delslice(self):
        sel_index = self.list_adapter.selection[0].index

        del self.list_adapter.data[sel_index:sel_index + 3]

    def list_append(self):
        self.list_adapter.data.append(self.new_item())

    def list_remove(self):
        sel_index = self.list_adapter.selection[0].index

        item = self.list_adapter.data[sel_index]

        self.list_adapter.data.remove(item)

    def list_insert(self):
        sel_index = self.list_adapter.selection[0].index

        self.list_adapter.data.insert(sel_index, self.new_item())

    def list_pop(self):
        self.list_adapter.data.pop()

    def list_pop_i(self):
        sel_index = self.list_adapter.selection[0].index

        self.list_adapter.data.pop(sel_index)

    def list_extend(self):
        self.list_adapter.data.extend(self.new_data(3))

    def list_sort(self):
        if self.data_is_strings():
            self.list_adapter.data.sort()
        else:
            self.list_adapter.data.sort(key=lambda obj: obj.text)

    def list_reverse(self):
        self.list_adapter.data.reverse()

    def dict_setitem_set(self):
        sel_key = self.dict_adapter.selection[0].key

        if self.dict_adapter.selection:
            new_item = {'key': sel_key, 'value': self.random_10()}
            self.dict_adapter.data[sel_key] = new_item
        else:
            Logger.info('Testing: No selection. Cannot setitem set.')

    def dict_setitem_add(self):
        k = self.random_10()
        self.dict_adapter.data[k] = {'key': k, 'value': k}

    def dict_delitem(self):
        sel_index = self.dict_adapter.selection[0].index

        sel_key = self.dict_adapter.sorted_keys[sel_index]

        del self.dict_adapter.data[sel_key]

    def dict_clear(self):
        self.dict_adapter.data.clear()

    def dict_pop(self):
        sel_index = self.dict_adapter.selection[0].index

        sel_key = self.dict_adapter.sorted_keys[sel_index]

        if self.dict_adapter.data.keys():
            self.dict_adapter.data.pop(sel_key)
        else:
            Logger.info('Testing: Data is empty. Cannot pop.')

    def dict_popitem(self):
        if self.dict_adapter.data.keys():
            self.dict_adapter.data.popitem()
        else:
            Logger.info('Testing: Data is empty. Cannot popitem.')

    def dict_setdefault(self):
        k = self.random_10()
        self.dict_adapter.data.setdefault(k, {'key': k, 'value': k})

    def dict_update(self):
        k1 = self.random_10()
        k2 = self.random_10()
        k3 = self.random_10()

        self.dict_adapter.data.update({k1: {'key': k1, 'value': k1},
                                       k2: {'key': k2, 'value': k2},
                                       k3: {'key': k3, 'value': k3}})

    def dict_insert(self):
        self.insert_into_dict(self.dict_adapter.selection[0].index)

    def dict_sort(self):
        self.dict_adapter.sorted_keys.sort(key=lambda k: k.lower())

if __name__ == '__main__':
    Test().run()
