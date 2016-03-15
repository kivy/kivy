# -*- coding: utf-8 -*-
from kivy.uix.listview import ListView
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.models import SelectableDataItem

from kivy.uix.listview import ListItemButton

import random


class DataItem(SelectableDataItem):
    def __init__(self, name, **kwargs):
        self.name = name
        super(DataItem, self).__init__(**kwargs)


class MainView(FloatLayout):
    """
    Implementation of a ListView using the kv language.
    """

    def __init__(self, **kwargs):
        super(MainView, self).__init__(**kwargs)

        data_items = []
        data_items.append(DataItem('One'))
        data_items.append(DataItem('Two'))
        data_items.append(DataItem('Three'))

        list_item_args_converter = lambda row_index, obj: {'text': obj.name,
                                                           'size_hint_y': None,
                                                           'height': 25}

        self.list_adapter = \
                ListAdapter(data=data_items,
                            args_converter=list_item_args_converter,
                            selection_mode='single',
                            propagate_selection_to_data=False,
                            allow_empty_selection=False,
                            cls=ListItemButton)

        self.list_view = ListView(adapter=self.list_adapter)

        self.add_widget(self.list_view)

        self.toggle = 'adding'

        Clock.schedule_interval(self.update_list_data, 1)

    def update_list_data(self, dt):
        items = self.list_adapter.data
        if self.toggle == 'adding':
            item = DataItem(name='New ' * random.randint(1, 2))
            items.append(item)
            self.toggle = 'changing'
            print('added ' + item.name)
        else:
            random_index = random.randint(0, len(items) - 1)
            item = items[random_index]
            items[random_index] = DataItem('Changed')
            self.toggle = 'adding'
            print('changed {0} to {1}'.format(item.name,
                                              items[random_index].name))


if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView(width=800))
