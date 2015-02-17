Google Summer of Code - 2015
============================
This document is still a work in progress.

Introduction
------------
Kivy is a cross-platform, business friendly, GPU Accelerated open source Python library for rapid development of applications that make use of innovative user interfaces, such as multi-touch apps.

The Kivy Organization oversees several major projects:

* The `Kivy <https://github.com/kivy/kivy>`_ GUI Library
* The `Python-For-Android <https://github.com/kivy/python-for-android>`_ compilation tool.
* The `Kivy-iOS <https://github.com/kivy/kivy-ios>`_ compilation tool.
* The `PyJNIus <https://github.com/kivy/pyjnius>`_ library for interfacing with Java from Python.
* The `PyOBJus <https://github.com/kivy/pyobjus>`_ library for interfacing with Objective-C from Python.
* The `Plyer <https://github.com/kivy/plyer>`_ platform-independent Python wrapper for platform dependent APIs.
* `Buildozer <https://github.com/kivy/buildozer>`_ - A generic Python packager for Android, iOS, and desktop.

Altogether, these projects allow the user to create applications for every major operating system that make use of any native APIs present. Our goal is to enable development of Python applications that run everywhere off the same codebase and make use of platform dependent APIs and features that users of specific operating systems have come to expect. Depending on which project you choose you may need to know Cython, OpenGL ES2, Java, Objective-C, or C in addition to python. We make heavy use of Cython and OpenGL for computational and graphics performance where it matters, and the other languages are typically involved in accesses OS or provider level APIs.

We are hoping to participate in Google Summer of Code 2015. This page showcases some ideas for gsoc projects and corresponding guidelines for students contributing to the Kivy Framework.

Requirements
------------

It is assumed that the incoming student meets some basic requirements as highlighted here:

* Intermediate level familiarity with python
* Comfortable with git and github (Kivy and its sister projects are all managed on github) If you have never used github before you may be interested in this tutorial: https://guides.github.com/activities/hello-world/
* Comfortable with event driven programming.
* Has suitable tools/environment for kivy or the sister project you are going to work on. For example to be able to work on pyobjus you would need access to an iOS device, mac with xcode and a developer license, to work on pyjnius you would need an android device, and to work on plyer you would need access to hardware for both platforms.

  
Additional desired skills may be listed with specific projects.

Familiarize yourself with the contributing guide http://kivy.org/docs/contribute.html We can help you get up to speed, however students demonstrating ability in advance will be given preference.

How to get setup
----------------

For Kivy, the easiest way is to follow the installation instructions for the development version for your specific platform:

http://kivy.org/docs/installation/installation.html#development-version

For the rest it's usually sufficient to install the relevant project from git and add it to your PYTHONPATH.

eg.. for pyjnius::

    git clone http://github.com/kivy/pyjnius
    export PYTHONPATH=/path/to/pyjnius:$PYTHONPATH


Project Ideas
--------------

The mentors list is only of potential mentors for a particular project and not final.

Enhancements to Kivy
~~~~~~~~~~~~~~~~~~~~

**UI Testing**

  Description:

  References:

  Expected Outcome:

  - **Mentors**:
  - **Task level**:

**Harfbuzz Font Rendering Support**

  Description:
    Currently Kivy does not support reshaping for alphabets such as Arabic, 
    Persian, Thai, or Devanagari. The solution is to integrate a text shaping
    engine- Harfbuzz. You would need to ensure that we can compile Harfbuzz
    on every platform and properly integrate it as a core text provider.

  References:
    - http://www.freedesktop.org/wiki/Software/HarfBuzz/
    - https://github.com/kivy/kivy/tree/master/kivy/core/text

  Expected Outcome:
    Harfbuzz core text provider for Kivy and correct compilation recipes for platforms that need it, such as Python-For-Android.

  - **Mentors**: Jacob Kovac
  - **Requirements:** Access to Linux, Windows, OSX, Android, iOS
  - **Task level**: Intermediate/Advanced
  - **Desired Skills**: Familiarity with text rendering, HarfBuzz, and Kivy's
  provider abstraction.


Enhancements to Mobile Platforms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Plyer:**

  Description:
    Plyer is a platform-independant api to use features commonly found on various platforms, especially mobile ones, in Python. The idea is to provide a stable API to the user for accessing featuresof their desktop or mobile device. The student would work on improving access to platform specific Accessibility features through Plyer. In addition Plyer currently rely on some .java code that should be replaced directly with use of Pyjnius.
    
    Under the hood you'll use PyJNIus and PyOBJus. This probably would also include improving PyObjus and PyJnius to handle interfaces that they can't right now.
    
  References:
    - https://github.com/kivy/plyer
    - https://github.com/kivy/pyjnius
    - https://github.com/kivy/pyobjus
  Expected Outcome:
    Platform independent api for accessing most platform specific features.
    
  - **Mentors**: 
  - **Requirements**: Access to Linux, Windows, OS X, iOS device, Android device.
  - **Task level**: Intermediate/Advanced.
  - **Desired Skills**: Familiarity with Pyjnius, PyObjus.


Enhancements to Toolchain
~~~~~~~~~~~~~~~~~~~~~~~~~

**SDL2 On Android:**
  
  Description:
    Currently Python-For-Android is not very flexible and have a very specific bootstrap crafted for use with Kivy's old SDL1.2/1.3 backend used through Pygame. In order to switch to SDL2 on Android, we need to switch from starting a Java application that then call the Python Interpreter to a Native C application that bootstrap SDL2 and then Python. In addition, PyJNIus currently expect this old method and it needs to be modified to be more flexible and have modifiable activity instead of always looking for org.renpy.android.PythonActivity or PythonService. 

  References:
    - https://github.com/kivy/python-for-android
    - https://docs.google.com/document/d/1kNBFtHG55ejAr-Ow5VhHCua-vvpAjtneTRdr7GdskMA/edit?usp=sharing

  Expected Outcome:
    Python-for-Android capable of compiling apk using SDL2 as backend instead
    of pygame.

  - **Mentors**: Jacob Kovac
  - **Requirements:** Access to Linux, Android.
  - **Task level**: Intermediate/Advanced
  - **Desired Skills**: Understanding of Cross-Compilation for Android, familiarity with PyJNIus

**Kivy Designer**

  Description:
    Kivy Designer is a GUI tool for creating Kivy GUI layouts written in Kivy. You can compose, customize, and test widgets using the tool. This project has been the subject of 2 previous GSOC and is experimental, alpha level software at the moment. However, it is a very popular request for more updates among our uses; if you are interested in GUI tool development this could be a great fit for you!

  References:
    - https://github.com/kivy/kivy-designer

  Expected Outcome:

  - **Mentors**:
  - **Requirements:** Access to Linux, Windows, OSX
  - **Task level**: Easy
  - **Desired Skills**: Experience with other GUI creation tools. Familiar with Kivy approach to EventLoop and UIX Widgets.


Applications
~~~~~~~~~~~~

**MatPlotLib Integration**

  Description:
    In order to enhance Kivy's usefulness for scientific disciplines tight MatPlotLib integration is highly desirable. This project would be a very exploratory project, involving both ensuring MatPlotLib is deployable on every platform Kivy supports and developing widgets that interface with the API.

  References:
    - http://matplotlib.org/
    - https://github.com/kivy/kivy

  Expected Outcome:
    The MatPlotLib widgets will be included in the Kivy garden and ready to use on all of Kivy's supported OS.

  - **Mentors**:
  - **Requirements:** Access to Linux, Windows, OSX, Android, iOS
  - **Task level**: Easy
  - **Desired Skills**: Familiarity with Kivy widget construction and MatPlotLib. 

How to Contact devs
-------------------
Ask your questions on the Kivy users forums http://kivy.org/#forum

Or send a mail at kivy-users@googlegroups.com

Make sure to Join kivy-dev user group too @ https://groups.google.com/forum/#!forum/kivy-dev

You can also try to contact us on IRC (online chat), to get the irc handles of the devs mentioned above visit http://kivy.org/#aboutus

Make sure to read the `IRC rules <http://kivy.org/docs/contact.html>`_ before connecting.
http://webchat.freenode.net/?nick=kvuser_GSOC_.&channels=kivy&uio=d4

Most of our developers are located in Europe, India, and North America so keep in mind typical waking hours for these areas.


How to be a good student
------------------------

If you want to participate as a student and want to maximize your chances of being accepted, start talking to us today and try fixing some smaller problems to get used to our workflow. If we know you can work well with us, that'd be a big plus.

Here's a checklist:

* Make sure to read through the website and at least skim the documentation.
* Look at the source code.
* Read our contribution guidelines.
* Pick an idea that you think is interesting from the ideas list or come up with your own idea.
* Do some research **yourself**. GSoC is not about us teaching you something and you getting paid for that. It is about you trying to achieve agreed upon goals by yourself with our support. The main driving force in this should be, obviously, yourself. Many students pop up and ask what they should do. Well, we don't know because we know neither your interests nor your skills. Show us you're serious about it and take the initiative.
* Write a draft `proposal <https://wiki.python.org/moin/SummerOfCode/ApplicationTemplate2014>`_ about what you want to do. Include what you understand the current state is (very roughly), what you would like to improve, how, etc. 
* Discuss that proposal with us in a timely manner. Get feedback.
* Be patient! Especially on IRC. We will try to get to you if we're available. If not, send an email and just wait. Most questions are already answered in the docs or somewhere else and can be found with some research. If your questions don't reflect that you've actually thought through what you're asking, it might not be well received.
  
What to expect if you are chosen
--------------------------------

* All students should join the #kivy and the #kivy-dev irc channels daily, this is how the development team communicates both internally and with the users. 
* You and your mentors will agree on two week milestones for the duration of the summer. 
* Development will occur in your fork of the master branch of Kivy, we expect you to submit at least one PR a week from your branch into a branch reserved for you in the primary repo. This will be your forum for reporting progress as well as documenting any struggles you may have encountered.
* Missing 2 weekly PR or 2 milestones will result in your failure unless there have been extenuating circumstances. If something comes up, please inform your mentors as soon as possible. If a milestone seems out of reach we will work with you to reevaluate the goals.
* Your changes will be merged into master once the project has been completed and we have thoroughly tested on every platform that is relevant!