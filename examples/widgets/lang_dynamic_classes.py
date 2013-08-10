# Dynamic kv classes

from kivy.lang import Builder
from kivy.base import runTouchApp

root = Builder.load_string('''
<ImageButton@Button>:
    source: None
    Image:
        source: root.source
        center: root.center

ImageButton:
    source: 'kivy/data/logo/kivy-icon-512.png'
''')

runTouchApp(root)
