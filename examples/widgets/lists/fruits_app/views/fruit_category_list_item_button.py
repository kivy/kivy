from kivy.lang import Builder
from kivy.uix.listview import ListItemButton


Builder.load_string("""

# This is not a dynamic class. See list_cascade.py for the same view made as a
# dynamic class. We need python imports to work for the file system definitions
# of widgets used here.

<FruitCategoryListItemButton>:
    size_hint_y: None
    height: 25
    args_converter: lambda index, data_item: {'text': data_item.name}
""")


class FruitCategoryListItemButton(ListItemButton):
    pass
