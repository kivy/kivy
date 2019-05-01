'''Label
=====

.. image:: images/label.png
    :align: right

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

.. _kivy-uix-label-sizing-and-text-content:

Sizing and text content
---------------------------

By default, the size of :class:`Label` is not affected by :attr:`~Label.text`
content and the text is not affected by the size. In order to control
sizing, you must specify :attr:`~Label.text_size` to constrain the text
and/or bind :attr:`~Label.size` to :attr:`~Label.texture_size` to grow with
the text.

For example, this label's size will be set to the text content
(plus :attr:`~Label.padding`):

.. code-block:: kv

    Label:
        size: self.texture_size

This label's text will wrap at the specified width and be clipped to the
height:

.. code-block:: kv

    Label:
        text_size: cm(6), cm(4)

.. note:: The :attr:`~Label.shorten` and :attr:`~Label.max_lines` attributes
 control how overflowing text behaves.

Combine these concepts to create a Label that can grow vertically but wraps the
text at a certain width:

.. code-block:: kv

    Label:
        text_size: root.width, None
        size: self.texture_size

How to have a custom background color in the label:

.. code-block:: kv

    # Define your background color Template
    <BackgroundColor@Widget>
        background_color: 1, 1, 1, 1
        canvas.before:
            Color:
                rgba: root.background_color
            Rectangle:
                size: self.size
                pos: self.pos
    # Now you can simply Mix the `BackgroundColor` class with almost
    # any other widget... to give it a background.
    <BackgroundLabel@Label+BackgroundColor>
        background_color: 0, 0, 0, 0
        # Default the background color for this label
        # to r 0, g 0, b 0, a 0
    # Use the BackgroundLabel any where in your kv code like below
    BackgroundLabel
        text: 'Hello'
        background_color: 1, 0, 0, 1

Text alignment and wrapping
---------------------------

The :class:`Label` has :attr:`~Label.halign` and :attr:`~Label.valign`
properties to control the alignment of its text. However, by default the text
image (:attr:`~Label.texture`) is only just large enough to contain the
characters and is positioned in the center of the Label. The valign property
will have no effect and halign will only have an effect if your text has
newlines; a single line of text will appear to be centered even though halign
is set to left (by default).

In order for the alignment properties to take effect, set the
:attr:`~Label.text_size`, which specifies the size of the bounding box within
which text is aligned. For instance, the following code binds this size to the
size of the Label, so text will be aligned within the widget bounds. This
will also automatically wrap the text of the Label to remain within this area.

.. code-block:: kv

    Label:
        text_size: self.size
        halign: 'right'
        valign: 'middle'

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
``[u][/u]``
    Underlined text
``[s][/s]``
    Strikethrough text
``[font=<str>][/font]``
    Change the font (note: this refers to a TTF file or registered alias)
``[font_context=<str>][/font_context]``
    Change context for the font, use string value "none" for isolated context
    (this is equivalent to `None`; if you created a font context named
    `'none'`, it cannot be referred to using markup)
``[font_family=<str>][/font_family]``
    Font family to request for drawing. This is only valid when using a
    font context, see :class:`kivy.uix.label.Label` for details.
``[font_features=<str>][/font_features]``
    OpenType font features, in CSS format, this is passed straight
    through to Pango. The effects of requesting a feature depends on loaded
    fonts, library versions, etc. Pango only, requires v1.38 or later.
``[size=<integer>][/size]``
    Change the font size
``[color=#<color>][/color]``
    Change the text color
``[ref=<str>][/ref]``
    Add an interactive zone. The reference + bounding box inside the
    reference will be available in :attr:`Label.refs`
``[anchor=<str>]``
    Put an anchor in the text. You can get the position of your anchor within
    the text with :attr:`Label.anchors`
``[sub][/sub]``
    Display the text at a subscript position relative to the text before it.
``[sup][/sup]``
    Display the text at a superscript position relative to the text before it.
``[text_language=<str>][/text_language]``
    Language of the text, this is an RFC-3066 format language tag (as string),
    for example "en_US", "zh_CN", "fr" or "ja". This can impact font selection
    and metrics. Use the string "None" to revert to locale detection.
    Pango only.

If you want to render the markup text with a [ or ] or & character, you need to
escape them. We created a simple syntax::

    [   -> &bl;
    ]   -> &br;
    &   -> &amp;

Then you can write::

    "[size=24]Hello &bl;World&br;[/size]"

Interactive zone in text
------------------------

.. versionadded:: 1.1.0

You can now have definable "links" using text markup. The idea is to be able
to detect when the user clicks on part of the text and to react.
The tag ``[ref=xxx]`` is used for that.

In this example, we are creating a reference on the word "World". When
this word is clicked, the function ``print_it`` will be called with the
name of the reference::

    def print_it(instance, value):
        print('User clicked on', value)
    widget = Label(text='Hello [ref=world]World[/ref]', markup=True)
    widget.bind(on_ref_press=print_it)

For prettier rendering, you could add a color for the reference. Replace the
``text=`` in the previous example with::

    'Hello [ref=world][color=0000ff]World[/color][/ref]'

Catering for Unicode languages
------------------------------

The font kivy uses does not contain all the characters required for displaying
all languages. When you use the built-in widgets, this results in a block being
drawn where you expect a character.

If you want to display such characters, you can chose a font that supports them
and deploy it universally via kv:

.. code-block:: kv

    <Label>:
        font_name: '/<path>/<to>/<font>'

Note that this needs to be done before your widgets are loaded as kv rules are
only applied at load time.

Usage example
-------------

The following example marks the anchors and references contained in a label::

    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.clock import Clock
    from kivy.graphics import Color, Rectangle


    class TestApp(App):

        @staticmethod
        def get_x(label, ref_x):
            """ Return the x value of the ref/anchor relative to the canvas """
            return label.center_x - label.texture_size[0] * 0.5 + ref_x

        @staticmethod
        def get_y(label, ref_y):
            """ Return the y value of the ref/anchor relative to the canvas """
            # Note the inversion of direction, as y values start at the top of
            # the texture and increase downwards
            return label.center_y + label.texture_size[1] * 0.5 - ref_y

        def show_marks(self, label):

            # Indicate the position of the anchors with a red top marker
            for name, anc in label.anchors.items():
                with label.canvas:
                    Color(1, 0, 0)
                    Rectangle(pos=(self.get_x(label, anc[0]),
                                   self.get_y(label, anc[1])),
                              size=(3, 3))

            # Draw a green surround around the refs. Note the sizes y inversion
            for name, boxes in label.refs.items():
                for box in boxes:
                    with label.canvas:
                        Color(0, 1, 0, 0.25)
                        Rectangle(pos=(self.get_x(label, box[0]),
                                       self.get_y(label, box[1])),
                                  size=(box[2] - box[0],
                                        box[1] - box[3]))

        def build(self):
            label = Label(
                text='[anchor=a]a\\nChars [anchor=b]b\\n[ref=myref]ref[/ref]',
                markup=True)
            Clock.schedule_once(lambda dt: self.show_marks(label), 1)
            return label

    TestApp().run()

'''

__all__ = ('Label', )

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.core.text import Label as CoreLabel, DEFAULT_FONT
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

    __events__ = ['on_ref_press']

    _font_properties = ('text', 'font_size', 'font_name', 'bold', 'italic',
                        'underline', 'strikethrough', 'font_family', 'color',
                        'disabled_color', 'halign', 'valign', 'padding_x',
                        'padding_y', 'outline_width', 'disabled_outline_color',
                        'outline_color', 'text_size', 'shorten', 'mipmap',
                        'line_height', 'max_lines', 'strip', 'shorten_from',
                        'split_str', 'ellipsis_options', 'unicode_errors',
                        'markup', 'font_hinting', 'font_kerning',
                        'font_blended', 'font_context', 'font_features',
                        'base_direction', 'text_language')

    def __init__(self, **kwargs):
        self._trigger_texture = Clock.create_trigger(self.texture_update, -1)
        super(Label, self).__init__(**kwargs)

        # bind all the property for recreating the texture
        d = Label._font_properties
        fbind = self.fbind
        update = self._trigger_texture_update
        fbind('disabled', update, 'disabled')
        for x in d:
            fbind(x, update, x)

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
            elif name == 'disabled_color' and self.disabled:
                self._label.options['color'] = value
            elif name == 'disabled_outline_color' and self.disabled:
                self._label.options['outline_color'] = value
            elif name == 'disabled':
                self._label.options['color'] = self.disabled_color if value \
                    else self.color
                self._label.options['outline_color'] = (
                    self.disabled_outline_color if value else
                    self.outline_color)
            else:
                self._label.options[name] = value
        self._trigger_texture()

    def texture_update(self, *largs):
        '''Force texture recreation with the current Label properties.

        After this function call, the :attr:`texture` and :attr:`texture_size`
        will be updated in this order.
        '''
        mrkup = self._label.__class__ is CoreMarkupLabel
        self.texture = None

        if (not self._label.text or
                (self.halign == 'justify' or self.strip) and
                not self._label.text.strip()):
            self.texture_size = (0, 0)
            self.is_shortened = False
            if mrkup:
                self.refs, self._label._refs = {}, {}
                self.anchors, self._label._anchors = {}, {}
        else:
            if mrkup:
                text = self.text
                # we must strip here, otherwise, if the last line is empty,
                # markup will retain the last empty line since it only strips
                # line by line within markup
                if self.halign == 'justify' or self.strip:
                    text = text.strip()
                self._label.text = ''.join(('[color=',
                                            get_hex_from_color(
                                                self.disabled_color if
                                                self.disabled else self.color),
                                            ']', text, '[/color]'))
                self._label.refresh()
                # force the rendering to get the references
                if self._label.texture:
                    self._label.texture.bind()
                self.refs = self._label.refs
                self.anchors = self._label.anchors
            else:
                self._label.refresh()
            texture = self._label.texture
            if texture is not None:
                self.texture = self._label.texture
                self.texture_size = list(self.texture.size)
            self.is_shortened = self._label.is_shortened

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
    '''The color of the text when the widget is disabled, in the (r, g, b, a)
    format.

    .. versionadded:: 1.8.0

    :attr:`disabled_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [1, 1, 1, .3].
    '''

    text = StringProperty('')
    '''Text of the label.

    Creation of a simple hello world::

        widget = Label(text='Hello world')

    If you want to create the widget with an unicode string, use::

        widget = Label(text=u'My unicode string')

    :attr:`text` is a :class:`~kivy.properties.StringProperty` and defaults to
    ''.
    '''

    text_size = ListProperty([None, None])
    '''By default, the label is not constrained to any bounding box.
    You can set the size constraint of the label with this property.
    The text will autoflow into the constraints. So although the font size
    will not be reduced, the text will be arranged to fit into the box as best
    as possible, with any text still outside the box clipped.

    This sets and clips :attr:`texture_size` to text_size if not None.

    .. versionadded:: 1.0.4

    For example, whatever your current widget size is, if you want the label to
    be created in a box with width=200 and unlimited height::

        Label(text='Very big big line', text_size=(200, None))

    .. note::

        This text_size property is the same as the
        :attr:`~kivy.core.text.Label.usersize` property in the
        :class:`~kivy.core.text.Label` class. (It is named size= in the
        constructor.)

    :attr:`text_size` is a :class:`~kivy.properties.ListProperty` and
    defaults to (None, None), meaning no size restriction by default.
    '''

    base_direction = OptionProperty(None,
                     options=['ltr', 'rtl', 'weak_rtl', 'weak_ltr', None],
                     allownone=True)
    '''Base direction of text, this impacts horizontal alignment when
    :attr:`halign` is `auto` (the default). Available options are: None,
    "ltr" (left to right), "rtl" (right to left) plus "weak_ltr" and
    "weak_rtl".

    .. note::
        This feature requires the Pango text provider.

    .. note::
        Weak modes are currently not implemented in Kivy text layout, and
        have the same effect as setting strong mode.

    .. versionadded:: 1.11.0

    :attr:`base_direction` is an :class:`~kivy.properties.OptionProperty` and
    defaults to None (autodetect RTL if possible, otherwise LTR).
    '''

    text_language = StringProperty(None, allownone=True)
    '''Language of the text, if None Pango will determine it from locale.
    This is an RFC-3066 format language tag (as a string), for example
    "en_US", "zh_CN", "fr" or "ja". This can impact font selection, metrics
    and rendering. For example, the same bytes of text can look different
    for `ur` and `ar` languages, though both use Arabic script.

    .. note::
        This feature requires the Pango text provider.

    .. versionadded:: 1.11.0

    :attr:`text_language` is a :class:`~kivy.properties.StringProperty` and
    defaults to None.
    '''

    font_context = StringProperty(None, allownone=True)
    '''Font context. `None` means the font is used in isolation, so you are
    guaranteed to be drawing with the TTF file resolved by :attr:`font_name`.
    Specifying a value here will load the font file into a named context,
    enabling fallback between all fonts in the same context. If a font
    context is set, you are not guaranteed that rendering will actually use
    the specified TTF file for all glyphs (Pango will pick the one it
    thinks is best).

    If Kivy is linked against a system-wide installation of FontConfig,
    you can load the system fonts by specifying a font context starting
    with the special string `system://`. This will load the system
    fontconfig configuration, and add your application-specific fonts on
    top of it (this imposes a signifficant risk of family name collision,
    Pango may not use your custom font file, but pick one from the system)

    .. note::
        This feature requires the Pango text provider.

    .. versionadded:: 1.11.0

    :attr:`font_context` is a :class:`~kivy.properties.StringProperty` and
    defaults to None.
    '''

    font_family = StringProperty(None, allownone=True)
    '''Font family, this is only applicable when using :attr:`font_context`
    option. The specified font family will be requested, but note that it may
    not be available, or there could be multiple fonts registered with the
    same family. The value can be a family name (string) available in the
    font context (for example a system font in a `system://` context, or a
    custom font file added using :class:`kivy.core.text.FontContextManager`).
    If set to `None`, font selection is controlled by the :attr:`font_name`
    setting.

    .. note::
        If using :attr:`font_name` to reference a custom font file, you
        should leave this as `None`. The family name is managed automatically
        in this case.

    .. note::
        This feature requires the Pango text provider.

    .. versionadded:: 1.11.0

    :attr:`font_family` is a :class:`~kivy.properties.StringProperty` and
    defaults to None.
    '''

    font_name = StringProperty(DEFAULT_FONT)
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

    :attr:`font_name` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'Roboto'. This value is taken
    from :class:`~kivy.config.Config`.
    '''

    font_size = NumericProperty('15sp')
    '''Font size of the text, in pixels.

    :attr:`font_size` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 15sp.
    '''

    font_features = StringProperty()
    '''OpenType font features, in CSS format, this is passed straight
    through to Pango. The effects of requesting a feature depends on loaded
    fonts, library versions, etc. For a complete list of features, see:

    https://en.wikipedia.org/wiki/List_of_typographic_features

    .. note::
        This feature requires the Pango text provider, and Pango library
        v1.38 or later.

    .. versionadded:: 1.11.0

    :attr:`font_features` is a :class:`~kivy.properties.StringProperty` and
    defaults to an empty string.
    '''

    line_height = NumericProperty(1.0)
    '''Line Height for the text. e.g. line_height = 2 will cause the spacing
    between lines to be twice the size.

    :attr:`line_height` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 1.0.

    .. versionadded:: 1.5.0
    '''

    bold = BooleanProperty(False)
    '''Indicates use of the bold version of your font.

    .. note::

        Depending of your font, the bold attribute may have no impact on your
        text rendering.

    :attr:`bold` is a :class:`~kivy.properties.BooleanProperty` and defaults to
    False.
    '''

    italic = BooleanProperty(False)
    '''Indicates use of the italic version of your font.

    .. note::

        Depending of your font, the italic attribute may have no impact on your
        text rendering.

    :attr:`italic` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    underline = BooleanProperty(False)
    '''Adds an underline to the text.

    .. note::
        This feature requires the SDL2 text provider.

    .. versionadded:: 1.10.0

    :attr:`underline` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    strikethrough = BooleanProperty(False)
    '''Adds a strikethrough line to the text.

    .. note::
        This feature requires the SDL2 text provider.

    .. versionadded:: 1.10.0

    :attr:`strikethrough` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    padding_x = NumericProperty(0)
    '''Horizontal padding of the text inside the widget box.

    :attr:`padding_x` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.

    .. versionchanged:: 1.9.0
        `padding_x` has been fixed to work as expected.
        In the past, the text was padded by the negative of its values.
    '''

    padding_y = NumericProperty(0)
    '''Vertical padding of the text inside the widget box.

    :attr:`padding_y` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.

    .. versionchanged:: 1.9.0
        `padding_y` has been fixed to work as expected.
        In the past, the text was padded by the negative of its values.
    '''

    padding = ReferenceListProperty(padding_x, padding_y)
    '''Padding of the text in the format (padding_x, padding_y)

    :attr:`padding` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`padding_x`, :attr:`padding_y`) properties.
    '''

    halign = OptionProperty('auto', options=['left', 'center', 'right',
                            'justify', 'auto'])
    '''Horizontal alignment of the text.

    :attr:`halign` is an :class:`~kivy.properties.OptionProperty` and
    defaults to 'auto'. Available options are : auto, left, center, right and
    justify. Auto will attempt to autodetect horizontal alignment for RTL text
    (Pango only), otherwise it behaves like `left`.

    .. warning::

        This doesn't change the position of the text texture of the Label
        (centered), only the position of the text in this texture. You probably
        want to bind the size of the Label to the :attr:`texture_size` or set a
        :attr:`text_size`.

    .. versionchanged:: 1.10.1
        Added `auto` option

    .. versionchanged:: 1.6.0
        A new option was added to :attr:`halign`, namely `justify`.
    '''

    valign = OptionProperty('bottom',
                            options=['bottom', 'middle', 'center', 'top'])
    '''Vertical alignment of the text.

    :attr:`valign` is an :class:`~kivy.properties.OptionProperty` and defaults
    to 'bottom'. Available options are : `'bottom'`,
    `'middle'` (or `'center'`) and `'top'`.

    .. versionchanged:: 1.10.0
        The `'center'` option has been added as an alias of `'middle'`.

    .. warning::

        This doesn't change the position of the text texture of the Label
        (centered), only the position of the text within this texture. You
        probably want to bind the size of the Label to the :attr:`texture_size`
        or set a :attr:`text_size` to change this behavior.
    '''

    color = ListProperty([1, 1, 1, 1])
    '''Text color, in the format (r, g, b, a).

    :attr:`color` is a :class:`~kivy.properties.ListProperty` and defaults to
    [1, 1, 1, 1].
    '''

    outline_width = NumericProperty(None, allownone=True)
    '''Width in pixels for the outline around the text. No outline will be
    rendered if the value is None.

    .. note::
        This feature requires the SDL2 text provider.

    .. versionadded:: 1.10.0

    :attr:`outline_width` is a :class:`~kivy.properties.NumericProperty` and
    defaults to None.
    '''

    outline_color = ListProperty([0, 0, 0])
    '''The color of the text outline, in the (r, g, b) format.

    .. note::
        This feature requires the SDL2 text provider.

    .. versionadded:: 1.10.0

    :attr:`outline_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [0, 0, 0].
    '''

    disabled_outline_color = ListProperty([0, 0, 0])
    '''The color of the text outline when the widget is disabled, in the
    (r, g, b) format.

    .. note::
        This feature requires the SDL2 text provider.

    .. versionadded:: 1.10.0

    :attr:`disabled_outline_color` is a :class:`~kivy.properties.ListProperty`
    and defaults to [0, 0, 0].
    '''

    texture = ObjectProperty(None, allownone=True)
    '''Texture object of the text.
    The text is rendered automatically when a property changes. The OpenGL
    texture created in this operation is stored in this property. You can use
    this :attr:`texture` for any graphics elements.

    Depending on the texture creation, the value will be a
    :class:`~kivy.graphics.texture.Texture` or
    :class:`~kivy.graphics.texture.TextureRegion` object.

    .. warning::

        The :attr:`texture` update is scheduled for the next frame. If you need
        the texture immediately after changing a property, you have to call
        the :meth:`texture_update` method before accessing :attr:`texture`::

            l = Label(text='Hello world')
            # l.texture is good
            l.font_size = '50sp'
            # l.texture is not updated yet
            l.texture_update()
            # l.texture is good now.

    :attr:`texture` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    texture_size = ListProperty([0, 0])
    '''Texture size of the text. The size is determined by the font size and
    text. If :attr:`text_size` is [None, None], the texture will be the size
    required to fit the text, otherwise it's clipped to fit :attr:`text_size`.

    When :attr:`text_size` is [None, None], one can bind to texture_size
    and rescale it proportionally to fit the size of the label in order to
    make the text fit maximally in the label.

    .. warning::

        The :attr:`texture_size` is set after the :attr:`texture`
        property. If you listen for changes to :attr:`texture`,
        :attr:`texture_size` will not be up-to-date in your callback.
        Bind to :attr:`texture_size` instead.
    '''

    mipmap = BooleanProperty(False)
    '''Indicates whether OpenGL mipmapping is applied to the texture or not.
    Read :ref:`mipmap` for more information.

    .. versionadded:: 1.0.7

    :attr:`mipmap` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    shorten = BooleanProperty(False)
    '''
    Indicates whether the label should attempt to shorten its textual contents
    as much as possible if a :attr:`text_size` is given. Setting this to True
    without an appropriately set :attr:`text_size` will lead to unexpected
    results.

    :attr:`shorten_from` and :attr:`split_str` control the direction from
    which the :attr:`text` is split, as well as where in the :attr:`text` we
    are allowed to split.

    :attr:`shorten` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    shorten_from = OptionProperty('center', options=['left', 'center',
                                                     'right'])
    '''The side from which we should shorten the text from, can be left,
    right, or center.

    For example, if left, the ellipsis will appear towards the left side and we
    will display as much text starting from the right as possible. Similar to
    :attr:`shorten`, this option only applies when :attr:`text_size` [0] is
    not None, In this case, the string is shortened to fit within the specified
    width.

    .. versionadded:: 1.9.0

    :attr:`shorten_from` is a :class:`~kivy.properties.OptionProperty` and
    defaults to `center`.
    '''

    is_shortened = BooleanProperty(False)
    '''This property indicates if :attr:`text` was rendered with or without
    shortening when :attr:`shorten` is True.

    .. versionadded:: 1.10.0

    :attr:`is_shortened` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    split_str = StringProperty('')
    '''The string used to split the :attr:`text` while shortening the string
    when :attr:`shorten` is True.

    For example, if it's a space, the string will be broken into words and as
    many whole words that can fit into a single line will be displayed. If
    :attr:`split_str` is the empty string, `''`, we split on every character
    fitting as much text as possible into the line.

    .. versionadded:: 1.9.0

    :attr:`split_str` is a :class:`~kivy.properties.StringProperty` and
    defaults to `''` (the empty string).
    '''

    ellipsis_options = DictProperty({})
    '''Font options for the ellipsis string('...') used to split the text.

    Accepts a dict as option name with the value. Only applied when
    :attr:`markup` is true and text is shortened. All font options which work
    for :class:`Label` will work for :attr:`ellipsis_options`. Defaults for
    the options not specified are taken from the surronding text.

    .. code-block:: kv

        Label:
            text: 'Some very long line which will be cut'
            markup: True
            shorten: True
            ellipsis_options: {'color':(1,0.5,0.5,1),'underline':True}

    .. versionadded:: 2.0.0

    :attr:`ellipsis_options` is a :class:`~kivy.properties.DictProperty` and
    defaults to `{}` (the empty dict).
    '''

    unicode_errors = OptionProperty(
        'replace', options=('strict', 'replace', 'ignore'))
    '''How to handle unicode decode errors. Can be `'strict'`, `'replace'` or
    `'ignore'`.

    .. versionadded:: 1.9.0

    :attr:`unicode_errors` is an :class:`~kivy.properties.OptionProperty` and
    defaults to `'replace'`.
    '''

    markup = BooleanProperty(False)
    '''
    .. versionadded:: 1.1.0

    If True, the text will be rendered using the
    :class:`~kivy.core.text.markup.MarkupLabel`: you can change the
    style of the text using tags. Check the
    :doc:`api-kivy.core.text.markup` documentation for more information.

    :attr:`markup` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    refs = DictProperty({})
    '''
    .. versionadded:: 1.1.0

    List of ``[ref=xxx]`` markup items in the text with the bounding box of
    all the words contained in a ref, available only after rendering.

    For example, if you wrote::

        Check out my [ref=hello]link[/ref]

    The refs will be set with::

        {'hello': ((64, 0, 78, 16), )}

    The references marked "hello" have a bounding box at (x1, y1, x2, y2).
    These co-ordinates are relative to the top left corner of the text, with
    the y value increasing downwards. You can define multiple refs with the
    same name: each occurrence will be added as another (x1, y1, x2, y2) tuple
    to this list.

    The current Label implementation uses these references if they exist in
    your markup text, automatically doing the collision with the touch and
    dispatching an `on_ref_press` event.

    You can bind a ref event like this::

        def print_it(instance, value):
            print('User click on', value)
        widget = Label(text='Hello [ref=world]World[/ref]', markup=True)
        widget.on_ref_press(print_it)

    .. note::

        This works only with markup text. You need :attr:`markup` set to
        True.
    '''

    anchors = DictProperty({})
    '''
    .. versionadded:: 1.1.0

    Position of all the ``[anchor=xxx]`` markup in the text.
    These co-ordinates are relative to the top left corner of the text, with
    the y value increasing downwards. Anchors names should be unique and only
    the first occurrence of any duplicate anchors will be recorded.


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

        This works only with markup text. You need :attr:`markup` set to
        True.

    '''

    max_lines = NumericProperty(0)
    '''Maximum number of lines to use, defaults to 0, which means unlimited.
    Please note that :attr:`shorten` take over this property. (with
    shorten, the text is always one line.)

    .. versionadded:: 1.8.0

    :attr:`max_lines` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    strip = BooleanProperty(False)
    '''Whether leading and trailing spaces and newlines should be stripped from
    each displayed line. If True, every line will start at the right or left
    edge, depending on :attr:`halign`. If :attr:`halign` is `justify` it is
    implicitly True.

    .. versionadded:: 1.9.0

    :attr:`strip` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    font_hinting = OptionProperty(
        'normal', options=[None, 'normal', 'light', 'mono'], allownone=True)
    '''What hinting option to use for font rendering.
    Can be one of `'normal'`, `'light'`, `'mono'` or None.

    .. note::
        This feature requires SDL2 or Pango text provider.

    .. versionadded:: 1.10.0

    :attr:`font_hinting` is an :class:`~kivy.properties.OptionProperty` and
    defaults to `'normal'`.
    '''

    font_kerning = BooleanProperty(True)
    '''Whether kerning is enabled for font rendering. You should normally
    only disable this if rendering is broken with a particular font file.

    .. note::
        This feature requires the SDL2 text provider.

    .. versionadded:: 1.10.0

    :attr:`font_kerning` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    font_blended = BooleanProperty(True)
    '''Whether blended or solid font rendering should be used.

    .. note::
        This feature requires the SDL2 text provider.

    .. versionadded:: 1.10.0

    :attr:`font_blended` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''
