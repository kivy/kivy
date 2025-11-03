"""
KV-based Nested Orthogonal ScrollView Demo
===========================================
Demo showing nested scrollviews using KV language.
Test orthogonal nested scrollview
(Vertical outer + Horizontal inner, Horizontal outer + Vertical inner)

"""

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import NumericProperty

# KV string defining the layout structure
kv = '''
<HorizontalScrollRow>:
    orientation: 'vertical'
    size_hint_y: None
    height: dp(120)

    # Inner horizontal ScrollView
    ScrollView:
        id: h_scroll
        do_scroll_x: True
        do_scroll_y: False
        scroll_type: ['bars', 'content']
        bar_width: dp(6)
        bar_color: 1.0, 0.5, 0.3, 0.8
        smooth_scroll_end: 10

        BoxLayout:
            id: content
            orientation: 'horizontal'
            spacing: dp(10)
            size_hint_x: None
            width: self.minimum_width

<VerticalScrollColumn>:
    size_hint_x: None
    width: dp(200)

    # Inner vertical ScrollView
    ScrollView:
        id: v_scroll
        do_scroll_x: False
        do_scroll_y: True
        scroll_type: ['bars', 'content']
        bar_width: dp(6)
        bar_color: 1.0, 0.3, 0.5, 0.8
        smooth_scroll_end: 10

        GridLayout:
            id: content
            cols: 1
            spacing: dp(10)
            size_hint_y: None
            height: self.minimum_height

# Main layout
BoxLayout:
    orientation: 'horizontal'
    spacing: dp(10)
    padding: dp(10)

    # LEFT SIDE: Vertical outer with horizontal inner scrollviews
    ScrollView:
        id: left_scroll
        do_scroll_x: False
        do_scroll_y: True
        scroll_type: ['bars', 'content']
        bar_width: dp(8)
        bar_color: 0.3, 0.6, 1.0, 0.8
        smooth_scroll_end: 10

        BoxLayout:
            id: left_container
            orientation: 'vertical'
            spacing: dp(20)
            size_hint_y: None
            height: self.minimum_height

    # RIGHT SIDE: Horizontal outer with vertical inner scrollviews
    ScrollView:
        id: right_scroll
        do_scroll_x: True
        do_scroll_y: False
        scroll_type: ['bars', 'content']
        bar_width: dp(8)
        bar_color: 0.3, 1.0, 0.6, 0.8
        smooth_scroll_end: 10

        BoxLayout:
            id: right_container
            orientation: 'horizontal'
            spacing: dp(20)
            size_hint_x: None
            width: self.minimum_width
'''


class HorizontalScrollRow(BoxLayout):
    """Widget containing a horizontal ScrollView with buttons."""
    row_index = NumericProperty(0)

    def on_kv_post(self, base_widget):
        """Populate the horizontal scroll content after KV is processed."""
        content = self.ids.content

        # Add row label
        label = Label(
            text=f'Row {self.row_index + 1} - Horizontal Scroll',
            size_hint_x=None,
            width='200dp',
            color=[1, 1, 1, 1],
            bold=True
        )
        content.add_widget(label)

        # Add 15 buttons
        for j in range(15):
            btn = Button(
                text=f'Btn {j + 1}',
                size_hint_x=None,
                width='100dp',
                background_color=[0.2 + (self.row_index * 0.1) % 0.8,
                                  0.3, 0.7, 1]
            )
            content.add_widget(btn)


class VerticalScrollColumn(BoxLayout):
    """Widget containing a vertical ScrollView with buttons."""
    column_index = NumericProperty(0)

    def on_kv_post(self, base_widget):
        """Populate the vertical scroll content after KV is processed."""
        content = self.ids.content

        # Add column label
        label = Label(
            text=f'Column {self.column_index + 1}\nVertical Scroll',
            size_hint_y=None,
            height='40dp',
            color=[1, 1, 1, 1],
            bold=True
        )
        content.add_widget(label)

        # Add 20 buttons
        for j in range(20):
            btn = Button(
                text=f'Item {j + 1}',
                size_hint_y=None,
                height='60dp',
                background_color=[0.7, 0.3,
                                  0.2 + (self.column_index * 0.1) % 0.8, 1]
            )
            content.add_widget(btn)


class NestedScrollViewKVDemo(App):
    """Main application."""

    def build(self):
        root = Builder.load_string(kv)

        # Populate left side with 8 horizontal scroll rows
        left_container = root.ids.left_container
        for i in range(8):
            row = HorizontalScrollRow(row_index=i)
            left_container.add_widget(row)

        # Populate right side with 6 vertical scroll columns
        right_container = root.ids.right_container
        for i in range(6):
            column = VerticalScrollColumn(column_index=i)
            right_container.add_widget(column)

        return root


if __name__ == '__main__':
    NestedScrollViewKVDemo().run()
