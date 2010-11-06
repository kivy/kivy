'''
Label: 
'''

__all__ = ('Label', )

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.core.text import Label as CoreLabel
from kivy.c_ext.properties import StringProperty, OptionProperty, \
        NumericProperty, BooleanProperty, ReferenceListProperty, \
        ListProperty, ObjectProperty

class Label(Widget):

    #: Text written in the label
    text = StringProperty('')

    #: Name of the font
    font_name = StringProperty('fonts/DejaVuSans.ttf')

    #: Size of the font
    font_size = NumericProperty(10)

    #: Activate bold style if available
    bold = BooleanProperty(False)

    #: Activate italic style if available
    italic = BooleanProperty(False)

    #: Padding X
    padding_x = NumericProperty(0)

    #: Padding Y
    padding_y = NumericProperty(0)

    #: Padding (x / y)
    padding = ReferenceListProperty(padding_x, padding_y)

    #: Horizontal alignement
    halign = OptionProperty('left', options=['left', 'center', 'right'])

    #: Vertical alignement
    valign = OptionProperty('bottom', options=['bottom', 'middle', 'top'])

    #: Color
    color = ListProperty([1, 1, 1, 1])

    #: Texture of the label
    texture = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(Label, self).__init__(**kwargs)

        # bind all the property for recreating the texture
        d = ('text', 'font_size', 'font_name', 'bold', 'italic', 'halign',
             'valign', 'padding_x', 'padding_y')
        dkw = dict(zip(d, [self._trigger_texture_update] * len(d)))
        self.bind(**dkw)

        dkw = dict(zip(d, [getattr(self, x) for x in d]))
        print dkw
        self._label = CoreLabel(**dkw)

        # force the texture creation
        self._trigger_texture_update()

        import pprint
        def printm(sender, value):
            print sender, value
        self.bind(texture=printm)

    def _trigger_texture_update(self, source=None, value=None):
        print '_trigger_texture_update()', source, value
        if source:
            self._label.options[source.name] = value
        Clock.unschedule(self._texture_update)
        Clock.schedule_once(self._texture_update)

    def _texture_update(self, *largs):
        self._label.refresh()
        self.texture = self._label.texture
