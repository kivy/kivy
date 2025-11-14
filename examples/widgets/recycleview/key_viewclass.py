"""
A form generator, using random data, but can be data driven (json or whatever)

Demonstrates the use of the key_viewclass attribute of RecycleView to select a
different Widget for each item.  The key_viewclass specifies the key to use in
the RecycleView.data list dict that holds the widget class to use for that item.

The `key_viewclass` attribute in Kivy's RecycleView allows you to
have multiple types of widgets in the same RecycleView.
You specify, on a per-item basis, what kind of widget is used for that
individual item.  In the example below, the widget classes are:
RVTextInputLine, RVCheckBoxLine, RVSpinnerLine.  This makes the RecycleView
highly flexible for heterogeneous data displays.

In the example the static data for each of the widgets is stored in the
RecycleView.data list.

Every time a widget is visible in the view, the visible widget will
apply the list of attributes from the items in the data list, to that
widget.  Of course, the binding applies, so keeping a selected state
in the widget doesn't work.

You want the (recycled) widget to be set/reset when the widget is used
for another data item so you have to save that selected state outside
of the widget. One possible solution is to edit the items in
data(the RecycleView data attribute), but that could trigger new
dispatches and so reset which widgets displays which items, and cause trouble.

The preferred solution is to save the widget state to a different list
property, and just make the widget lookup that property when the
widget's key is updated.

The method get_active_value() is used to get the active value for the widget
at a given index, or a default if the index is not yet set by RecycleView.
The default value for index is -1, which is used to indicate that the index
is not yet set by RecycleView.  The App.handle_update() method is used to
update the active values for each widget, writing the data back to the
active_values list.
"""

from random import choice, choices
from string import ascii_lowercase

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import (BooleanProperty, ListProperty,
                             NumericProperty, StringProperty)

KV = '''
<NumberedLabel>:  # a RelativeLayout
    BoxLayout:
        size_hint_x: None
        width: self.minimum_width
        pos_hint: {'center_x': 0.5}
        spacing: '5dp'
        Label:
            text: str(root.index)
            size_hint_x: None
            width: '30dp'
            text_size: self.size
            halign: 'right'
            valign: 'middle'
        Label:
            text: root.title
            size_hint_x: None
            width: '100dp'
            text_size: self.size
            halign: 'left'
            valign: 'middle'

<RVTextInputLine>:
    NumberedLabel:
        index: root.index
        title: root.title
    TextInput:
        text: app.get_active_value(root.index, '')
        on_text: app.handle_update(self.text, root.index)
        multiline: False

<RVCheckBoxLine>:
    NumberedLabel:
        index: root.index
        title: root.title
    CheckBox:
        active: app.get_active_value(root.index, False)
        on_active: app.handle_update(self.active, root.index)

<RVSpinnerLine>:
    NumberedLabel:
        index: root.index
        title: root.title
    Spinner:
        text: app.get_active_value(root.index, 'One')
        values: ['One', 'Two', 'Three', 'Four', 'Five']
        on_text: app.handle_update(self.text, root.index)

BoxLayout:
    orientation: 'vertical'
    BoxLayout:
        size_hint_y: None
        height: '30dp'
        Label:
            text: 'Title'
        Label:
            text: 'Widget'
    RecycleView:
        id: rv
        data: app.data
        key_viewclass: 'widget'
        RecycleBoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            default_size_hint: 1, None
            default_height: dp(48)  # Default height for each line
'''


class NumberedLabel(RelativeLayout):
    index = NumericProperty(-1)  # -1 to indicate not yet set by RecycleView
    title = StringProperty()


class RVTextInputLine(BoxLayout):
    value = StringProperty()
    index = NumericProperty(-1)  # -1 to indicate not yet set by RecycleView
    title = StringProperty()


class RVCheckBoxLine(BoxLayout):
    value = BooleanProperty()
    index = NumericProperty(-1)  # -1 to indicate not yet set by RecycleView
    title = StringProperty()


class RVSpinnerLine(BoxLayout):
    value = StringProperty()
    index = NumericProperty(-1)  # -1 to indicate not yet set by RecycleView
    title = StringProperty()


class Application(App):
    """
    A form manager demonstrating the power of RecycleView's key_viewclass
    property.
    """
    data = ListProperty()  # a copy of the RecycleView.data list
    active_values = ListProperty()  # a list of the active values of the widgets

    def build(self):
        # create 200 lines, randomly selecting the widget type
        self.data = [self.create_random_input(index)
                     for index in range(200)]
        self.initialize_active_values()
        return Builder.load_string(KV)

    def initialize_active_values(self):
        """
        Initialize the active_values list to the same length as the data list.
        The active_values list is used to store the active state of the
        widgets. Create a random value, based on the widget type, for each
        index in the data list.
        """
        self.active_values = [None] * len(self.data)
        for idx, d in enumerate(self.data):
            if d['widget'] == 'RVTextInputLine':
                self.active_values[idx] = ''.join(
                    choices(ascii_lowercase, k=10))
            elif d['widget'] == 'RVCheckBoxLine':
                self.active_values[idx] = choice((True, False))
            elif d['widget'] == 'RVSpinnerLine':
                # Use a valid value from the spinner's values list
                self.active_values[idx] = choice(
                    ['One', 'Two', 'Three', 'Four', 'Five'])

    def get_active_value(self, index, default=None):
        """
        Returns the active value for the widget at a given index, or a default
        if the index is not yet set by RecycleView (index < 0).
        """
        # Check if index is the sentinel value (-1) indicating it
        # hasn't been set by RecycleView yet
        if index < 0:
            return default
        return self.active_values[index]

    def handle_update(self, value, index):
        """
        Called when the value of a widget is changed.
        The index is the index of the widget in the RecycleView.data list.
        Writes the updated value to the active_values list.
        """
        self.active_values[index] = value

    def create_random_input(self, index):
        """
        returns a function that creates a dictionary of data for a
        textinput, checkbox, or spinner.  The function is chosen randomly from
        the list of functions.
        """
        return choice((
            self.create_textinput,
            self.create_checkbox,
            self.create_spinner
        ))(index)

    def create_spinner(self, index):
        """
        create a dict of data for a spinner
        """
        return {
            'index': index,
            'title': 'Spinner',
            'widget': 'RVSpinnerLine',
        }

    def create_checkbox(self, index):
        """
        create a dict of data for a checkbox
        """
        return {
            'index': index,
            'title': 'Checkbox',
            'widget': 'RVCheckBoxLine',
        }

    def create_textinput(self, index):
        """
        create a dict of data for a textinput
        """
        return {
            'index': index,
            'title': 'TextInput',
            'widget': 'RVTextInputLine',
        }


if __name__ == "__main__":
    Application().run()
