"""
Nested Parallel Vertical ScrollView Demo
==================================================
Demonstrating nested ScrollViews with parallel scrolling using KV language.
Nested Parallel Vertical Scrolling, both outer and inner ScrollViews scroll
vertically.

"""

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import NumericProperty

# KV string defining the layout structure
kv = '''
<InnerPanel>:
    orientation: 'vertical'
    size_hint_y: None
    height: dp(260)

    # Header row
    BoxLayout:
        size_hint_y: None
        height: dp(44)
        padding: dp(12), 0

        Label:
            text: f'Panel {root.panel_index + 1}'
            bold: True

        Label:
            text: 'Vertical inner scroll below'
            color: 0.8, 0.8, 0.8, 1

    # Inner vertical scroll - centered with spacers
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: dp(200)

        Label:  # Left spacer

        ScrollView:
            id: inner_scroll
            do_scroll_x: False
            do_scroll_y: True
            bar_width: dp(6)
            scroll_type: ['bars', 'content']
            size_hint_y: None
            size_hint_x: None
            height: dp(200)

            BoxLayout:
                id: content
                orientation: 'vertical'
                size_hint: None, None
                size: self.minimum_width, self.minimum_height
                padding: dp(8)
                spacing: dp(6)

        Label:  # Right spacer

# Main layout
ScrollView:
    do_scroll_x: False
    do_scroll_y: True
    bar_width: dp(8)
    scroll_type: ['bars', 'content']

    BoxLayout:
        id: outer_layout
        orientation: 'vertical'
        size_hint_y: None
        height: self.minimum_height
        padding: dp(12)
        spacing: dp(12)

        # Info label at the top
        Label:
            text:
                'Nested Vertical ScrollViews Test\\n'\
                'Outer: Vertical scroll (15 panels)\\n'\
                'Inner: Vertical scroll (30 items each)\\n'\
                'Both ScrollViews scroll in the same direction (Y-axis)'
            size_hint_y: None
            height: dp(80)
            color: 1, 1, 0, 1
            halign: 'center'
            text_size: self.size
'''


class InnerPanel(BoxLayout):
    """Panel widget containing a vertical ScrollView with items."""
    panel_index = NumericProperty(0)

    def on_kv_post(self, base_widget):
        """Populate the inner scroll content after KV is processed."""
        content = self.ids.content
        scrollview = self.ids.inner_scroll

        # Add 30 labels to make it scrollable
        for j in range(1, 31):
            label = Label(
                text=f"Inner Item {j} in Panel {self.panel_index + 1}",
                size_hint_y=None,
                size_hint_x=None,
                height=32,
                color=(0.2, 0.6, 1, 1),  # Blue color to distinguish inner items
            )
            # Size label to fit text
            label.bind(texture_size=label.setter('size'))
            content.add_widget(label)

        # Bind scrollview width to content width so it centers properly
        content.bind(width=scrollview.setter('width'))


class NestedVerticalsKVDemo(App):
    """Main application."""

    def build(self):
        root = Builder.load_string(kv)

        # Get the outer layout container
        outer_layout = root.ids.outer_layout

        # Add 15 panels to make the outer scroll scrollable
        for i in range(15):
            panel = InnerPanel(panel_index=i)
            outer_layout.add_widget(panel)

        return root


if __name__ == '__main__':
    NestedVerticalsKVDemo().run()

