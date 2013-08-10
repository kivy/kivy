Google Summer of Code - 2013
============================

Kivy is hoping to participate in Google Summer of Code 2013.


Projects ideas
--------------

Kivy
~~~~

* Kivy language compiler - our language is parsed and interpreted at runtime.
  If you run on an embed device with low cpu resources (such as Raspberry Pi),
  you want to have a faster loading and execution
* Graphics pipeline enhancements - we have lot of ideas around the graphics
  pipeline, like merging instructions / vbos to reduce gl call, helpers to
  create dynamically shaders according to the current vertex format / improve
  the 3D support
* Enhance Kivy to be a good game-engine - a lot of peoples are still wondering
  how they can create game in top of kivy. Even if we have a good set of
  widgets, we still lack of good API for a gaming approach. Multiple part could
  be improved, and new classes added, just as a Sprite that subclass a
  Rectangle, but can be rotated, scaled, etc. Or a Tiling manager. Or anything.
  A good knownledge of others game engine is required.
* Widget and application serialization - this is a recurent project, but nobody
  has really tackle the idea yet. Kivy widgets cannot be serialized, yet. It
  would be nice if you could "save" your part of your widget tree, and restore
  it later, and transmit it over the web. Serialization open also the doors to
  collaborative widget.
* Inspector - redo / improve the inspector module. Python have an awesome
  introspection possibilities. Let's work together to have an awesome inspector
  that would allow the user to debug anything from its application.
* ListView / GridView work and the generalization of the selection / adapter
  (and "controller") system. Goal would be two-fold: 1) improving ListView and
  bring GridView in; 2) extending a general selection / adapter (and
  "controller") approach to other widgets where appropriate. There is already a
  good start for ListView, but it needs fleshing out for layout and resizing
  improvements.  GridView has a substantial start:
  https://github.com/geojeff/kivy/tree/uix-gridview. 

Mobile
~~~~~~

* Plyer - the idea is to provide an stable API to the user for accessing to any
  feature of your desktop or mobile, such as Accelerometer, GPS, SMS, Contact,
  and more. Under the hood, you'll use PyJNIus, PyOBJus, Cython, to do what it
  need to be done.
* PyOBJus - access to Objective C from Python. That will allow any python
  project to access to anything in the objective C API. The project is not
  working yet, and a good knowledge to Objective C and C is required. This base
  is required to access to GPS, Accelerometer, SMS, Contacts from your iPhone
  or iPad from Python.

Toolchain
~~~~~~~~~

* Python for android - enhance the project to support native android interface,
  and not just Kivy interface. The project can also be improved to release
  binary for users, and they just have to call build.py.
* Create a new toolchain for iOS - based on the idea of Python for android, in
  order to replace kivy-ios. Cross-platform compilation skills are heavilly
  required.
* Kivy in HTML5 - we already have a POC internally for compiling Python, SDL,
  SDLimage, etc... into javascript. We could go further on this POC, if a good
  student with awesome skills on javascript, python and cross compilation come
  to us :)


Applications
~~~~~~~~~~~~

* A kivy designer - we tackle this idea last year, without success. A lot of
  users would love to have a designer for create screen of their application:
  add widgets element on a page, reorder the tree, editing properties, attach
  kv lang to it, and test in real time.
* For the scope of a GSOC project, perhaps it is better not to have a specific
  app, such as the Designer app, as a target. Rather, focus could be put on
  kivy-statecharts, https://github.com/kivy/kivy-statecharts/, which would be a
  great help to app development in general, and is a very good fit for the
  Designer app.  This project would involve: 1) improving the Kivy statecharts
  framework and its documentation;  2) targeting app examples, including the
  Designer app, for illustration purposes and for their advancement toward
  working apps. There has been discussion of writing statecharts documentation
  as an advanced section for Kivy docs.
* Website - a new Kivy website is required!


Anything else ?
~~~~~~~~~~~~~~~

Let your imagination run wild, and show what Kivy is capable off!


How to be a good student
------------------------

If you want to participate as a student and want to maximize your chances of
beeing accepted, start talking to us today and try fixing some smaller problems
to get used to our workflow. If we know you can work well with us, that'd be a
big plus.

Here's a checklist:

* Make sure to read through the website and at least skim the documentation.
* Look at the source code.
* Read our contribution guidelines.
* Pick an idea that you think is interesting from the ideas list (see link
  above) or come up with your own idea.
* Do some research **yourself**. GSoC is not about us teaching you something
  and you getting paid for that. It is about you trying to achieve agreed upon
  goals by yourself with our support. The main driving force in this should be,
  obviously, yourself. Many students come up and ask what they should do. Well,
  we don't know because we know neither your interests nor your skills. Show us
  you're serious about it and take initiative.
* Write a draft proposal about what you want to do. Include what you understand
  the current state is (very roughly), what you would like to improve and how,
  etc.
* Discuss that proposal with us in a timely manner. Get feedback.
* Be patient! Especially on IRC. We will try to get to you if we're available.
  If not, send an email and just wait. Most questions are already answered in
  the docs or somewhere else and can be found with some research. If your
  questions don't reflect that you've actually thought through what you're
  asking, it might not be well received.
