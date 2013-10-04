from kivy.app import App
from kivy.binding import DataBinding
from kivy.binding import SelectionBinding
from kivy.controllers.listcontroller import ListController
from kivy.models import SelectableDataItem
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView
from kivy.uix.listview import ListItemButton

from fixtures import fruit_data_list_of_dicts


##############################################################################
#
#    Data
#
#        Data items must have a ksel object, which is a Kivy Selection object
#        used to tie selection of individual items to the selection machinery
#        of ListView and other similar views. Subclass SelectableDataItem for
#        an easy way to get this functionality. Note that self.data here is
#        in internal scope within FruitItem, and should not to be confused
#        with the formal data property of controllers.

class FruitItem(SelectableDataItem):
    def __init__(self, **kwargs):
        super(FruitItem, self).__init__(**kwargs)
        self.text = kwargs.get('name', '')
        self.serving_size = kwargs.get('Serving Size', '')
        self.data = kwargs.get('data', [])

# Quote from ListView docs about data items: "They MUST be subclasses of
# SelectableDataItem, or the equivalent, because each data item needs an all
# important "Kivy selection" object, abbreviated **ksel** in internal coding.
# Without a ksel, a list item will not respond to user action, and will appear
# just as a dumb list item, along for the ride."


######################
#  The Main Widget

class SelectionBindingView(GridLayout):
    '''Implementation of a two-list widget, with a scrollable list of fruits
    on the left and a list on the right that shows items selected in the
    first list. It illustrates multiple selection in the left list and binding
    to a custom dict adapter.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        super(SelectionBindingView, self).__init__(**kwargs)

        app = App.app()

        self.add_widget(ListView(
                data_binding=DataBinding(
                    source=app.fruits_controller),
                list_item_class=ListItemButton,
                size_hint=(.5, 1.0)))

        # The second list, on the right, will accumulate items selected in the
        # first, and will reflect selection in the first list, even for
        # deselection, reselection.
        self.add_widget(ListView(
                data_binding=DataBinding(
                    source=app.selected_fruits_controller),
                list_item_class=ListItemButton,
                size_hint=(.5, 1.0)))


class SelectionBindingApp(App):

    def __init__(self, **kwargs):
        super(SelectionBindingApp, self).__init__(**kwargs)

        self.fruits_controller = ListController(
            selection_mode='multiple',
            allow_empty_selection=False)

        self.selected_fruits_controller = ListController(
            data_binding=DataBinding(
                source=self.fruits_controller,
                prop='selection'),
            selection_binding=SelectionBinding(
                source=self.fruits_controller,
                prop='selection'),
            selection_mode='multiple',
            allow_empty_selection=False)

    def build(self):
        return SelectionBindingView(width=800)

    def on_start(self):

        # Load data into controllers. Put some thinking into when you want or
        # need to load data into controllers. Here we illustrate how the app
        # can be initialized with empty controllers, only to be filled later,
        # in this case on app start up.

        # fruit_data_list_of_dicts is a list of dicts, already sorted.
        self.fruits_controller.data = \
            [FruitItem(**fruit_dict) for fruit_dict in fruit_data_list_of_dicts]


if __name__ in ('__main__'):
    SelectionBindingApp().run()
