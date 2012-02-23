.. _designwithkv:

.. highlight:: python
    :linenothreshold: 3

Designing with the Kivy Language
============================

Let's start with a little example. First, the Python file named `main.py`:

.. include:: ../../../examples/guide/designwithkv/main.py
   :literal:

In this example, we are creating a Controller class, with 2 properties:

    * ``info`` for receving some text
    * ``label_wid`` for receving the label widget

In addition, we are creating a ``do_action()`` method, that will use both of
these properties. It will change the ``info`` text, and change text in the
``label_wid`` widget.

Executing this application without a corresponding `.kv` file will work, but
nothing will be shown on the screen. This is expected, because the
``Controller`` class has no widgets in it, it's just a ``FloatLayout``. We can
create the UI around the ``Controller`` class in a file named `controller.kv`,
which will be loaded when we run the ``ControllerApp``. How this is done and
what files are loaded is described in the :func:`kivy.app.App.load_kv` method.

.. include:: ../../../examples/guide/designwithkv/controller.kv
    :literal:

One label and one button in a vertical ``BoxLayout``. Seems very simple. There
are 3 things going on here:

    1. Using data from the ``Controller``. As soon as the ``info`` property is
       changed in the controller, the expression ``text: 'My controller info is
       : ' + root.info`` will automatically be re-evaluated, changing the text
       in the ``Button``.

    2. Giving data to the ``Controller``. The expression ``id: my_custom_label``
       is assigning the created ``Label`` the id of ``my_custom_label``. Then,
       using ``my_custom_label`` in the expression ``label_wid:
       my_custom_label`` gives the instance of that ``Label`` widget to your
       ``Controller``.

    3. Creating a custom callback in the ``Button`` using the ``Controller``'s
       ``on_press`` method.

        * ``root`` and ``self`` are reserved keywords, useable anywhere.
          ``root`` represents the top widget in the rule and ``self`` represents
          the current widget.

        * You can use any id declared in the rule the same as ``root`` and
          ``self``. For example, you could do this in the ``on_press()``::

            Button:
                on_press: root.do_action(); my_custom_label.font_size = 18

And that's that. Now when we run `main.py`, `controller.kv` will be loaded so
that the ``Button`` and ``Label`` will show up and respond to our touch events.

