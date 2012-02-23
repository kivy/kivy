'''
Label
=====

The :class:`Label` widget is for rendering text. It supports ascii and unicode
strings ::

    # hello world text
    l = Label(text='Hello world')

    # unicode text; can only display glyphs that are available in the font
    l = Label(text=u'Hello world ' + unichr(2764))

    # multiline text
    l = Label(text='Multi\\nLine')

    # size
    l = Label(text='Hello world', font_size=20)

Markup text
-----------

.. versionadded:: 1.1.0

You can change the style of the text using :doc:`api-kivy.core.text.markup`.
The syntax is near the bbcode syntax, but only the inline styling is allowed::

    # hello world with world in bold
    l = Label(text='Hello [b]World[/b]', markup=True)

    # hello in red, world in blue
    l = Label(text='[color=ff3333]Hello[/color][color=3333ff]World[/color]',
        markup = True)

The following tags are availables:

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
    Add an interactive zone. The reference + all the word box inside the
    reference will be available in :data:`Label.refs`
``[anchor=<str>]``
    Put an anchor in the text. You can get the position of your anchor within
    the text with :data:`Label.anchors`

If you want to render the markup text with a character [ or ] or &, you need to
escape them. We created a simple syntax::

    [   -> &bl;
    ]   -> &br;
    &   -> &amp;

Then you can write::

    "[size=24]Hello &bl;World&bt;[/size]"

Interactive zone in text
------------------------

.. versionadded:: 1.1.0

You can now have some kind of "links" using text markup. The idea is to be able
to detect when the user click on a some part of the text, and react to it.
The tag ``[ref=xxx]`` is used for that.

In this example, we are creating a reference on the word "World". When click on
it, the function ``print_it`` will be called with the name of the reference::

    def print_it(instance, value):
        print 'User click on', value
    widget = Label(text='Hello [ref=world]World[/ref]', markup=True)
    widget.on_ref_press(print_it)

For a better rendering, you could put a color for the reference. Replace the
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


class Label(Widget):
    '''Label class, see module documentation for more information.

    :Events:
        `on_ref_press`
            Fired when the user have clicked on a word referenced with a
            ``[ref]`` tag in a text markup.
    '''

    _font_properties = ('text', 'font_size', 'font_name', 'bold', 'italic',
        'halign', 'valign', 'padding_x', 'padding_y', 'text_size', 'shorten',
        'mipmap', 'markup')

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
        self.texture_update()

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
            dkw = dict(zip(d, [getattr(self, x) for x in d]))
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
            if self._label.__class__ is CoreMarkupLabel:
                self.refs = self._label.refs
                self.anchors = self._label.anchors
            texture = self._label.texture
            if texture is not None:
                self.texture = self._label.texture
                self.texture_size = list(self.texture.size)

    def on_touch_down(self, touch):
        if not len(self.refs):
            return False
        tx, ty = touch.pos
        tx -= self.center_x - self.texture_size[0] / 2.
        ty -= self.center_y - self.texture_size[1] / 2.
        ty = self.texture_size[1] - ty
        for uid, zones in self.refs.iteritems():
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
    text = StringProperty('')
    '''Text of the label.

    Creation of a simple hello world ::

        widget = Label(text='Hello world')

    If you want to create the widget with an unicode string, use ::

        widget = Label(text=u'My unicode string')

    :data:`text` a :class:`~kivy.properties.StringProperty`.
    '''

    text_size = ListProperty([None, None])
    '''By default, the label is not constrained to any bounding box.
    You can set the size constraint of the label with this property.

    .. versionadded:: 1.0.4

    For example, whatever your current widget size is, if you want the label to
    be created in a box with width=200 and unlimited height::

        Label(text='Very big big line', text_size=(200, None))

    .. note::

        This text_size property is the same as
        :data:`~kivy.core.text.Label.usersize` property in
        :class:`~kivy.core.text.Label` class. (Even if it's named size= in
        constructor.)

    :data:`text_size` is a :class:`~kivy.properties.ListProperty`,
    default to (None, None), meaning no size restriction by default.
    '''

    font_name = StringProperty('DroidSans')
    '''Filename of the font to use, the path can be absolute or relative.
    Relative paths are resolved by the :func:`~kivy.resources.resource_find`
    function.

    .. warning::

        Depending of your text provider, the font file can be ignored. However,
        you can mostly use this without trouble.

        If the font used lacks the glyphs for the perticular language/symbols
        you are using, you will see '[]' blank box characters instead of the
        actual glyphs. The solution is to use a font that has the glyphs you
        need to display. For example to display |unicodechar|, use a font like
        freesans.ttf that has the glyph.

        .. |unicodechar| image:: images/unicode-char.png

    :data:`font_name` is a :class:`~kivy.properties.StringProperty`, default to
    'DroidSans'.
    '''

    font_size = NumericProperty(12)
    '''Font size of the text, in pixels.

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
    The text is rendered automatically when a property changes, and stored in
    this property. You can use this :data:`texture` for any graphics elements.

    Depending on the texture creation, the value will be a
    :class:`~kivy.graphics.texture.Texture` or
    :class:`~kivy.graphics.texture.TextureRegion` object.

    .. warning::

        The :data:`texture` update is scheduled for the next frame. If you need
        the texture immediately after changing a property, you have to call
        the :func:`texture_update` function before acessing :data:`texture` ::

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

        The data:`texture_size` is set after the :data:`texture` property. If
        you listen for changes to :data:`texture`, :data:`texture_size` will not
        be up to date in your callback. Bind to data:`texture_size` instead.
    '''

    mipmap = BooleanProperty(False)
    '''Indicate if you want OpenGL mipmapping applied to texture or not.
    Read :ref:`mipmap` for more information.

    .. versionadded:: 1.0.7

    :data:`mipmap` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
    '''

    shorten = BooleanProperty(False)
    '''
    Indicate whether the label should attempt to shorten its textual contents as
    much as possible if a `text_size` is given. Setting this to True without an
    appropriately set `text_size` will lead to unexpected results.

    :data:`shorten` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
    '''

    markup = BooleanProperty(False)
    '''
    .. versionadded:: 1.1.0

    If true, the text will be rendered with
    :class:`~kivy.core.text.markup.MarkupLabel`: you can change the style of the
    text using tags. Check :doc:`api-kivy.core.text.markup` documentation for
    more information

    :data:`markup` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
    '''

    refs = DictProperty({})
    '''
    .. versionadded:: 1.1.0

    List of ``[ref=xxx]`` markup put into the text, with all the bounding box of
    all the words contained in a ref, only after rendering.

    For example, if you wrote::

        Check out my [ref=hello]link[/hello]

    The refs will be set with::

        {'hello': ((64, 0, 78, 16), )}

    You know that the reference "hello" have one bounding box set at (x1, y1,
    x2, y2). The current Label implementation use theses references if existing
    in your markup text, do automatically the collision with the touch, and
    dispatch an ``on_ref_press`` event.

    You can bind a ref event like this::

        def print_it(instance, value):
            print 'User click on', value
        widget = Label(text='Hello [ref=world]World[/ref]', markup=True)
        widget.on_ref_press(print_it)

    .. note::

        This is working only with markup text. You need :data:`markup` set to
        True.
    '''

    anchors = DictProperty({})
    '''
    .. versionadded:: 1.1.0

    Position of all the ``[anchor=xxx]`` markup put into the text.

    You can put some anchors in your markup text::

        text = """
            [anchor=title1][size=24]This is my Big title.[/size]
            [anchor=content]Hello world
        """

    Then, all the ``[anchor=]`` will be removed, and you'll get all the anchors
    positions in this property (only after rendering)::

        >>> widget = Label(text=text, markup=True)
        >>> widget.texture_update()
        >>> widget.anchors
        {"content": (20, 32), "title1": (20, 16)}

    .. note::

        This is working only with markup text. You need :data:`markup` set to
        True.

    '''

