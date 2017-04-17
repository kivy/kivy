from kivy.adapters.dictadapter import DictAdapter
from kivy.properties import NumericProperty, AliasProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget


class OpsDictAdapter(DictAdapter):

    listview_id = NumericProperty(0)
    owning_view = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.listview_id = kwargs['listview_id']
        super(OpsDictAdapter, self).__init__(**kwargs)

    def on_selection_change(self, *args):
        for i in range(len(self.selection)):
            listview_selection_buttons[self.listview_id][i].text = \
                    self.selection[i].text

        if self.listview_id is 0:
            # Scroll to the most recently selected item.
            if len(self.selection) > 0:
                print('selection', self.selection)
                self.owning_view.scroll_to(
                    index=self.sorted_keys.index(self.selection[-1].text))

        elif self.listview_id is 1:
            # Scroll to the selected item that is the minimum of a sort.
            if len(self.selection) > 0:
                self.owning_view.scroll_to(
                    index=self.sorted_keys.index(
                        sorted([sel.text for sel in self.selection])[0]))

        elif self.listview_id is 2:
            # Scroll to the selected item that is the maximum of a sort.
            if len(self.selection) > 0:
                self.owning_view.scroll_to(
                    index=self.sorted_keys.index(
                        sorted([sel.text for sel in self.selection])[-1]))


class SelectionMonitor(Widget):

    def get_count_string(self):
        return "Total sel: " + str(self.sel_count_0 +
                                   self.sel_count_1 +
                                   self.sel_count_2 +
                                   self.sel_count_3 +
                                   self.sel_count_4 +
                                   self.sel_count_5 +
                                   self.sel_count_6)

    def set_count_string(self, value):
        self.count_string = value

    sel_count_0 = NumericProperty(0)
    sel_count_1 = NumericProperty(0)
    sel_count_2 = NumericProperty(0)
    sel_count_3 = NumericProperty(0)
    sel_count_4 = NumericProperty(0)
    sel_count_5 = NumericProperty(0)
    sel_count_6 = NumericProperty(0)

    count_string = AliasProperty(get_count_string,
                                 set_count_string,
                                 bind=('sel_count_0',
                                       'sel_count_1',
                                       'sel_count_2',
                                       'sel_count_3',
                                       'sel_count_4',
                                       'sel_count_5',
                                       'sel_count_6'))

    def __init__(self, **kwargs):
        super(SelectionMonitor, self).__init__(**kwargs)

    def update_sel_count_0(self, adapter, *args):
        self.sel_count_0 = len(adapter.selection)

    def update_sel_count_1(self, adapter, *args):
        self.sel_count_1 = len(adapter.selection)

    def update_sel_count_2(self, adapter, *args):
        self.sel_count_2 = len(adapter.selection)

    def update_sel_count_3(self, adapter, *args):
        self.sel_count_3 = len(adapter.selection)

    def update_sel_count_4(self, adapter, *args):
        self.sel_count_4 = len(adapter.selection)

    def update_sel_count_5(self, adapter, *args):
        self.sel_count_5 = len(adapter.selection)

    def update_sel_count_6(self, adapter, *args):
        self.sel_count_6 = len(adapter.selection)


letters_dict = {
    l: {'text': l, 'is_selected': False} for l in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}

listview_selection_buttons = {}


class OpsView(BoxLayout):
    '''Seven list views are shown at the bottom, each focusing on one of the
    available operations for collection adapters: scroll_to, trim_to_sel,
    trim_left_of_sel, etc. At the top is a display that shows individual
    items selected across the seven lists, along with a total of all selected
    items for the lists.
    '''
    def __init__(self, **kwargs):
        kwargs['orientation'] = 'vertical'
        super(OpsView, self).__init__(**kwargs)

        # UPPER PANEL
        #
        # Create an upper panel with labels for items selected in the
        # listviews shown in the lower panel.
        #
        upper_panel = BoxLayout()

        grid_layout = GridLayout(cols=1,
                                 row_force_default=True,
                                 row_default_height=40)

        # On the left side of the upper panel, show the selected items. There
        # is a total possible of 5 for each listview, so 5 buttons are made.
        #
        for listview_id in range(7):
            box_layout = BoxLayout()
            listview_selection_buttons[listview_id] = []

            box_layout.add_widget(
                    Label(text="Listview #{0} selection".format(listview_id)))

            for i in range(5):
                button = Button(size_hint_x=None, width=50,
                                size_hint_y=None, height=35,
                                background_color=[.25, .25, .6, 1.0])
                listview_selection_buttons[listview_id].append(button)
                box_layout.add_widget(button)

            grid_layout.add_widget(box_layout)

        upper_panel.add_widget(grid_layout)

        # On the right side of the upper panel, show the total selected count.

        total_selection_button = Button(text="Total: 0",
                                        size_hint=(.5, 1.0),
                                        background_color=[.25, .25, .6, 1.0])
        selection_monitor = SelectionMonitor()
        selection_monitor.bind(
            count_string=total_selection_button.setter('text'))

        upper_panel.add_widget(total_selection_button)

        self.add_widget(upper_panel)

        # LOWER PANEL
        #
        # Show 6 listviews with either a header label or a header button.
        #
        grid_layout = GridLayout(cols=7)

        list_item_args_converter = \
                lambda row_index, rec: {'text': rec['text'],
                                        'size_hint_y': None,
                                        'height': 25}

        letters = [l for l in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']

        adapters = []

        # Create 7 listviews, limiting selection to 5 items for the first 3,
        # and allowing unlimited selection for the others, by setting the
        # selection limit to 1000.
        #
        # Use OpsDictAdapter, from above, which will post selections to
        # the display in the top panel.
        #
        listview_header_widgets = [Label(text="scroll_to rec",
                                         size_hint_y=None,
                                         height=25),
                                   Label(text="scroll_to min",
                                         size_hint_y=None,
                                         height=25),
                                   Label(text="scroll_to max",
                                         size_hint_y=None,
                                         height=25),
                                   Button(text="trim_left_of_sel",
                                          size_hint_y=None,
                                          height=25),
                                   Button(text="trim_right_of_sel",
                                          size_hint_y=None,
                                          height=25),
                                   Button(text="trim_to_sel",
                                          size_hint_y=None,
                                          height=25),
                                   Button(text="cut_to_sel",
                                          size_hint_y=None,
                                          height=25)]

        for listview_id in range(7):

            box_layout = BoxLayout(orientation='vertical')

            letters_dict_adapter = \
                    OpsDictAdapter(
                        listview_id=listview_id,
                        sorted_keys=letters[:],
                        data=letters_dict,
                        args_converter=list_item_args_converter,
                        selection_mode='multiple',
                        selection_limit=5 if listview_id < 3 else 1000,
                        allow_empty_selection=True,
                        cls=ListItemButton)

            adapters.append(letters_dict_adapter)

            letters_list_view = ListView(adapter=letters_dict_adapter)

            letters_dict_adapter.owning_view = letters_list_view

            box_layout.add_widget(listview_header_widgets[listview_id])
            box_layout.add_widget(letters_list_view)

            grid_layout.add_widget(box_layout)

        # Bind selection of each list to the selection monitor.
        adapters[0].bind(selection=selection_monitor.update_sel_count_0)
        adapters[1].bind(selection=selection_monitor.update_sel_count_1)
        adapters[2].bind(selection=selection_monitor.update_sel_count_2)
        adapters[3].bind(selection=selection_monitor.update_sel_count_3)
        adapters[4].bind(selection=selection_monitor.update_sel_count_4)
        adapters[5].bind(selection=selection_monitor.update_sel_count_5)
        adapters[6].bind(selection=selection_monitor.update_sel_count_6)

        # For the last three listviews, bind the header buttons to the trim
        # op method in the associated dict adapter instance.
        button_3 = listview_header_widgets[3]
        button_4 = listview_header_widgets[4]
        button_5 = listview_header_widgets[5]
        button_6 = listview_header_widgets[6]
        button_3.bind(on_release=adapters[3].trim_left_of_sel)
        button_4.bind(on_release=adapters[4].trim_right_of_sel)
        button_5.bind(on_release=adapters[5].trim_to_sel)
        button_6.bind(on_release=adapters[6].cut_to_sel)

        self.add_widget(grid_layout)


if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(OpsView(width=800))
