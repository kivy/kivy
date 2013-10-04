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

    def build(self):
        return MainView(width=800)

if __name__ == '__main__':
    BasicApp().run()
