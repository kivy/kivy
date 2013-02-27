Non-widget stuff
-----------------

.. container:: title

    Kivy FrameWork

.. |animation_img| image:: ../images/gs-animation.gif

.. |animation_text| replace:: :class:`Animation <kivy.animation.Animation>` is used to change a Widget's properties
    (size/pos/center...), to a target value, in a target time.
    Various :class:`transition <kivy.animation.AnimationTransition>` functions are provided. 
    Using them, you can animate widgets and build very smooth UI behaviours.

.. |atlas_img| image:: ../images/gs-atlas.png

.. |atlas_text| replace:: :class:`Atlas <kivy.atlas.Atlas>` is a class for managing texture maps, i.e. packing multiple
    textures into one image. Using it allows you to reduce the number of images to load and speed up the application 
    start.

.. |clock_text| replace:: :class:`Clock <kivy.clock.Clock>` provides you with a convenient way to do jobs at set time
    intervals and is preferred over *sleep()*  which would block the kivy Event Loop. These intervals can be set 
    relative to the OpenGL Drawing instructions, :ref:`before <schedule-before-frame>` 
    or :ref:`after <schedule-before-frame>` frame.  Clock also provides you with a way to create 
    :ref:`triggered events <triggered-events>` that are grouped together and only called once before the next frame.

.. |sched_once| replace:: :meth:`~kivy.clock.ClockBase.schedule_once`
.. |sched_intrvl| replace:: :meth:`~kivy.clock.ClockBase.schedule_interval`
.. |unsched| replace:: :meth:`~kivy.clock.ClockBase.unschedule`
.. |trigger| replace:: :meth:`~kivy.clock.ClockBase.create_trigger`
.. |urlreq| replace:: :class:`UrlRequest <kivy.network.urlrequest.UrlRequest>` is useful to do asynchronous requests 
    without blocking the event loop, and manage the result and progress with callbacks.

+------------------+------------------+
| |animation_text| |   |animation_img||
+------------------+------------------+
| |atlas_text|     |     |atlas_img|  |
+------------------+------------------+
| |clock_text|     | - |sched_once|   |
|                  | - |sched_intrvl| |
|                  | - |unsched|      |
|                  | - |trigger|      |
+------------------+------------------+
| |urlreq|         |                  |
+------------------+------------------+
