from kivy.lang import Builder
from kivy.uix.label import Label


Builder.load_string("""

# This is not a dynamic class. See list_cascade.py for the same view made as a
# dynamic class. We need python imports to work for the file system definitions
# of widgets used here.

<AttributeValueLabel>:
    size_hint_y: None
    height: 50
    halign: 'right'
""")


class AttributeValueLabel(Label):
    pass
