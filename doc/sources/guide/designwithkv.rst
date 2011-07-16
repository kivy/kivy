.. _designwithkv:

.. highlight:: python
    :linenothreshold: 3

Designing with Kivy language
============================

Let's start with a little example. First, the Python file named `main.py`:

.. include:: ../../../examples/guide/designwithkv/main.py
   :literal:

In this example, we are creating a Controller class, with 2 properties:

    * `info` for receving some text
    * `label_wid` for receving the label widget

In addition, we are creating a `do_action()` method, that will use both of
theses properties: change the `info` text, and use `label_wid` to change the
content of the label with a nex text.

If you execute that application without kv, it will work... but nothing will be
showed on the screen. That's normal: `Controller` class have no widget in it,
it's just a Layout. We can now create a kv file and create the UI around the
`Controller` class in a file named `controller.kv`. The relation between the
previous file and the kv is described in the :class:`kivy.app.App` class.

.. include:: ../../../examples/guide/designwithkv/controller.kv
    :literal:

Yes, one label and one button in a vertical boxlayout. Seem very simple. Now, we have 2 things here:

    1. Use data from `Controller`: that's the goal of `info` property: as soon
       as the property is changed in the controller, the kv part that use it
       will be automatically re-evaluated, and change the button text.

    2. Give data to `Controller`: the first assignation `label_wid:
       my_custom_label` is to assign a new value to the `label_wid` property.
       Using id, you can give the instance of one of your widget to the
       `Controller`.

Also, we are creating a custom callback in the `Button` using `on_press`. Remember that:

    * `root` and `self` are 2 reserved keyword, that can be used anywhere for
      evaluation. `root` represent the top widget in the rule and `self`
      represent the current widget.

    * you can use any id declared in the rule same as `root` and `self`. For example, you could do in on_press::

        Button:
            on_press: root.do_action(); my_custom_label.font_size = 18


