Drawing
-------
.. container:: title

    Graphics Instructions, Canvas

Each widget has a canvas, i.e. a place to draw on. The canvas is a group of instructions that should be executed whenever there is a change to the widget's graphics representation. You can add two types of instructions to the canvas, context instructions and vertex instructions. You can put instructions either from python or from kv (preffered way). If you add them from kv, the advantage is that they are automatically updated when any property they depend on changes. In python, you need to do this yourself.

.. image:: ../images/gs-drawing.png

In both cases the canvas of the MyWidget is re-drawn whenever the ``position`` or the ``size`` of the widget changes.

You can use **canvas.before** or **canvas.after** . This allows you to seperate your instructions based on when you want each to happen.

For an in depth look at how Kivys Graphics are handled, look `here <http://kivy.org/docs/api-kivy.graphics.html>`_
