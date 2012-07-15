__all__ = ('AbstractView', )

from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty, DictProperty


class AbstractView(FloatLayout):
    '''View using an Adapter as a data provider
    '''

    adapter = ObjectProperty(None)

    item_view_instances = DictProperty({})

    def set_item_view(self, index, item_view):
        pass

    def get_item_view(self, index):
        item_view_instances = self.item_view_instances
        if index in item_view_instances:
            return item_view_instances[index]
        item_view = self.adapter.get_view(index)
        if item_view:
            item_view_instances[index] = item_view
        return item_view
