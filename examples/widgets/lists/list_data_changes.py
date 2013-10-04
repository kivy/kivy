#!/usr/bin/env python
# -*- coding: utf-8 -*-

from random import choice

from kivy.app import App
from kivy.lang import Builder
from kivy.logger import Logger
from random import sample

from kivy.binding import Binding
from kivy.controllers.listcontroller import ListController
from kivy.controllers.dictcontroller import DictController
from kivy.models import SelectableDataItem
from kivy.properties import DictProperty
from kivy.properties import ListProperty
from kivy.properties import StringProperty
from kivy.selection import SelectionTool
from kivy.uix.listview import ListItemButton
from kivy.uix.screenmanager import Screen
from kivy.uix.screenmanager import ScreenManager


###############
#  Data

class CustomDataItem(SelectableDataItem):

    def __init__(self, **kwargs):
        super(CustomDataItem, self).__init__(**kwargs)
        self.text = kwargs.get('text', '')

# Quote from ListView docs about data items: "They MUST be subclasses of
# SelectableDataItem, or the equivalent, because each data item needs an all
# important "Kivy selection" object, abbreviated **ksel** in internal coding.
# Without a ksel, a list item will not respond to user action, and will appear
# just as a dumb list item, along for the ride."

#######################
#  The Main Widget

Builder.load_string('''
#:import choice random.choice
#:import sample random.sample
#:import binding_modes kivy.enums.binding_modes
#:import DataBinding kivy.binding.DataBinding
#:import ListItemButton kivy.uix.listview.ListItemButton
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

            Label:
                pos_hint: {'center_x': .5}
                size_hint: None, None
                width: 200
                height: 30
                text: 'TEST OpObservableList'

            ListView:
                canvas:
                    Color:
                        rgba: .4, .4, .4, .4
                    Rectangle:
                        pos: self.pos
                        size: self.size
                list_item_class: 'ListItemButton'
                DataBinding:
                    source: app.list_controller

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
                    on_release: app.list_delslice()
    #
    # TODO: iadd and imul are getting a nonetype is not iterable error.
    # ROD object. So we will add labels instead of buttons for them for now.
    #
    #            Button:
    #                size_hint: None, None
    #                width:80
    #                height: 30
    #                text: 'iadd'
    #                on_release: app.list_controller.data += \
    #                        [choice(app.nato_alphabet_words)] * 3
    #
    #            Button:
    #                size_hint: None, None
    #                width:80
    #                height: 30
    #                text: 'imul'
    #                on_release: app.list_controller.data *= 2
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
                canvas:
                    Color:
                        rgba: .4, .4, .4, .4
                    Rectangle:
                        pos: self.pos
                        size: self.size
                list_item_class: 'ListItemButton'
                DataBinding:
                    source: app.dict_controller

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

    data_items = ListProperty([])
    data_dict = DictProperty([])

    def create_list_item_obj(self):
        return CustomDataItem(text=choice(self.nato_alphabet_words))

    def create_list_item_obj_list(self, n):
        return [CustomDataItem(text=choice(self.nato_alphabet_words))] * n

    def insert_into_dict(self, index):
        key = CustomDataItem(text=self.random_10())
        self.dict_controller.insert(index, key, CustomDataItem(text=self.random_10()))

    def random_10(self):
        return ''.join(sample('abcdefghijklmnopqrstuvwxyz', 10))

    def build(self):

        for word in self.nato_alphabet_words:
            self.data_items.append(CustomDataItem(text=word))
            self.data_dict[CustomDataItem(text=word)] = CustomDataItem(text=word)

        self.list_controller = ListController(
                data=self.data_items,
                selection_mode='single',
                allow_empty_selection=False)

        self.dict_controller = DictController(
                data=sorted(self.data_dict.keys()),
                data_dict=self.data_dict,
                selection_mode='single',
                allow_empty_selection=False)

        self._screen_manager = ScreenManager()

        self._screen_manager.add_widget(ItemsScreen(name="test_data_changes"))

        return self._screen_manager

    def new_item(self):
        return self.create_list_item_obj()

    def new_data(self, how_many):
        return self.create_list_item_obj_list(how_many)

    def list_setitem(self):
        sel_index = self.list_controller.data.index(self.list_controller.selection[0])

        self.list_controller.data[sel_index] = self.new_item()

    def list_delitem(self):
        sel_index = self.list_controller.data.index(self.list_controller.selection[0])
        del self.list_controller.data[sel_index]

    def list_setslice(self):
        sel_index = self.list_controller.data.index(self.list_controller.selection[0])

        self.list_controller.data[sel_index:sel_index + 3] = self.new_data(3)

    def list_delslice(self):
        sel_index = self.list_controller.data.index(self.list_controller.selection[0])

        del self.list_controller.data[sel_index:sel_index + 3]

    def list_append(self):
        self.list_controller.data.append(self.new_item())

    def list_remove(self):
        sel_index = self.list_controller.data.index(self.list_controller.selection[0])

        item = self.list_controller.data[sel_index]

        self.list_controller.data.remove(item)

    def list_insert(self):
        sel_index = self.list_controller.data.index(self.list_controller.selection[0])

        self.list_controller.data.insert(sel_index, self.new_item())

    def list_pop(self):
        self.list_controller.data.pop()

    def list_pop_i(self):
        sel_index = self.list_controller.data.index(self.list_controller.selection[0])

        self.list_controller.data.pop(sel_index)

    def list_extend(self):
        self.list_controller.data.extend(self.new_data(3))

    def list_sort(self):
        self.list_controller.data.sort(key=lambda obj: obj.text)

    def list_reverse(self):
        self.list_controller.data.reverse()

    def dict_setitem_set(self):
        sel_key = self.dict_controller.selection[0]

        if self.dict_controller.selection:
            self.dict_controller.data_dict[sel_key] = CustomDataItem(text=self.random_10())
        else:
            Logger.info('Testing: No selection. Cannot setitem set.')

    def dict_setitem_add(self):
        k = CustomDataItem(text=self.random_10())
        self.dict_controller.data_dict[k] = CustomDataItem(text=k)

    def dict_delitem(self):
        sel_index = self.dict_controller.data.index(self.dict_controller.selection[0])

        sel_key = self.dict_controller.data[sel_index]

        del self.dict_controller.data_dict[sel_key]

    def dict_clear(self):
        self.dict_controller.data_dict.clear()

    def dict_pop(self):
        sel_index = self.dict_controller.data.index(self.dict_controller.selection[0])

        sel_key = self.dict_controller.data[sel_index]

        if self.dict_controller.data_dict.keys():
            self.dict_controller.data_dict.pop(sel_key)
        else:
            Logger.info('Testing: Data is empty. Cannot pop.')

    def dict_popitem(self):
        if self.dict_controller.data_dict.keys():
            self.dict_controller.data_dict.popitem()
        else:
            Logger.info('Testing: Data is empty. Cannot popitem.')

    def dict_setdefault(self):
        k = CustomDataItem(text=self.random_10())
        self.dict_controller.data_dict.setdefault(k, CustomDataItem(text=k))

    def dict_update(self):
        k1 = CustomDataItem(text=self.random_10())
        k2 = CustomDataItem(text=self.random_10())
        k3 = CustomDataItem(text=self.random_10())

        self.dict_controller.data_dict.update(
                {k1: CustomDataItem(text=k1),
                 k2: CustomDataItem(text=k2),
                 k3: CustomDataItem(text=k3)})

    def dict_insert(self):
        sel_index = self.dict_controller.data.index(self.dict_controller.selection[0])
        self.insert_into_dict(sel_index)

    def dict_sort(self):
        self.dict_controller.data.sort(key=lambda k: k.text.lower())

if __name__ == '__main__':
    Test().run()

