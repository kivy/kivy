'''
Widgets
=======

A widget is an element of a graphical user interface.
The `kivy.uix` module contains classes for creating and managing Widgets.

Read first: :doc:`api-kivy.uix.widget`

- **UX widgets**: Classical user interface widgets, perfect and ready to be
  assembled to create more complex widgets.

    :doc:`api-kivy.uix.label`, :doc:`api-kivy.uix.button`,
    :doc:`api-kivy.uix.checkbox`,
    :doc:`api-kivy.uix.image`, :doc:`api-kivy.uix.slider`,
    :doc:`api-kivy.uix.progressbar`, :doc:`api-kivy.uix.textinput`,
    :doc:`api-kivy.uix.togglebutton`, :doc:`api-kivy.uix.switch`,
    :doc:`api-kivy.uix.video`

- **Layouts**: A layout widget has no rendering, just a trigger
  that will arrange its children in a specific way. Read more on
  :doc:`api-kivy.uix.layout`

    :doc:`api-kivy.uix.gridlayout`, :doc:`api-kivy.uix.boxlayout`,
    :doc:`api-kivy.uix.anchorlayout`, :doc:`api-kivy.uix.stacklayout`

- **Complex UX widgets**: Non-atomic widgets, result of classic widget
  combinations. We call them complex because the assembly and usages are not as
  generic as the classicals widgets.

    :doc:`api-kivy.uix.bubble`,
    :doc:`api-kivy.uix.filechooser`, :doc:`api-kivy.uix.popup`,
    :doc:`api-kivy.uix.tabbedpanel`, :doc:`api-kivy.uix.videoplayer`,
    :doc:`api-kivy.uix.vkeyboard`,

- **Behaviors widgets**: Theses widgets have no rendering, but act on the
  graphics part, or even on the interaction (touch) part.

    :doc:`api-kivy.uix.scatter`, :doc:`api-kivy.uix.stencilview`

All widgets which are not marked "experimental" are available for export
directly from the `kivy.uix` module. Thus you can use::

    from kivy.uix import Label, Button, FloatLayout, ...

Or, if you are exceptionally lazy, you can import all stable widgets and
layouts into your program using::

    from kivy.uix import *

----
'''

from kivy.uix.anchorlayout import *
from kivy.uix.boxlayout import *
from kivy.uix.bubble import *
from kivy.uix.button import *
from kivy.uix.camera import *
from kivy.uix.checkbox import *
from kivy.uix.floatlayout import *
from kivy.uix.gridlayout import *
from kivy.uix.image import *
from kivy.uix.label import *
from kivy.uix.popup import *
from kivy.uix.progressbar import *
from kivy.uix.scatter import *
from kivy.uix.scrollview import *
from kivy.uix.settings import *
from kivy.uix.slider import *
from kivy.uix.stacklayout import *
from kivy.uix.stencilview import *
from kivy.uix.switch import *
from kivy.uix.textinput import *
from kivy.uix.togglebutton import *
from kivy.uix.video import *
from kivy.uix.videoplayer import *
from kivy.uix.widget import *
