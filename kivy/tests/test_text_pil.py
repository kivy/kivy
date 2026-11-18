'''The PIL provider must not pass line or paragraph separators to Pillow.

libraqm 0.11, bundled with Pillow 13, rejects them, so measuring the
``'\\n'`` tokens that TextInput produces raised
``RuntimeError: raqm_layout() failed.``
'''

import pytest

from kivy.tests.common import requires_graphics

LINE_BREAKS = ['\n', '\r', '\x1c', '\x1d', '\x1e', '\x85', '\u2029']


@pytest.fixture
def pil_label_class():
    try:
        from kivy.core.text.text_pil import LabelPIL
    except ImportError:
        pytest.skip('pil text provider is not available')
    return LabelPIL


@pytest.mark.parametrize('char', LINE_BREAKS, ids=repr)
def test_line_break_is_not_measured(pil_label_class, char):
    label = pil_label_class(font_size=20)
    assert label.get_extents('a' + char + 'b') == label.get_extents('ab')
    assert label.get_extents(char)[0] == 0


@pytest.mark.parametrize('char', LINE_BREAKS, ids=repr)
@requires_graphics
def test_text_with_line_break_renders(pil_label_class, char):
    label = pil_label_class(text='a' + char + 'b', font_size=20)
    label.refresh()
    assert label.texture is not None
