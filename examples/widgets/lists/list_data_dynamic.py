# -*- coding: utf-8 -*-
from random import choice
from string import ascii_uppercase, digits

import random

from kivy.binding import DataBinding
from kivy.controllers.listcontroller import ListController
from kivy.clock import Clock
from kivy.enums import selection_schemes
from kivy.models import SelectableDataItem

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.listview import ListItemButton
from kivy.uix.listview import ListView


##############
#  Data

class DataItem(SelectableDataItem):
    def __init__(self, **kwargs):
        super(DataItem, self).__init__(**kwargs)
        self.name = ''.join(choice(ascii_uppercase + digits) for x in range(6))

# Quote from ListView docs about data items: "They MUST be subclasses of
# SelectableDataItem, or the equivalent, because each data item needs an all
# important "Kivy selection" object, abbreviated **ksel** in internal coding.
# Without a ksel, a list item will not respond to user action, and will appear
# just as a dumb list item, along for the ride."

#####################
#  The Main Widget

# In this example, we are taking a pure-python approach for everything. See
# other examples for use of the kv language.

class MainView(FloatLayout):

    def __init__(self, **kwargs):
        super(MainView, self).__init__(**kwargs)

        data_items = []
        data_items.append(DataItem())
        data_items.append(DataItem())
        data_items.append(DataItem())

        list_item_class_args = lambda row_index, obj: {'text': obj.name,
                                                           'size_hint_y': None,
                                                           'height': 25}

        self.list_controller = ListController(
                data=data_items,
                selection_mode='single',
                allow_empty_selection=False)

        self.list_view = ListView(
                data_binding=DataBinding(source=self.list_controller),
                args_converter=list_item_class_args,
                list_item_class=ListItemButton)

        self.add_widget(self.list_view)

        self.toggle = 'adding'

        Clock.schedule_interval(self.update_list_data, 1)

    def update_list_data(self, dt):
        items = self.list_controller.data
        if self.toggle == 'adding':
            item = DataItem(name='New ' * random.randint(1, 2))
            items.append(item)
            self.toggle = 'changing'
            print('added ' + item.name)
        else:
            random_index = random.randint(0, len(items) - 1)
            item = items[random_index]
            items[random_index] = DataItem()
            self.toggle = 'adding'
            print('changed {0} to {1}'.format(item.name,
                                              items[random_index].name))


if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView(width=800))
