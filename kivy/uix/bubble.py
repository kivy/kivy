'''
Bubble
======

.. image:: images/bubble.jpg
    :align: right

:class:`Bubble` is a :class:`~kivy.uix.gridlayout.GridLayout`.
To configure the bubble, you can use the same properties that you can use for
the GridLayout class::

    bubble = Bubble(pos=(10,20), size =(50, 50))

'''

__all__ = ('Bubble', )

from kivy.uix.image      import Image
from kivy.uix.label      import Label
from kivy.uix.scatter    import Scatter
from kivy.uix.gridlayout import GridLayout
from kivy.properties     import ObjectProperty, StringProperty
from kivy.lang           import Builder

Builder.load_string('''
<BubbleContent>
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        BorderImage:
            border: 16, 16, 16, 16
            texture: root.parent.background_texture if root.parent else None
            size:root.size
            pos: root.pos
''')

class BubbleContent(GridLayout):
      def __init__(self, **kwargs):
          super(BubbleContent, self).__init__(**kwargs)
          self.rows = 1

class Bubble(GridLayout):
    '''Bubble class, see module documentation for more information.
    '''

    background_image = StringProperty('data/images/bubble.png')
    '''Background image of the bubble
    '''

    arrow_image = StringProperty('data/images/bubble_arrow.png')
    ''' Image of the arrow pointing to the bubble
    '''

    arrow_pos = StringProperty('bottom_mid')
    '''specifies the position of the arrow relative to the bubble
    can be one of 'left_top, left_mid, left_bottom
                   top_left, top_mid, top_right
                   right_top, right_mid, right_bottom
                   bottom_left, bottom_mid, bottom_right'
    '''

    background_texture = ObjectProperty(None)
    '''specifies the background texture of the bubble
    '''

    content = ObjectProperty(None)
    '''this is the object where the main content of the bubble
       is held
    '''

    def __init__(self, **kwargs):
        self.arrow_layout = GridLayout(rows = 1)
        self.bk_img = Image(source = self.background_image,
                                  allow_stretch = True,
                                  keep_ratio = False)
        self.background_texture = self.bk_img.texture
        self.arrow_img = Image(source = self.arrow_image)
        self.rows = 1
        super(Bubble, self).__init__(**kwargs)
        self.content = BubbleContent()
        self.padding = 2
        self.add_widget(self.content)
        self.bk_img.bind(on_texture = self._on_texture)
        self.on_arrow_pos()

    def _on_texture(self, *l):
        self.background_texture = self.bk_img.texture

    def add_widget(self, *l):
        if l[0] == self.content or l[0] == self.arrow_img\
            or l[0] == self.arrow_layout:
            super(Bubble, self).add_widget(*l)
        else:
            self.content.add_widget(l[0])

    def on_background_image(self, *l):
        self.bk_img.source = self.background_image

    def on_arrow_image(self, *l):
        self.arrow_img.source = self.arrow_image

    def on_arrow_pos(self, *l):
        if not self.content:
            return
        self.arrow_layout.clear_widgets()
        self.clear_widgets()
        self.arrow_img.size_hint = (1, None)
        self.arrow_img.height = self.arrow_img.texture_size[1]
        if self.arrow_pos[0] == 'b' or self.arrow_pos[0] == 't':
            self.cols = 1
            self.rows = 2
            self.arrow_layout.rows = 1
            self.arrow_layout.cols = 3
            self.arrow_img.width = self.width/3
            self.arrow_layout.size_hint = (1, None)
            self.arrow_layout.height = self.arrow_img.height
            if self.arrow_pos[0] == 'b':
                self.add_widget(self.content)
                if self.arrow_pos == 'bottom_mid':
                    self.add_widget(self.arrow_img)
                elif self.arrow_pos == 'bottom_left':
                    self.arrow_layout.add_widget(self.arrow_img)
                    #add two dummy widgets
                    self.arrow_layout.add_widget(Label())
                    self.arrow_layout.add_widget(Label())
                    self.add_widget(self.arrow_layout)
                elif self.arrow_pos == 'bottom_right':
                    #add two dummy widgets
                    self.arrow_layout.add_widget(Label())
                    self.arrow_layout.add_widget(Label())
                    self.arrow_layout.add_widget(self.arrow_img)
                    self.add_widget(self.arrow_layout)
            else:
                sctr = Scatter(do_translation = False,
                               rotation = 180,
                               do_rotation = False,
                               do_scale = False,
                               size_hint = (None, None),
                               size = self.arrow_img.size)
                sctr.add_widget(self.arrow_img)
                if self.arrow_pos == 'top_mid':
                    #add two dummy widgets
                    self.arrow_layout.add_widget(Label())
                    self.arrow_layout.add_widget(sctr)
                    self.arrow_layout.add_widget(Label())
                    self.add_widget(self.arrow_layout)
                    self.add_widget(self.content)
                elif self.arrow_pos == 'top_left':
                    self.arrow_layout.add_widget(sctr)
                    #add two dummy widgets
                    self.arrow_layout.add_widget(Label())
                    self.arrow_layout.add_widget(Label())
                    self.add_widget(self.arrow_layout)
                    self.add_widget(self.content)
                elif self.arrow_pos == 'top_right':
                    #add two dummy widgets
                    self.arrow_layout.add_widget(Label())
                    self.arrow_layout.add_widget(Label())
                    self.arrow_layout.add_widget(sctr)
                    self.add_widget(self.arrow_layout)
                    self.add_widget(self.content)
        elif self.arrow_pos[0] == 'l' or self.arrow_pos[0] == 'r':
            self.cols = 2
            self.rows = 1
            self.arrow_img.width = self.height/3
            self.arrow_layout.rows = 3
            self.arrow_layout.cols = 1
            self.arrow_layout.size_hint = (None, 1)
            self.arrow_layout.width = self.arrow_img.height
            rotation = -90 if self.arrow_pos[0] == 'l' else 90
            sctr = Scatter(do_translation = False,
                               rotation = rotation,
                               do_rotation = False,
                               do_scale = False,
                               size_hint = (None, None),
                               size = self.arrow_img.size)
            sctr.add_widget(self.arrow_img)
            len_arrow_pos = len(self.arrow_pos)
            if self.arrow_pos[len_arrow_pos-4:] == '_top':
                self.arrow_layout.add_widget(Label(size_hint = (1, .07)))
                self.arrow_layout.add_widget(sctr)
                #add two dummy widgets
                self.arrow_layout.add_widget(Label(size_hint = (1, .3)))
                if self.arrow_pos[0] =='l':
                    self.add_widget(self.arrow_layout)
                    self.add_widget(self.content)
                else:
                    self.add_widget(self.content)
                    self.add_widget(self.arrow_layout)
            elif self.arrow_pos[len_arrow_pos-4:] == '_mid':
                #add two dummy widgets
                self.arrow_layout.add_widget(Label())
                self.arrow_layout.add_widget(sctr)
                self.arrow_layout.add_widget(Label())
                if self.arrow_pos[0] =='l':
                    self.add_widget(self.arrow_layout)
                    self.add_widget(self.content)
                else:
                    self.add_widget(self.content)
                    self.add_widget(self.arrow_layout)
            elif self.arrow_pos[len_arrow_pos-7:] == '_bottom':
                #add two dummy widgets
                self.arrow_layout.add_widget(Label())
                self.arrow_layout.add_widget(Label())
                self.arrow_layout.add_widget(sctr)
                if self.arrow_pos[0] =='l':
                    self.add_widget(self.arrow_layout)
                    self.add_widget(self.content)
                else:
                    self.add_widget(self.content)
                    self.add_widget(self.arrow_layout)