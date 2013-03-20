Kv Design Language
------------------

.. container:: title

    Designing with the kv language.

Kivy provides a design language specifically geared towards ease of GUI Design,
which makes it easier to separate interface design and logic from internal design and
logic. For example:

.. image:: ../images/gs-lang.png
    :align: center
    :height: 229px

In the above code :

.. code-block:: kv

    <LoginScreen>:  # every class in your app can be represented by a rule like this in the kv file
        GridLayout: # this is how you add your widget/layout to the parent (note the indentation).
            rows: 2 # this how you set each property of your widget/layout

That's it, that's how simple it is to design your GUI in the kv language. To get a
more in-depth understanding look at :doc:`/guide/lang`
