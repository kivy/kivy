"""
svg_layers.py
-------------
Demonstrates per-layer visibility and opacity control on a multi-layer SVG
using SvgWidget.  The SVG is embedded directly and
contains four named layers:

  background  - solid dark-blue rectangle
  sun         - yellow circle (top-right)
  mountains   - green/teal mountain shapes
  foreground  - dark silhouette foreground strip with a tree

Use the checkboxes to show/hide each layer and the sliders to adjust opacity.

Run from the repo root::

    python examples/svg/svg_layers.py
"""

# --------------------------------------------------------------------------- #
#  Embedded SVG - four clearly distinct layers with id attributes             #
# --------------------------------------------------------------------------- #

SVG_SRC = b"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 250" width="400" height="250">

  <!-- Layer 1: sky / background -->
  <rect id="background" x="0" y="0" width="400" height="250" fill="#1a6bb5"/>

  <!-- Layer 2: sun -->
  <circle id="sun" cx="320" cy="60" r="45" fill="#f5c518"/>

  <!-- Layer 3: mountains - three triangles as a single path so ThorVG can
       address them by id.  ThorVG does not reliably assign ids to g groups
       so leaf shapes must be used instead. -->
  <path id="mountains"
        d="M0,210 L80,90 L160,210 Z
           M80,210 L180,70 L280,210 Z
           M180,210 L300,80 L400,210 Z"
        fill="#3a9e78"/>

  <!-- Layer 4: foreground silhouette - ground strip, tree trunk, and canopy
       combined into a single path for the same reason. -->
  <path id="foreground"
        d="M0,210 L400,210 L400,250 L0,250 Z
           M93,175 L107,175 L107,215 L93,215 Z
           M100,120 L70,180 L130,180 Z"
        fill="#0d2b1a"/>

</svg>
"""

# --------------------------------------------------------------------------- #
#  Kivy app                                                                   #
# --------------------------------------------------------------------------- #

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, ScissorPush, ScissorPop
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

KV = '''
<ControlsRow>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '44dp'
    spacing: 8
    padding: 4, 4
    Label:
        text: root.label_text
        size_hint_x: None
        width: 120
        halign: 'right'
        valign: 'middle'
        text_size: self.size
    CheckBox:
        size_hint_x: None
        width: 36
        activated: True
        on_activated: root.on_visible(self.activated)
    Slider:
        id: sld
        min: 0.0
        max: 1.0
        value: 1.0
        on_value: root.on_opacity(self.value)
    Label:
        text: '{:.2f}'.format(sld.value)
        size_hint_x: None
        width: 42

BoxLayout:
    orientation: 'horizontal'
    RelativeLayout:
        CheckeredBackground:
        SvgWidget:
            id: svg
            source: app.svg_src
            size_hint: None, None
            size: self.viewbox_size
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}

    BoxLayout:
        id: panel
        orientation: 'vertical'
        size_hint_x: None
        width: '400dp'
        padding: 12, 12
        spacing: 8

        Label:
            text: 'Layer Controls'
            size_hint_y: None
            height: 36
            bold: True
            font_size: '16sp'

        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: 24
            spacing: 8
            padding: 4, 0
            Label:
                text: 'Layer'
                size_hint_x: None
                width: 120
                color: 0.7, 0.7, 0.7, 1
                text_size: self.size
                halign: 'right'
                valign: 'middle'
            Label:
                text: 'Vis'
                size_hint_x: None
                width: 36
                color: 0.7, 0.7, 0.7, 1
            Label:
                text: 'Opacity'
                color: 0.7, 0.7, 0.7, 1
            Label:
                text: 'Val'
                size_hint_x: None
                width: 42
                color: 0.7, 0.7, 0.7, 1
'''


class ControlsRow(BoxLayout):
    """One row in the control panel: label | checkbox | opacity slider | value."""

    svg_widget = ObjectProperty(None, allownone=True)
    layer_id = StringProperty()
    label_text = StringProperty()

    def on_visible(self, activated):
        if self.svg_widget:
            self.svg_widget.set_element_visible(self.layer_id, activated)

    def on_opacity(self, value):
        if self.svg_widget:
            self.svg_widget.set_element_opacity(self.layer_id, value)


class CheckeredBackground(Widget):
    """Draws a grey checkerboard so transparency in the SVG is visible."""

    TILE = dp(20)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *_):
        self.canvas.before.clear()
        tile = self.TILE
        with self.canvas.before:
            ScissorPush(x=int(self.x), y=int(self.y),
                        width=int(self.width), height=int(self.height))
            for row in range(int(self.height / tile) + 2):
                for col in range(int(self.width / tile) + 2):
                    x = self.x + col * tile
                    y = self.y + row * tile
                    light = (row + col) % 2 == 0
                    Color(0.75, 0.75, 0.75, 1) if light else Color(0.55, 0.55, 0.55, 1)
                    Rectangle(pos=(x, y), size=(tile, tile))
            ScissorPop()


class SvgLayersApp(App):
    svg_src = SVG_SRC

    def build(self):
        Window.size = (960, 400)
        Window.clearcolor = (0.15, 0.15, 0.15, 1)

        root = Builder.load_string(KV)
        root.ids.svg.bind(on_load=self.on_svg_loaded)
        return root

    def on_svg_loaded(self, svg):
        """ Build the control panel based on the element ids in the SVG. """
        panel = self.root.ids.panel
        element_ids = svg.get_element_ids()
        for element_id in element_ids:
            panel.add_widget(ControlsRow(
                svg_widget=svg,
                layer_id=element_id,
                label_text=element_id.title(),
            ))

        panel.add_widget(Widget())  # spacer




if __name__ == '__main__':
    SvgLayersApp().run()
