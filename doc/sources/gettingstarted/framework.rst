Non widgets stuff
-----------------

.. container:: Non widgets stuff

.. only:: html

    .. image:: images/animation.gif

:class:`Animation <kivy.animation.Animation>` and are used to change a Widget
properties (size/pos/center...), to a target value, in a target time, various
:class:`transition <kivy.animation.AnimationTransition>` functions are
provided. Using them, you can animate widgets and build very smoth UI
behaviours.

:class:`Atlas <kivy.atlas.Atlas>` is a class for managing texture maps, i.e.
packing multiple texture into one image. Using it allow to reduce the number of
images to load and speedup the application starting. 

:class:`Clock <kivy.clock.Clock>` provides you with a convenient way to do jobs
at set time intervals and is preffered over sleep() as sleep would block kivy
Event Loop. These intervals can be also set relative to the OpenGL Drawing
instructions, :ref:`before <schedule-before-frame>` or :ref:`after
<schedule-after-frame>` frame. Clock also provides you with a way to create
:ref:`triggered events <triggered-events>` that are clubbed togeather and only
called once before the next frame.

:class:`UrlRequest <kivy.network.urlrequest.UrlRequest>` is useful to do http
requests without blocking the event loop, and manage the result with callbacks.
