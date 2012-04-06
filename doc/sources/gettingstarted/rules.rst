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

That's it, that's how simple it is to design your GUI in kv language. To get a more in-depth understanding look at :doc:`/guide/kvlang`