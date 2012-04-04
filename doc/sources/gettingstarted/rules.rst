Kv Design Language
-------------------

.. container:: title

    Designing through kv language.

Kivy provides a design language specifically geared towards ease of GUI Design, seperating the interface design part of your App from the rest. for example.
To create a username/passsword accepting feilds, do this in your kv file :

.. code-block:: kv
    #:kivy 1.1.2
    <MyAppClass>
        GridLayout:
            rows: 2
            cols: 2
            Label:
                text: 'User Name:'
            TextInput:
            Label:
                text: 'Password:'
            TextInput:
                password: True

In the above code :

.. code-block:: kv

    <MyappClass>    # every class in your app can be represented by a rule like this in the kv file
        GridLayout: # this is how you add your widget/layout to the parent note the indentation.
            rows: 2 # this how you set each property of your widget

An important thing to note here is that when you set a property in your ``kv`` language like ``row: 2`` one of two things happen.
If the value(the part that comes after the ``:``) has no variables then what happens is a normal assignment like ``gridlayout_obj.rows = 2`` .
However, if the value part has one or more variables in it then the property/field(the part to the left of ``:``) is updated whenever any of the variables on the right change.
For example consider this:

.. code-block:: kv

    pos: self.center_x - self.texture_size[0] / 2., self.center_y - self.texture_size[1] / 2.

This expression listens for a change in center_x, center_y, and texture_size. If one of them is changing, the expression will be re-evaluated, and update the ``pos`` field.

You can also handle ``on_`` events inside your kv language. For example the TextInput class has a ``focus`` property whose auto-generated ``on_focus`` event can be accessed inside the kv language like so:

.. code-block:: kv

    TextInput:
        on_focus: Print args

The ``args`` is a list of arguments passed to the ``on_focus`` event.

To define a new property in you class through kv language:

.. code-block:: kv

    <MyAppClass>
        myNewProperty: 'my new property value'

Now you can access this new property in your .py file like so::

    my_app_class_instance.myNewProperty

To change the appearance of any widget inside the kv language you can use the canvas property like so:

.. code-block:: kv

    Button:
        text: 'Hello World!'
        canvas:
            Color:
                rgba: 0, 1, 0, 1

For an in depth look at the kv design language look at http://kivy.org/docs/guide/kvlang.html

Please note that if you want to call from kv lang a widget you defined from python. you need to register it from python, using the `Factory` object.
