'''
Widgets
=======

Widgets are elements of a graphical user interface that form part of the
`User Experience <http://en.wikipedia.org/wiki/User_experience>`_.
The `kivy.uix` module contains classes for creating and managing Widgets.
Please refer to the :doc:`api-kivy.uix.widget` documentation for further
information.

Kivy widgets can be categorized as follows:

- **UX widgets**: Classical user interface widgets, ready to be assembled to
  create more complex widgets.

    :doc:`api-kivy.uix.label`, :doc:`api-kivy.uix.button`,
    :doc:`api-kivy.uix.checkbox`,
    :doc:`api-kivy.uix.image`, :doc:`api-kivy.uix.slider`,
    :doc:`api-kivy.uix.progressbar`, :doc:`api-kivy.uix.textinput`,
    :doc:`api-kivy.uix.togglebutton`, :doc:`api-kivy.uix.switch`,
    :doc:`api-kivy.uix.video`

- **Layouts**: A layout widget does no rendering but just acts as a trigger
  that arranges its children in a specific way. Read more on
  :doc:`Layouts here <api-kivy.uix.layout>`.

    :doc:`api-kivy.uix.anchorlayout`, :doc:`api-kivy.uix.boxlayout`,
    :doc:`api-kivy.uix.floatlayout`,
    :doc:`api-kivy.uix.gridlayout`, :doc:`api-kivy.uix.pagelayout`,
    :doc:`api-kivy.uix.relativelayout`, :doc:`api-kivy.uix.scatterlayout`,
    :doc:`api-kivy.uix.stacklayout`

- **Complex UX widgets**: Non-atomic widgets that are the result of
  combining multiple classic widgets.
  We call them complex because their assembly and usage are not as
  generic as the classical widgets.

    :doc:`api-kivy.uix.bubble`, :doc:`api-kivy.uix.dropdown`,
    :doc:`api-kivy.uix.filechooser`, :doc:`api-kivy.uix.popup`,
    :doc:`api-kivy.uix.spinner`,
    :doc:`api-kivy.uix.listview`,
    :doc:`api-kivy.uix.tabbedpanel`, :doc:`api-kivy.uix.videoplayer`,
    :doc:`api-kivy.uix.vkeyboard`,

- **Behaviors widgets**: These widgets do no rendering but act on the
  graphics instructions or interaction (touch) behavior of their children.

    :doc:`api-kivy.uix.scatter`, :doc:`api-kivy.uix.stencilview`

- **Screen manager**: Manages screens and transitions when switching
  from one to another.

    :doc:`api-kivy.uix.screenmanager`

----
'''
