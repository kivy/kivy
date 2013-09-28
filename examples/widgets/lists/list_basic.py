from kivy.binding import DataBinding
from kivy.controllers.listcontroller import ListController
from kivy.models import SelectableStringItem
from kivy.uix.listview import ListItemButton
from kivy.uix.listview import ListView
from kivy.uix.gridlayout import GridLayout


class MainView(GridLayout):

    def __init__(self, **kwargs):
        kwargs['cols'] = 1
        super(MainView, self).__init__(**kwargs)

        def list_item_class_args(index, data_item):
            return {'text': data_item.text,
                    'size_hint_y': None,
                    'height': 25}

        list_controller = ListController(
            data=[SelectableStringItem(text=str(index))
                      for index in range(100)],
            selection_mode='single',
            allow_empty_selection=False)

        list_view = ListView(
            data_binding=DataBinding(
                source=list_controller),
            args_converter=list_item_class_args,
            list_item_class=ListItemButton)

        self.add_widget(list_view)

if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView(width=800))

##############################################################################
# You can use a function for the args_converter, as shown above, or you can
# use a Python lambda, which also is a function, but some prefer it:
#
#        list_item_class_args = \
#                lambda index, data_item: {'text': data_item.text,
#                                          'size_hint_y': None,
#                                          'height': 25}
