from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.listview import SelectableView


Builder.load_string("""

# This is not a dynamic class. See list_cascade.py for the same view made as a
# dynamic class. We need python imports to work for the file system definitions
# of widgets used here.

# Note the use of ../ in the path for the fruit images. In a real app, the
# images would be in a fruit_images directory within the app, but here, for the
# examples, we point to the ones up in the examples directory to avoid
# duplicating them.

<FruitListItem@SelectableView+BoxLayout>:
    index: self.index
    text: self.text
    size_hint_y: None
    height: 25
    args_converter: lambda index, data_item: {'text': data_item.name}
    Image
        source: "../fruit_images/{0}.32.jpg".format(root.text) if root.text else ''
    ListItemButton:
        index: root.index
        text: root.text if root.text else ''
        on_release: self.parent.trigger_action(duration=0)
""")


class FruitListItem(SelectableView, BoxLayout):
    pass
