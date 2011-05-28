'''
Label
=====

The label widget is a widget for rendering text. You can use ascii strings or
unicode strings.

Snippet ::

    # hello world text
    l = Label(text='Hello world')

    # multiline text
    l = Label(text='Multi\\nLine')

    # size
    l = Label(text='Hello world', font_size=20)

'''

__all__ = ('Label', )

from functools import partial
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.core.text import Label as CoreLabel
from kivy.resources import resource_find
from kivy.properties import StringProperty, OptionProperty, \
        NumericProperty, BooleanProperty, ReferenceListProperty, \
        ListProperty, ObjectProperty


class Label(Widget):
    '''Label class, see module documentation for more information.
    '''

    def __init__(self, **kwargs):
        self._trigger_texture = Clock.create_trigger(self.texture_update, -1)
        super(Label, self).__init__(**kwargs)

        # bind all the property for recreating the texture
        d = ('text', 'font_size', 'font_name', 'bold', 'italic', 'halign',
             'valign', 'padding_x', 'padding_y', 'text_size', 'shorten')
        dkw = {}
        for x in d:
            dkw[x] = partial(self._trigger_texture_update, x)
        self.bind(**dkw)

        dkw = dict(zip(d, [getattr(self, x) for x in d]))
        font_name = resource_find(self.font_name)
        if font_name:
            dkw['font_name'] = font_name
        self._label = CoreLabel(**dkw)

        # force the texture creation
        self.texture_update()

    def _trigger_texture_update(self, name=None, source=None, value=None):
        if source:
            if name == 'text':
                self._label.text = value
            elif name == 'text_size':
                self._label.usersize = value
            elif name == 'font_name':
                rvalue = resource_find(value)
                self._label.options['font_name'] = rvalue if rvalue else value
            else:
                self._label.options[name] = value
        self._trigger_texture()

    def texture_update(self, *largs):
        '''Force texture recreation with the current Label properties.

        After this function call, the :data:`texture` and :data`texture_size`
        will be updated in this order.
        '''
        self.texture = None
        if self._label.text.strip() == '':
            self.texture_size = (0, 0)
        else:
            self._label.refresh()
            texture = self._label.texture
            if texture is not None:
                self.texture = self._label.texture
                self.texture_size = list(self.texture.size)

    #
    # Properties
    #
    text = StringProperty('')
    '''Text of the label.

    Creation of a simple hello world ::

        widget = Label(text='Hello world')

    If you want to create the widget with an unicode string, use ::

        widget = Label(text=u'My unicode string')

    :data:`text` a :class:`~kivy.properties.StringProperty`.
    '''

    text_size = ListProperty([None, None])
    '''By default, the label is not contraint to any bounding box.
    You can set the size constraint of the label creation with this property.

    .. versionadded:: 1.0.4

    For example, whatever is your current widget size, if you want your label to
    be created in a box with width=200 and unlimited height::

        Label(text='Very big big line', text_size=(200, None))

    .. note::

        This text_size property is the same as
        :data:`~kivy.core.text.Label.usersize` property in
        :class:`~kivy.core.text.Label` class. (Even if it's named size= in
        constructor.)

    :data:`text_size` is a :class:`~kivy.properties.ListProperty` instance,
    default to (None, None). Mean they are no size restriction by default.
    '''

    font_name = StringProperty('fonts/DroidSans.ttf')
    '''File of the font to use. The path used for the font can be a absolute
    path, or a relative path that will be search with the
    :func:`~kivy.resources.resource_find` function.

    .. warning::

        Depending of your text provider, the font file can be ignored. But you
        can mostly use this without trouble.

    :data:`font_name` is a :class:`~kivy.properties.StringProperty`, default to
    'fonts/DroidSans.ttf'.
    '''

    font_size = NumericProperty(12)
    '''Font size of the text. The font size is in pixels.

    :data:`font_size` is a :class:`~kivy.properties.NumericProperty`, default to
    12.
    '''

    bold = BooleanProperty(False)
    '''Indicate if you want to use the bold version of your font.

    .. note::

        Depending of your font, the bold attribute may have no impact on your
        text rendering.

    :data:`bold` is a :class:`~kivy.properties.BooleanProperty`, default to
    False
    '''

    italic = BooleanProperty(False)
    '''Indicate if you want to use the italic version of your font.

    .. note::

        Depending of your font, the italic attribute may have no impact on your
        text rendering.

    :data:`italic` is a :class:`~kivy.properties.BooleanProperty`, default to
    False
    '''

    padding_x = NumericProperty(0)
    '''Horizontal padding of the text, inside the widget box.

    :data:`padding_x` is a :class:`~kivy.properties.NumericProperty`, default to
    0
    '''

    padding_y = NumericProperty(0)
    '''Vertical padding of the text, inside the widget box.

    :data:`padding_x` is a :class:`~kivy.properties.NumericProperty`, default to
    0
    '''

    padding = ReferenceListProperty(padding_x, padding_y)
    '''Padding of the text, in the format (padding_x, padding_y)

    :data:`padding` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:data:`padding_x`, :data:`padding_y`) properties.
    '''

    halign = OptionProperty('left', options=['left', 'center', 'right'])
    '''Horizontal alignment of the text.

    :data:`halign` is a :class:`~kivy.properties.OptionProperty`, default to
    'left'. Available options are : left, center and right.
    '''

    valign = OptionProperty('bottom', options=['bottom', 'middle', 'top'])
    '''Vertical alignment of the text.

    :data:`valign` is a :class:`~kivy.properties.OptionProperty`, default to
    'bottom'. Available options are : bottom, middle and top.
    '''

    color = ListProperty([1, 1, 1, 1])
    '''Text color, in the format (r, g, b, a)

    :data:`color` is a :class:`~kivy.properties.ListProperty`, default to [1, 1,
    1, 1].
    '''

    texture = ObjectProperty(None, allownone=True)
    '''Texture object of the text.
    The text is rendered after each properties changes, and stored inside this
    property. You can use this :data:`texture` for any graphics elements.

    Depending of the texture creation, the value will be a
    :class:`~kivy.graphics.texture.Texture` or
    :class:`~kivy.graphics.texture.TextureRegion` object.

    .. warning::

        The texture update is scheduled for the next frame. That's mean if you
        really want the texture just after changing a property, you need to call
        :func:`texture_update` function before ::

            l = Label(text='Hello world')
            # l.texture is good
            l.font_size = 50
            # l.texture is not updated yet
            l.update_texture()
            # l.texture is good now.

    :data:`texture` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    texture_size = ListProperty([0, 0])
    '''Texture size of the text.

    .. warning::

        The texture size is set after the texture property. So if you listen on
        the change to :data:`texture`, the property texture_size will be not yet
        updated. Use self.texture.size instead.
    '''

    shorten = BooleanProperty(False)
    '''
    Indicate whether the label should attempt to shorten its textual contents as
    much as possible if a `text_size` is given. Setting this to True without an
    appropriately set `text_size` will lead unexpected results.
    '''

