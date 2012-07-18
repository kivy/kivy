Non-widget stuff
-----------------

.. container:: title

    Kivy FrameWork

.. |animation_img| image:: ../images/gs-animation.gif

.. |animation_text| replace:: :class:`Animation <kivy.animation.Animation>` is used to change a Widget's properties (size/pos/center...), to a target value, in a target time.
    Various :class:`transition <kivy.animation.AnimationTransition>` functions are provided. 
    Using them, you can animate widgets and build very smooth UI behaviours.

.. |atlas_img| image:: ../images/gs-atlas.png

.. |atlas_text| replace:: :class:`Atlas <kivy.atlas.Atlas>` is a class for managing texture maps, i.e. packing multiple textures into one image. Using it allows you to reduce the number of images to load and speed up the application start.

.. |clock_text| replace:: :class:`Clock <kivy.clock.Clock>` provides you with a convenient way to do jobs at set time intervals and is preferred over *sleep()*  which would block the kivy Event Loop. These intervals can be set relative to the OpenGL Drawing instructions, :ref:`before <schedule-before-frame>` or :ref:`after <schedule-after-frame>` frame.  Clock also provides you with a way to create :ref:`triggered events <triggered-events>` that are grouped together and only called once before the next frame.

.. |sched_once| replace:: `Clock.schedule_once <http://kivy.org/docs/api-kivy.clock.html?highlight=clock#kivy.clock.ClockBase.schedule_once>`__
.. |sched_intrvl| replace:: `Clock.schedule_interval <http://kivy.org/docs/api-kivy.clock.html?highlight=clock#kivy.clock.ClockBase.schedule_interval>`__
.. |unsched| replace:: `Clock.unschedule <http://kivy.org/docs/api-kivy.clock.html?highlight=clock#kivy.clock.ClockBase.unschedule>`__
.. |trigger| replace:: `Clock.create_trigger <http://kivy.org/docs/api-kivy.clock.html?highlight=clock#kivy.clock.ClockBase.create_trigger>`__
.. |urlreq| replace:: :class:`UrlRequest <kivy.network.urlrequest.UrlRequest>` is useful to do asynchronous requests without blocking the event loop, and manage the result and progress with callbacks.

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
