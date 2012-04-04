Non widgets stuff
-----------------

.. container:: Non widgets stuff

what is an animation (and a gif to go with it)
**Animation** and AnimationTransition are used to animate Widget properties(size/pos/center...), in a sequential http://kivy.org/docs/api-kivy.animation.html#sequential-animation or parallel http://kivy.org/docs/api-kivy.animation.html#parallel-animation order.

**Atlas**: Atlas is a class for managing textures atlases: packing multiple texture into one. With it, you are reducing the number of image to load and speedup the application loading. For an in-depth look at the atlas look in http://kivy.org/docs/api-kivy.atlas.html

**Clock** http://kivy.org/docs/api-kivy.clock.htm
Clock provides you with a convinenient way to do jobs at set intervals and is preffered over sleep() as sleep tends to block kivy's Event Loop. These intervals can be also set relative to the OpenGL Drawing instructions, a.k.a draw before/after frame http://kivy.org/docs/api-kivy.clock.html#schedule-before-frame . Clock also provides you with a way to create triggered events http://kivy.org/docs/api-kivy.clock.html#triggered-events , that are clubbed togeather and only called once before the next frame.

