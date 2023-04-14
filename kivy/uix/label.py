from kivy.core.text import Label as CoreLabel, DEFAULT_FONT
from kivy.core.text.markup import MarkupLabel as CoreMarkupLabel
from kivy.properties import StringProperty, OptionProperty, \
    NumericProperty, BooleanProperty, ListProperty, \
    ObjectProperty, DictProperty, ColorProperty, VariableListProperty
from kivy.utils import get_hex_from_color


	@@ -304,14 +304,14 @@ class Label(Widget):
    _font_properties = ('text', 'font_size', 'font_name', 'font_script_name',
                        'font_direction', 'bold', 'italic',
                        'underline', 'strikethrough', 'font_family', 'color',
                        'disabled_color', 'halign', 'valign', 'padding',
                        'outline_width', 'disabled_outline_color',
                        'outline_color', 'text_size', 'shorten', 'mipmap',
                        'line_height', 'max_lines', 'strip', 'shorten_from',
                        'split_str', 'ellipsis_options', 'unicode_errors',
                        'markup', 'font_hinting', 'font_kerning',
                        'font_blended', 'font_context', 'font_features',
                        'base_direction', 'text_language')

    def __init__(self, **kwargs):
        self._trigger_texture = Clock.create_trigger(self.texture_update, -1)
	@@ -321,11 +321,6 @@ def __init__(self, **kwargs):
        d = Label._font_properties
        fbind = self.fbind
        update = self._trigger_texture_update

        # NOTE: Compatibility code due to deprecated properties.
        fbind('padding_x', update, 'padding_x')
        fbind('padding_y', update, 'padding_y')

        fbind('disabled', update, 'disabled')
        for x in d:
            fbind(x, update, x)
	@@ -378,17 +373,8 @@ def _trigger_texture_update(self, name=None, source=None, value=None):
                self._label.options['outline_color'] = (
                    self.disabled_outline_color if value else
                    self.outline_color)

            # NOTE: Compatibility code due to deprecated properties
            # Must be removed along with padding_x and padding_y
            elif name == 'padding_x':
                self._label.options['padding'][::2] = [value] * 2
            elif name == 'padding_y':
                self._label.options['padding'][1::2] = [value] * 2

            else:
                self._label.options[name] = value

        self._trigger_texture()

    def texture_update(self, *largs):
	@@ -746,7 +732,7 @@ def on_ref_press(self, ref):
    defaults to False.
    '''

    padding_x = NumericProperty(0, deprecated=True)
    '''Horizontal padding of the text inside the widget box.
    :attr:`padding_x` is a :class:`~kivy.properties.NumericProperty` and
	@@ -755,12 +741,9 @@ def on_ref_press(self, ref):
    .. versionchanged:: 1.9.0
        `padding_x` has been fixed to work as expected.
        In the past, the text was padded by the negative of its values.
    .. deprecated:: 2.2.0
        Please use :attr:`padding` instead.
    '''

    padding_y = NumericProperty(0, deprecated=True)
    '''Vertical padding of the text inside the widget box.
    :attr:`padding_y` is a :class:`~kivy.properties.NumericProperty` and
	@@ -769,23 +752,13 @@ def on_ref_press(self, ref):
    .. versionchanged:: 1.9.0
        `padding_y` has been fixed to work as expected.
        In the past, the text was padded by the negative of its values.
    .. deprecated:: 2.2.0
        Please use :attr:`padding` instead.
    '''

    padding = VariableListProperty([0, 0, 0, 0], lenght=4)
    '''Padding of the text in the format [padding_left, padding_top,
    padding_right, padding_bottom]
    ``padding`` also accepts a two argument form [padding_horizontal,
    padding_vertical] and a one argument form [padding].
    .. versionchanged:: 2.2.0
        Replaced ReferenceListProperty with VariableListProperty.
    :attr:`padding` is a :class:`~kivy.properties.VariableListProperty` and
    defaults to [0, 0, 0, 0].
    '''

    halign = OptionProperty('auto', options=['left', 'center', 'right',
	@@ -1177,3 +1150,12 @@ def print_it(instance, value):
    :attr:`font_blended` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''
    responsive = BooleanProperty(False)
    '''
        It uses loop to determine best fit and can have more power consumption when enabled.
    .. versionadded:: 1.10.0
    :attr:`responsive` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

