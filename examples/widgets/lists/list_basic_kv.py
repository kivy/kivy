from kivy.app import App
from kivy.binding import DataBinding
from kivy.controllers.listcontroller import ListController
from kivy.lang import Builder
from kivy.models import SelectableStringItem
from kivy.uix.gridlayout import GridLayout

Builder.load_string("""
#:import DataBinding kivy.binding.DataBinding
#:import binding_modes kivy.enums.binding_modes
#:import ListItemButton kivy.uix.listview.ListItemButton

<MainView>:
    cols: 1

    ListView:
        list_item_class: 'ListItemButton'
        args_converter: app.list_item_class_args
        DataBinding:
            source: app.list_controller
""")


class MainView(GridLayout):
    pass


class BasicApp(App):

    def __init__(self, **kwargs):
        super(BasicApp, self).__init__(**kwargs)

        self.list_controller = ListController(
            data=[SelectableStringItem(text=str(index))
                      for index in range(100)],
            selection_mode='single',
            allow_empty_selection=False)

    def list_item_class_args(self, index, data_item):
        return {'text': data_item.text,
                'size_hint_y': None,
                'height': 25}

    def build(self):
        return MainView(width=800)

if __name__ == '__main__':
    BasicApp().run()

##############################################################################
# You can use a function for the args_converter, as shown above, or you can
# use a Python lambda, which also is a function, but some prefer it:
#
#        list_item_class_args = \
#                lambda index, data_item: {'text': data_item.text,
#                                          'size_hint_y': None,
#                                          'height': 25}
