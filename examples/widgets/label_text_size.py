
'''
Label textsize
============

This example shows how the textsize and line_height property are used
to format label widget
'''

import kivy
kivy.require('1.0.7')

from kivy.app import App
from kivy.uix.label import Label


_long_text = ("""Lorem ipsum dolor sit amet, consectetur adipiscing elit. """
    """Phasellus odio nisi, pellentesque molestie adipiscing vitae, aliquam """
    """at tellus. Fusce quis est ornare erat pulvinar elementum ut sed """
    """felis. Donec vel neque mauris. In sit amet nunc sit amet diam dapibus """
    """lacinia. In sodales placerat mauris, ut euismod augue laoreet at. """
    """Integer in neque non odio fermentum volutpat nec nec nulla. Donec et """
    """risus non mi viverra posuere. Phasellus cursus augue purus, eget """
    """volutpat leo. Phasellus sed dui vitae ipsum mattis facilisis vehicula """
    """eu justo.\n\n"""
    """Quisque neque dolor, egestas sed venenatis eget, porta id ipsum. Ut """
    """faucibus, massa vitae imperdiet rutrum, sem dolor rhoncus magna, non """
    """lacinia nulla risus non dui. Nulla sit amet risus orci. Nunc libero """
    """justo, interdum eu pulvinar vel, pulvinar et lectus. Phasellus sed """
    """luctus diam. Pellentesque non feugiat dolor. Cras at dolor velit, """
    """gravida congue velit. Aliquam erat volutpat. Nullam eu nunc dui, quis """
    """sagittis dolor. Ut nec dui eget odio pulvinar placerat. Pellentesque """
    """mi metus, tristique et placerat ac, pulvinar vel quam. Nam blandit """
    """magna a urna imperdiet molestie. Nullam ut nisi eget enim laoreet """
    """sodales sit amet a felis.\n""")


class LabelTextSizeTest(App):
    def build(self):
        l = Label(
            text=_long_text,
            text_size=(600, None),
            line_height=1.5
        )
        return l

if __name__ == '__main__':
    LabelTextSizeTest().run()
