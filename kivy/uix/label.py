'''
Label
=====

The :class:`Label` widget is for rendering text. It supports ascii and unicode
strings::

    # hello world text
    l = Label(text='Hello world')

    # unicode text; can only display glyphs that are available in the font
    l = Label(text=u'Hello world ' + unichr(2764))

    # multiline text
    l = Label(text='Multi\\nLine')

    # size
    l = Label(text='Hello world', font_size='20sp')

Markup text
-----------

.. versionadded:: 1.1.0

You can change the style of the text using :doc:`api-kivy.core.text.markup`.
The syntax is similar to the bbcode syntax but only the inline styling is
allowed::

    # hello world with world in bold
    l = Label(text='Hello [b]World[/b]', markup=True)

    # hello in red, world in blue
    l = Label(text='[color=ff3333]Hello[/color][color=3333ff]World[/color]',
        markup = True)

If you need to escape the markup from the current text, use
:func:`kivy.utils.escape_markup`::

    text = 'This is an important message [1]'
    l = Label(text='[b]' + escape_markup(text) + '[/b]', markup=True)

The following tags are available:

``[b][/b]``
    Activate bold text
``[i][/i]``
    Activate italic text
``[font=<str>][/font]``
    Change the font
``[size=<integer>][/size]``
    Change the font size
``[color=#<color>][/color]``
    Change the text color
``[ref=<str>][/ref]``
    Add an interactive zone. The reference + bounding box inside the
    reference will be available in :data:`Label.refs`
``[anchor=<str>]``
    Put an anchor in the text. You can get the position of your anchor within
    the text with :data:`Label.anchors`
``[sub][/sub]``
    Display the text at a subscript position relative to the text before it.
``[sup][/sup]``
    Display the text at a superscript position relative to the text before it.

If you want to render the markup text with a [ or ] or & character, you need to
escape them. We created a simple syntax::

    [   -> &bl;
    ]   -> &br;
    &   -> &amp;

Then you can write::

    "[size=24]Hello &bl;World&bt;[/size]"

Interactive Zone in Text
------------------------

.. versionadded:: 1.1.0

You can now have definable "links" using text markup. The idea is to be able
to detect when the user clicks on part of the text and to react.
The tag ``[ref=xxx]`` is used for that.

In this example, we are creating a reference on the word "World". When this word
is clicked, the function ``print_it`` will be called with the name of the
reference::

    def print_it(instance, value):
        print('User clicked on', value)
    widget = Label(text='Hello [ref=world]World[/ref]', markup=True)
    widget.bind(on_ref_press=print_it)

For prettier rendering, you could add a color for the reference. Replace the
``text=`` in the previous example with::

    'Hello [ref=world][color=0000ff]World[/color][/ref]'

'''

__all__ = ('Label', )

from functools import partial
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.core.text import Label as CoreLabel
from kivy.core.text.markup import MarkupLabel as CoreMarkupLabel
from kivy.properties import StringProperty, OptionProperty, \
        NumericProperty, BooleanProperty, ReferenceListProperty, \
        ListProperty, ObjectProperty, DictProperty
from kivy.utils import get_hex_from_color


class Label(Widget):
    '''Label class, see module documentation for more information.

    :Events:
        `on_ref_press`
            Fired when the user clicks on a word referenced with a
            ``[ref]`` tag in a text markup.
    '''

    _font_properties = ('text', 'font_size', 'font_name', 'bold', 'italic',
        'halign', 'valign', 'padding_x', 'padding_y', 'text_size', 'shorten',
        'mipmap', 'markup', 'line_height', 'max_lines')

    def __init__(self, **kwargs):
        self._trigger_texture = Clock.create_trigger(self.texture_update, -1)
        self.register_event_type('on_ref_press')
        super(Label, self).__init__(**kwargs)

        # bind all the property for recreating the texture
        d = Label._font_properties
        dkw = {}
        for x in d:
            dkw[x] = partial(self._trigger_texture_update, x)
        self.bind(**dkw)

        self._label = None
        self._create_label()

        # force the texture creation
        self._trigger_texture()

    def _create_label(self):
        # create the core label class according to markup value
        if self._label is not None:
            cls = self._label.__class__
        else:
            cls = None
        markup = self.markup
        if (markup and cls is not CoreMarkupLabel) or \
           (not markup and cls is not CoreLabel):
            # markup have change, we need to change our rendering method.
            d = Label._font_properties
            dkw = dict(list(zip(d, [getattr(self, x) for x in d])))
            if markup:
                self._label = CoreMarkupLabel(**dkw)
            else:
                self._label = CoreLabel(**dkw)

    def _trigger_texture_update(self, name=None, source=None, value=None):
        # check if the label core class need to be switch to a new one
        if name == 'markup':
            self._create_label()
        if source:
            if name == 'text':
                self._label.text = value
            elif name == 'text_size':
                self._label.usersize = value
            elif name == 'font_size':
                self._label.options[name] = value
            else:
                self._label.options[name] = value
        self._trigger_texture()

    def texture_update(self, *largs):
        '''Force texture recreation with the current Label properties.

        After this function call, the :data:`texture` and :data:`texture_size`
        will be updated in this order.
        '''
        self.texture = None
        if self._label.text.strip() == '':
            self.texture_size = (0, 0)
        else:
            mrkup = self._label.__class__ is CoreMarkupLabel
            if mrkup:
                text = self._label.text
                self._label.text = ''.join(('[color=',
                                            get_hex_from_color(self.color), ']',
                                            text, '[/color]'))
                self._label.refresh()
                # force the rendering to get the references
                if self._label.texture:
                    self._label.texture.bind()
                self._label.text = text
                self.refs = self._label.refs
                self.anchors = self._label.anchors
            else:
                self._label.refresh()
            texture = self._label.texture
            if texture is not None:
                self.texture = self._label.texture
                self.texture_size = list(self.texture.size)

    def on_touch_down(self, touch):
        if super(Label, self).on_touch_down(touch):
            return True
        if not len(self.refs):
            return False
        tx, ty = touch.pos
        tx -= self.center_x - self.texture_size[0] / 2.
        ty -= self.center_y - self.texture_size[1] / 2.
        ty = self.texture_size[1] - ty
        for uid, zones in self.refs.items():
            for zone in zones:
                x, y, w, h = zone
                if x <= tx <= w and y <= ty <= h:
                    self.dispatch('on_ref_press', uid)
                    return True
        return False

    def on_ref_press(self, ref):
        pass

    #
    # Properties
    #

    disabled_color = ListProperty([1, 1, 1, .3])
    '''Text color, in the format (r, g, b, a)

    .. versionadded:: 1.8.0

    :data:`disabled_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [1, 1, 1, .5].
    '''

    text = StringProperty('')
    '''Text of the label.

    Creation of a simple hello world::

        widget = Label(text='Hello world')

    If you want to create the widget with an unicode string, use::

        widget = Label(text=u'My unicode string')

    :data:`text` is a :class:`~kivy.properties.StringProperty`.
    '''

    text_size = ListProperty([None, None])
    '''By default, the label is not constrained to any bounding box.
    You can set the size constraint of the label with this property.

    .. versionadded:: 1.0.4

    For example, whatever your current widget size is, if you want the label to
    be created in a box with width=200 and unlimited height::

        Label(text='Very big big line', text_size=(200, None))

    .. note::

        This text_size property is the same as the
        :data:`~kivy.core.text.Label.usersize` property in the
        :class:`~kivy.core.text.Label` class. (It is named size= in the
        constructor.)

    :data:`text_size` is a :class:`~kivy.properties.ListProperty` and
    defaults to (None, None), meaning no size restriction by default.
    '''

    font_name = StringProperty('DroidSans')
    '''Filename of the font to use. The path can be absolute or relative.
    Relative paths are resolved by the :func:`~kivy.resources.resource_find`
    function.

    .. warning::

        Depending of your text provider, the font file can be ignored. However,
        you can mostly use this without problems.

        If the font used lacks the glyphs for the particular language/symbols
        you are using, you will see '[]' blank box characters instead of the
        actual glyphs. The solution is to use a font that has the glyphs you
        need to display. For example, to display |unicodechar|, use a font such
        as freesans.ttf that has the glyph.

        .. |unicodechar| image:: images/unicode-char.png

    :data:`font_name` is a :class:`~kivy.properties.StringProperty` and defaults
    to 'DroidSans'.
    '''

    font_size = NumericProperty('15sp')
    '''Font size of the text, in pixels.

    :data:`font_size` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 12dp.
    '''

    line_height = NumericProperty(1.0)
    '''Line Height for the text. e.g. line_height = 2 will cause the spacing
    between lines to be twice the size.

    :data:`line_height` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 1.0.

    .. versionadded:: 1.5.0
    '''

    bold = BooleanProperty(False)
    '''Indicates use of the bold version of your font.

    .. note::

        Depending of your font, the bold attribute may have no impact on your
        text rendering.

    :data:`bold` is a :class:`~kivy.properties.BooleanProperty` and defaults to
    False.
    '''

    italic = BooleanProperty(False)
    '''Indicates use of the italic version of your font.

    .. note::

        Depending of your font, the italic attribute may have no impact on your
        text rendering.

    :data:`italic` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    padding_x = NumericProperty(0)
    '''Horizontal padding of the text inside the widget box.

    :data:`padding_x` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    padding_y = NumericProperty(0)
    '''Vertical padding of the text inside the widget box.

    :data:`padding_x` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    padding = ReferenceListProperty(padding_x, padding_y)
    '''Padding of the text in the format (padding_x, padding_y)

    :data:`padding` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:data:`padding_x`, :data:`padding_y`) properties.
    '''

    halign = OptionProperty('left', options=['left', 'center', 'right',
                            'justify'])
    '''Horizontal alignment of the text.

    :data:`halign` is an :class:`~kivy.properties.OptionProperty` and defaults to
    'left'. Available options are : left, center, right and justified.

    .. warning::

        This doesn't change the position of the text texture of the Label
        (centered), only the position of the text in this texture. You probably
        want to bind the size of the Label to the :data:`texture_size` or set a
        :data:`text_size`.

    .. versionchanged:: 1.6.0

        A new option was added to :data:`halign`, namely `justify`.
    '''

    valign = OptionProperty('bottom', options=['bottom', 'middle', 'top'])
    '''Vertical alignment of the text.

    :data:`valign` is an :class:`~kivy.properties.OptionProperty` and defaults
    to 'bottom'. Available options are : bottom, middle and top.

    .. warning::

        This doesn't change the position of the text texture of the Label
        (centered), only the position of the text within this texture. You
        probably want to bind the size of the Label to the :data:`texture_size`
        or set a :data:`text_size` to change this behavior.
    '''

    color = ListProperty([1, 1, 1, 1])
    '''Text color, in the format (r, g, b, a)

    :data:`color` is a :class:`~kivy.properties.ListProperty` and defaults to
    [1, 1, 1, 1].
    '''

    texture = ObjectProperty(None, allownone=True)
    '''Texture object of the text.
    The text is rendered automatically when a property changes. The OpenGL
    texture created in this operation is stored in this property. You can use
    this :data:`texture` for any graphics elements.

    Depending on the texture creation, the value will be a
    :class:`~kivy.graphics.texture.Texture` or
    :class:`~kivy.graphics.texture.TextureRegion` object.

    .. warning::

        The :data:`texture` update is scheduled for the next frame. If you need
        the texture immediately after changing a property, you have to call
        the :meth:`texture_update` method before accessing :data:`texture`::

            l = Label(text='Hello world')
            # l.texture is good
            l.font_size = '50sp'
            # l.texture is not updated yet
            l.texture_update()
            # l.texture is good now.

    :data:`texture` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    texture_size = ListProperty([0, 0])
    '''Texture size of the text.

    .. warning::

        The :data:`texture_size` is set after the :data:`texture` property. If
        you listen for changes to :data:`texture`, :data:`texture_size` will not
        be up-to-date in your callback. Bind to :data:`texture_size` instead.
    '''

    mipmap = BooleanProperty(False)
    '''Indicates whether OpenGL mipmapping is applied to the texture or not.
    Read :ref:`mipmap` for more information.

    .. versionadded:: 1.0.7

    :data:`mipmap` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    shorten = BooleanProperty(False)
    '''
    Indicates whether the label should attempt to shorten its textual contents
    as much as possible if a `text_size` is given. Setting this to True without
    an appropriately set `text_size` will lead to unexpected results.

    :data:`shorten` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    markup = BooleanProperty(False)
    '''
    .. versionadded:: 1.1.0

    If True, the text will be rendered using the
    :class:`~kivy.core.text.markup.MarkupLabel`: you can change the style of the
    text using tags. Check the :doc:`api-kivy.core.text.markup` documentation
    for more information.

    :data:`markup` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    refs = DictProperty({})
    '''
    .. versionadded:: 1.1.0

    List of ``[ref=xxx]`` markup items in the text with the bounding box of
    all the words contained in a ref, available only after rendering.

    For example, if you wrote::

        Check out my [ref=hello]link[/hello]

    The refs will be set with::

        {'hello': ((64, 0, 78, 16), )}

    You know that the reference "hello" has a bounding box at (x1, y1, x2, y2).
    The current Label implementation uses these references if they exist in
    your markup text, automatically doing the collision with the touch and
    dispatching an `on_ref_press` event.

    You can bind a ref event like this::

        def print_it(instance, value):
            print('User click on', value)
        widget = Label(text='Hello [ref=world]World[/ref]', markup=True)
        widget.on_ref_press(print_it)

    .. note::

        This works only with markup text. You need :data:`markup` set to
        True.
    '''

    anchors = DictProperty({})
    '''
    .. versionadded:: 1.1.0

    Position of all the ``[anchor=xxx]`` markup in the text.

    You can place anchors in your markup text as follows::

        text = """
            [anchor=title1][size=24]This is my Big title.[/size]
            [anchor=content]Hello world
        """

    Then, all the ``[anchor=]`` references will be removed and you'll get all
    the anchor positions in this property (only after rendering)::

        >>> widget = Label(text=text, markup=True)
        >>> widget.texture_update()
        >>> widget.anchors
        {"content": (20, 32), "title1": (20, 16)}

    .. note::

        This works only with markup text. You need :data:`markup` set to
        True.

    '''

    max_lines = NumericProperty(0)
    '''Maximum number of lines to use, defaults to 0, which means unlimited.
    Please note that :data:`shorten` take over this property. (with shorten, the
    text is always one line.)

    .. versionadded:: 1.8.0

    :data:`max_lines` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''


