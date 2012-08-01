from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

Builder.load_string('''
[CustomListItem@BoxLayout]:
    size_hint_y: ctx.size_hint_y
    height: ctx.height
    Button:
        text: ctx.text
''')


class MainView(GridLayout):
    '''Implementation of a list view with a kv template used for the list
    item class.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 1
        kwargs['size_hint'] = (1.0, 1.0)
        super(MainView, self).__init__(**kwargs)

        # Here we create a list adapter with some item strings, passing our
        # CompositeListItemTemplate for the list item view, and then we create
        # a list view using this adapter:
        list_adapter = ListAdapter(data=[str(i) for i in xrange(100)],
                                   template='CustomListItem')
        list_view = ListView(adapter=list_adapter)

        self.add_widget(list_view)


if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(MainView(width=800))
