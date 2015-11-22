'''
Behaviors
=========

.. versionadded:: 1.8.0

Behavior mixin classes
----------------------

This module implements behaviors that can be
`mixed in <https://en.wikipedia.org/wiki/Mixin>`_
with existing base widgets. The idea behind these classes is to encapsulate
properties and events associated with certain types of widgets.

Isolating these properties and events in a mixin class allows you to define your
own implementation for standard kivy widgets that can act as drop-in
replacements. This means you can re-style and re-define widgets as desired
without breaking compatibility: as long as they implement the behaviors
correctly, they can simply replace the standard widgets.

Adding behaviors
----------------

Say you want to add :class:`~kivy.uix.button.Button` capabilities to an
:class:`~kivy.uix.image.Image`, you could do::

    class IconButton(ButtonBehavior, Image):
        pass

This would give you an :class:`~kivy.uix.image.Image` with the events and
properties inherited from :class:`ButtonBehavior`. For example, the *on_press*
and *on_release* events would be fired when appropriate::

    class IconButton(ButtonBehavior, Image):
        def on_press(self):
            print("on_press")

Or in kv:

.. code-block:: kv

    IconButton:
        on_press: print('on_press')

Naturally, you could also bind to any property changes the behavior class
offers:

.. code-block:: python

        def state_changed(*args):
            print('state changed')

        button = IconButton()
        button.bind(state=state_changed)


.. note::

    The behavior class must always be _before_ the widget class. If you don't
    specify the inheritance in this order, the behavior will not work because
    the behavior methods are overwritten by the class method listed first.

    Similarly, if you combine a behavior class with a class which
    requires the use of the methods also defined by the behavior class, the
    resulting class may not function properly. For example, when combining the
    :class:`ButtonBehavior` with a :class:`~kivy.uix.slider.Slider`, both of
    which use the :meth:`~kivy.uix.widget.Widget.on_touch_up` method,
    the resulting class may not work properly.

.. versionchanged:: 1.9.1

    The individual behavior classes, previously in one big `behaviors.py`
    file, has been split into a single file for each class under the
    :mod:`~kivy.uix.behaviors` module. All the behaviors are still imported
    in the :mod:`~kivy.uix.behaviors` module so they are accessible as before
    (e.g. both `from kivy.uix.behaviors import ButtonBehavior` and
    `from kivy.uix.behaviors.button import ButtonBehavior` work).

'''

__all__ = ('ButtonBehavior', 'ToggleButtonBehavior', 'DragBehavior',
           'FocusBehavior', 'CompoundSelectionBehavior',
           'CodeNavigationBehavior', 'EmacsBehavior')

from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.behaviors.togglebutton import ToggleButtonBehavior
from kivy.uix.behaviors.drag import DragBehavior
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.behaviors.compoundselection import CompoundSelectionBehavior
from kivy.uix.behaviors.codenavigation import CodeNavigationBehavior
from kivy.uix.behaviors.emacs import EmacsBehavior
