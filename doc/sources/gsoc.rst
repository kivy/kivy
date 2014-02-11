Google Summer of Code - 2014
============================

Kivy is hoping to participate in Google Summer of Code 2014


Projects ideas
--------------

Kivy
~~~~

* Embedded Support: Add full support for major embedded platforms like Beagle
  Board and Raspberry Pi. Kivy already has partial support for RPi. It would be
  great to get full support for other major embedded platforms.
* Inspector: Redo or improve the inspector module. Python has awesome
  introspection possibilities. Let's work together to have an awesome inspector
  that would allow the user to debug anything from their application.
* KV Language Compiler: The KV language is parsed and interpreted at runtime.
  If you run on an embedded device with low CPU resources (such as Raspberry
  Pi), you'll want to have faster loading and execution.
* Graphics Pipeline Enhancements: We have a lot of ideas around the graphics
  pipeline, like merging instructions or VBOs to reduce GL calls, helpers to
  create shaders dynamically according to the current vertex format, and
  improving 3D support.
* Kivy Game Engine: A lot of people are still wondering how they can create
  games on top of Kivy. Even if we have a good set of widgets, we still lack a
  good API for approaching gaming. Multiple parts could be improved, and new
  classes added, like a Sprite that subclasses a Rectangle, but can be rotated,
  scaled, etc. Or a Tiling manager. Or anything. A good knowledge of other game
  engines is required.


Mobile
~~~~~~

* Plyer: The idea is to provide a stable API to the user for accessing features
  of your desktop or mobile device, such as Accelerometer, GPS, SMS, Contact,
  and more. Under the hood, you'll use PyJNIus, PyOBJus, and Cython, to do what
  needs to be done. This probably would also include improving PyObjus and
  PyJnius to handle interfaces that they can't right now.
* SL4A Facades: Porting facades from Scripting Language for Android to Plyer
  for easy integration and compatability. 


Toolchain
~~~~~~~~~

* Python for Android: Enhance the project to support native Android interfaces,
  and not just a Kivy interface. The project can also be improved to create a
  binary release for users so they just have to call build.py.
* Toolchain for iOS: An iOS interface based on the idea of Python for Android,
  in order to replace kivy-ios. Cross-platform compilation skills are heavily
  required.
* Buildozer: Needs support for generating RPM, DEB, DMG, and EXE files. This,
  however, might not be enough in itself for a GSoC project. It would have to
  be joined together with some other work.
* SDL2 Backends: SDL2 providers for Kivy, including porting the mobile
  toolchains to SDL2. Part of the work is already done, so please contact the
  devs for further details. 


Applications
~~~~~~~~~~~~

* Website: A new Kivy website is required!


Anything Else ?
~~~~~~~~~~~~~~~

* Let your imagination run wild, and show what Kivy is capable of!


How to be a good student
------------------------

If you want to participate as a student and want to maximize your chances of
being accepted, start talking to us today and try fixing some smaller problems
to get used to our workflow. If we know you can work well with us, that'd be a
big plus.

Here's a checklist:

* Make sure to read through the website and at least skim the documentation.
* Look at the source code.
* Read our contribution guidelines.
* Pick an idea that you think is interesting from the ideas list or come up
  with your own idea.
* Do some research **yourself**. GSoC is not about us teaching you something
  and you getting paid for that. It is about you trying to achieve agreed upon
  goals by yourself with our support. The main driving force in this should be,
  obviously, yourself. Many students pop up and ask what they should do. Well,
  we don't know because we know neither your interests nor your skills. Show us
  you're serious about it and take the initiative.
* Write a draft proposal about what you want to do. Include what you understand
  the current state is (very roughly), what you would like to improve, how,
  etc.
* Discuss that proposal with us in a timely manner. Get feedback.
* Be patient! Especially on IRC. We will try to get to you if we're available.
  If not, send an email and just wait. Most questions are already answered in
  the docs or somewhere else and can be found with some research. If your
  questions don't reflect that you've actually thought through what you're
  asking, it might not be well received.
