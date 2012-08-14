from kivy.adapters.objectadapter import ObjectAdapter
from kivy.adapters.dictadapter import DictAdapter
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.uix.observerview import ObserverView

from fixtures import fruit_data

from fruit_detail_view import FruitObserverDetailView


class OOView(GridLayout):
    '''What is oo, you say?

         ...  An example featuring ObserverView and ObjectAdapter

              There is a list view on the left showing fruits, and on the
              right is an ObserverView(ObjectAdapter) that shows a detail
              view of the selected fruit. Compare to the list_cascade.py
              example that uses a custom detail view on the right.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 3
        kwargs['size_hint'] = (1.0, 1.0)
        super(OOView, self).__init__(**kwargs)

        list_item_args_converter = lambda rec: {'text': rec['name'],
                                                'size_hint_y': None,
                                                'height': 25}

        fruits_list_adapter = \
                DictAdapter(
                    sorted_keys=sorted(fruit_data.keys()),
                    data=fruit_data,
                    args_converter=list_item_args_converter,
                    selection_mode='single',
                    allow_empty_selection=False,
                    cls=ListItemButton)

        fruits_list_view = \
                ListView(adapter=fruits_list_adapter,
                    size_hint=(.2, 1.0))

        self.add_widget(fruits_list_view)

        # For the fruit detail view on the right, this is ObserverView, which
        # is tied to an ObjectAdapter instance's obj value. The observed obj
        # is used as the key to updating the fruit detail view on the right.
        #
        # Note the use of the obj_bind_from argument, offering a convenient
        # alternative to the scheme of manually setting up a required binding
        # post-instantiation. This way the ObjectAdapter sets up the binding.
        #
        # The view creation and use of args_converter and either a cls or
        # template works the same as for ListAdapter.
        #
        fruit_detail_view = ObserverView(adapter=ObjectAdapter(
                obj_bind_from=fruits_list_adapter,
                args_converter=lambda x: {'fruit_name': str(x),
                                          'size_hint': (.6, 1.0)},
                cls=FruitObserverDetailView))

        self.add_widget(fruit_detail_view)

        # Force triggering of on_selection_change() for the DetailView, for
        # correct initial display.
        fruits_list_adapter.touch_selection()


if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(OOView(width=800))
