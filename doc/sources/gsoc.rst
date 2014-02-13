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


The mentors list is only of potential mentors for a particular project and not final.

Kivy
~~~~

* Embedded Support:

  Description:
    Add full support for major embedded platforms like Beagle Board and Raspberry Pi.
    Kivy already has partial support for RPi. It would be
    great to get full support for other major embedded platforms.
  
  This would involve:
    - Native Keyboard Provider.
    - Window prvider for Beagle board using hooks to the driver for hardware
      acceleration inspiration can be taken from the rpi window provier
      https://github.com/kivy/kivy/blob/master/kivy/core/window/window_egl_rpi.py.
    - Making sure at least one of the backend for each of the core providers work on
      the embedded hardware with acceptable performnce. Namely Text, Window, Audio,
      Video, Keyboard, Clipboard, Image.
  Reference: 
      https://github.com/kivy/kivy/blob/master/kivy/core/window/window_egl_rpi.py.
      http://kivy.org/docs/api-kivy.core.html
      http://kivy.org/docs/guide/architecture.html#architecture
      http://kivy.org/docs/guide/architecture.html#providers
      
  Expected Outcome:
    Full Working support for the embedded platforms. This would include suport for
    at least one of the backends for each core providers mentioned above to achieve
    feature parity with other patforms.

  - Mentors: Gabriel Pettier, Mathieu Virbel
  - Requirements: Access to specific embedded hardware.
  - Task level: Intermediate/Advanced
  - Desired Skills: Familiarity with programming on the specific embedded hardware.

* Inspector: 

  Description:
    Redo or improve the inspector module to include the following features:
      - Use Python introspection to enhance current state of inpector. 
      - Extend Inspectors debugging cpabilities to the whole app.
      - Introduce automatic creash reporting.
      - Possibly launch debugger automaticlaly when kivy app crashes.
  Reference: 
      http://kivy.org/docs/api-kivy.modules.html
      http://kivy.org/docs/api-kivy.modules.inspector.html

  Expected Outcome:
    A fully functional Inspector module that facilitates debugging at any stage,
    including crash reports and a debugging console.
  
  - Mentors: Akshay Arora, Gabriel Pettier
  - Task level: Intermediate

* Graphics Pipeline Enhancements:

  Description:
    We have a lot of ideas around the graphics pipeline:
      - Merging instructions
      - VBOs to reduce GL calls
      - helpers to create shaders dynamically according to the current vertex format
      - improving 3D support.
      - add Bounding-Box calculation / selection on the tree only if requested
      - Unit tests to quantify the amount of improvements achieved.
  Reference: 
      http://kivy.org/docs/api-kivy.graphics.html
      http://www.khronos.org/opengles/
  Expected Outcome:
    Significant improvement in the graphics pipeline that can be quantfied by tests.

  - Mentors: Jacob Kovac, Mathieu Virbel
  - Task level: Intermediate/Advanced
  - Desired Skills: Familiarity with OpenGL ES, desire to learn/solve difficult
    concepts/puzzles.


Mobile
~~~~~~

* Plyer:

  Description:
    The idea is to provide a stable API to the user for accessing features
    of their desktop or mobile device.
    
    Facades and implementation for::
      - such as Accelerometer, GPS, SMS, Contact,
        and more. 
      - Porting facades from Scripting Language for Android to Plyer
        for easy integration and compatability.
    
    Under the hood you'll use PyJNIus, PyOBJus. This probably
    would also include improving PyObjus and PyJnius to handle interfaces that
    they can't right now.
  References:
    https://github.com/kivy/plyer
    https://github.com/kivy/pyjnius
    https://github.com/kivy/pyobjus
  Expected Outcome:
    platform independent api for accessing most platform specific parts.
    
  - Mentors: Gabriel Pettier, Akshay Arora, Alexander Taylor, Ben Rousch.
  - Requirements: Access to Linux, Windows, OS X, iOS device, Android device.
  - Task level: Intermediate/Advanced.
  - Desired Skills: Familiarity with Pyjnius, PyObjus.


Toolchain
~~~~~~~~~

* Toolchain for iOS:

  Description:
    An iOS interface based on the idea of Python for Android,
    in order to replace kivy-ios. Cross-platform compilation skills are heavily
    required.
  References:
    https://github.com/kivy/kivy-ios
  Expected Outcome:
    A new new/improved modular and extendable toolchain.
  
  - Mentors: Thomas Hansen, Mathieu Virbel
  - Reuirements: Access to iOS, Android device along with a developer licence.
  - Task level: Intermediate/Advanced
  - Desired Skills: Familiarity with xcode, objc.

* Buildozer:

  Description:
    Needs support for generating RPM, DEB, DMG, and EXE files. This might not be
    enough in itself for a GSoC project. It would have to be joined together with 
    some other work.
  References:
    https://github.com/kivy/Buildozer
  Expected Outcome:
    New targets for buildozer to be able to get deb, rpm, dmg, exe binaries.

  - Mentors: Gabriel Pettier, Akshay Arora, Alexander Taylor, Ben Rousch
  - Requirements: Access to linux, Windows, OS X, iOS, Android.
  - Task level: Intermediate

* SDL2 Backends:
  
  Description:
    SDL2 backend providers for Kivy, including porting the mobile
    toolchains to SDL2. Part of the work is already done. What left is mostly

    - Hashing out distribution mechanisms for the lib.
    - Porting mobile backends to ios and android sdl2. Partial work on this has 
      already been going on.
    - Unit tests for the new sdl2 bckends making sure apps work the same
      on sdl2 as on other backends.
    - Performace testing. Looking at the difference between sdl2 and other providers
      to ascertain wether sdl2 could be used as the default provider giving it priority
      over other backends.
  References:
    https://github.com/kivy/kivy sdl2 branch
  Expected Outcome:
    New sdl2 core providers and support for using sdl2 on mobiles.

  - Mentors: Akshay Arora, Jacob Kovac, Mathieu Virbel
  - Requirements: Access to Linux, Windows, OS X, iOS, Android.
  - Task level: Intermediate/Advanced

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
