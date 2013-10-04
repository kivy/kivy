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

        list_controller = ListController(
            data=[SelectableStringItem(text=str(index))
                      for index in range(100)],
            selection_mode='single',
            allow_empty_selection=False)

        list_view = ListView(
            data_binding=DataBinding(
                source=list_controller),
            list_item_class=ListItemButton)

        self.add_widget(list_view)

if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView(width=800))
