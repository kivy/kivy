Google Summer of Code - 2014
============================

Kivy is hoping to participate in Google Summer of Code 2014.
This page showcases some ideas for gsoc projects and corresponding
guidelines to get students familiar with contributing towards the
kivy framework.

Requirements
------------
It is assumed that the incoming student be familiar with some basic
skills as highlighted here:

* Intermediate level familiarity with python
* Student should be fairly comfortable with git and github
  (Kivy and its sister projects are all managed on github)
* Comfortable with Event Driven programming.
* Preset development environment for kivy or the appropriate
  sister project you are going to work on. For example to be
  able to work on pyobjus/pyjnius/plyer you would need access
  to an iOS device, mac with xcode and a developer license,
  android device respectively.
  
Additional desired skills may be listed with specific projects.

Familiarize yourself with the contributing guide http://kivy.org/docs/contribute.html 
We can help you get up to speed, however students demonstrating ability
in advance would be given preference.


Projects ideas
--------------

THIS SECTION IS a WIP. The mentors list is not yet final.

Kivy
~~~~

* Embedded Support:
    - Mentors: Gabriel Pettier, Mathieu Virbel
    - Requirements: Access to specific embedded hardware.
    - Task level: Intermediate/Advanced
    - Desired Skills: Familiarity with programming on the specific embedded hardware.

  Add full support for major embedded platforms like Beagle
  Board and Raspberry Pi. Kivy already has partial support for RPi. It would be
  great to get full support for other major embedded platforms.

* Inspector: 
    - Mentors: Akshay Arora
    - Task level: Intermediate

  Redo or improve the inspector module. Python has awesome
  introspection possibilities. Let's work together to have an awesome inspector
  that would allow the user to debug anything from their application.

* Graphics Pipeline Enhancements:
      - Mentors: Jacob Kovac, Mathieu Virbel
      - Task level: Intermediate/Advanced
      - Desired Skills: Familiarity with OpenGL, desire to learn/solve difficult
        concepts/puzzles.
  
  We have a lot of ideas around the graphics
  pipeline, like merging instructions or VBOs to reduce GL calls, helpers to
  create shaders dynamically according to the current vertex format, and
  improving 3D support.


Mobile
~~~~~~

* Plyer:
    - Mentors: Gabriel Pettier, Akshay Arora, Alexander Taylor, Ben Rousch.
    - Requirements: Access to Linux, Windows, OS X, iOS device, Android device.
    - Task level: Intermediate/Advanced.
    - Desired Skills: Familiarity with Pyjnius, PyObjus.

  The idea is to provide a stable API to the user for accessing features
  of their desktop or mobile device, such as Accelerometer, GPS, SMS, Contact,
  and more. Under the hood you'll use PyJNIus, PyOBJus and Cython. This probably
  would also include improving PyObjus and PyJnius to handle interfaces that
  they can't right now.

* SL4A Facades:
    - Mentors: Gabriel Pettier, Akshay Arora, Mathieu Virbel

  Porting facades from Scripting Language for Android to Plyer
  for easy integration and compatability. 


Toolchain
~~~~~~~~~

* Toolchain for iOS:
    - Mentors: Thomas Hansen, Mathieu Virbel
    - Reuirements: Access to iOS, Android device along with a developer licence.
    - Task level: Intermediate/Advanced
    - Desired Skills: Familiarity with xcode, objc.

  An iOS interface based on the idea of Python for Android,
  in order to replace kivy-ios. Cross-platform compilation skills are heavily
  required.

* Buildozer:
    - Mentors: Gabriel Pettier, Akshay Arora, Alexander Taylor, Ben Rousch
    - Requirements: Access to linux, Windows, OS X, iOS, Android.
    - Task level: Intermediate

  Needs support for generating RPM, DEB, DMG, and EXE files. This might not be
  enough in itself for a GSoC project. It would have to be joined together with 
  some other work.

* SDL2 Backends:
    - Mentors: Akshay Arora, Jacob Kovac, Mathieu Virbel
    - Requirements: Access to Linux, Windows, OS X, iOS, Android.
    - Task level: Intermediate/Advanced

  SDL2 providers for Kivy, including porting the mobile
  toolchains to SDL2. Part of the work is already done, so please contact the
  devs for further details. 



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
  
  [1]:http://en.wikipedia.org/wiki/Event-driven_programming
