Google Summer of Code - 2017
============================

Introduction
------------
Kivy is a cross-platform, business friendly, GPU accelerated open source
Python library for rapid development of applications that make use of
innovative user interfaces, such as multi-touch apps.

The Kivy Organization oversees several major projects:

* The `Kivy <https://github.com/kivy/kivy>`_ GUI Library
* The `Python-For-Android <https://github.com/kivy/python-for-android>`_
  compilation tool.
* The `Kivy-iOS <https://github.com/kivy/kivy-ios>`_ compilation tool.
* The `PyJNIus <https://github.com/kivy/pyjnius>`_ library for interfacing with
  Java from Python.
* The `PyOBJus <https://github.com/kivy/pyobjus>`_ library for interfacing with
  Objective-C from Python.
* The `Plyer <https://github.com/kivy/plyer>`_ platform-independent Python
  wrapper for platform dependent APIs.
* `Buildozer <https://github.com/kivy/buildozer>`_ - A generic Python packager
  for Android, iOS, and desktop.
* `KivEnt <https://github.com/kivy/kivent>`_ - A 2d Game Engine that provides
  optimized methods of handling large amounts of dynamic visual data.
* `Kivy Designer <https://github.com/kivy/kivy-designer>`_ - A graphical GUI
  designer for Kivy built in Kivy.

Altogether, these projects allow the user to create applications for every
major operating system that make use of any native APIs present. Our goal is to
enable development of Python applications that run everywhere off the same
codebase and make use of platform dependent APIs and features that users of
specific operating systems have come to expect.

Depending on which project you choose you may need to know Cython, OpenGL ES2,
Java, Objective-C, or C in addition to Python. We make heavy use of Cython and
OpenGL for computational and graphics performance where it matters, and the
other languages are typically involved in accessing OS or provider level APIs.

We are hoping to participate in Google Summer of Code 2017. This page showcases
some ideas for GSoC projects and corresponding guidelines for students
contributing to the Kivy Framework.

Requirements
------------

It is assumed that the incoming student meets some basic requirements as
highlighted here:

* Intermediate level familiarity with Python.
* Comfortable with git and github (Kivy and its sister projects are all managed
  on github) If you have never used github before you may be interested in this
  `tutorial <https://guides.github.com/activities/hello-world/>`_.
* Comfortable with event driven programming.
* Has suitable tools/environment for Kivy or the sister project you are going
  to work on. For example to be able to work on PyOBJus you would need access
  to an iOS device, OS X with Xcode and a developer license, to work on PyJNIus
  you would need an Android device, and to work on plyer you would need access
  to hardware for both platforms.


Additional desired skills may be listed with specific projects.

Familiarize yourself with the
`contribution guide <http://kivy.org/docs/contribute.html>`_
We can help you get up to speed, however students demonstrating ability in
advance will be given preference.

How to get started
------------------

For Kivy, the easiest way is to follow the installation instructions for the
development version for your specific platform:

http://kivy.org/docs/installation/installation.html#development-version

For the rest it's usually sufficient to install the relevant project from git
and add it to your PYTHONPATH.

e.g. for PyJNIus::

    git clone http://github.com/kivy/pyjnius
    export PYTHONPATH=/path/to/pyjnius:$PYTHONPATH


Project Ideas
--------------
Here are some prospective ideas sourced from the Kivy development team, if
none of these projects interest you come talk to us in #kivy-dev about a
project idea of your own.

Beginner Projects
~~~~~~~~~~~~~~~~~
These projects should be suitable for anyone with a college level familiarity
with Python and require little knowledge of platform specifics.

Intermediate Projects
~~~~~~~~~~~~~~~~~~~~~
These projects may involve cursory level knowledge of several OS level details,
some OpenGL interaction, or other topics that may be a bit out of the
wheelhouse of the average Pythonista.

**Plyer:**

  Description:
    Plyer is a platform-independent Python API to use features
    commonly found on the desktop and mobile platforms supported by
    Kivy. The idea is to provide a stable API to the user for
    accessing features of their desktop or mobile device.

    The student would replace some `.java` code currently in the p4a
    project to a more appropriate place in Plyer. In addition, the
    student would work on improving access to platform specific
    features through Plyer, including accessibility, Bluetooth Low Energy,
    accessing and editing contacts, sharing, NFC, in-app browser,
    Wi-Fi (enable, disable, access to Wi-Fi services (Wi-Fi direct,
    network accessibility, current IP info on network etc.),
    Camera capture (video), camera display, Google Play integration,
    launch phone call interface, sms interface, geolocation,
    interaction with notifications, internationalization (I18N),
    and all the missing platform implementations from existing features.

    Under the hood you'll use PyJNIus on Android, PyOBJus on OS X and
    iOS, ctypes on Windows, and native APIs on Linux. This probably
    would also include improving PyOBJus and PyJNIus to handle
    interfaces that they can't right now.

  References:
    - https://github.com/kivy/plyer
    - https://github.com/kivy/pyjnius
    - https://github.com/kivy/pyobjus
    - https://github.com/kivy/python-for-android
    - https://github.com/kivy/kivy-ios
  Expected outcome:
    A successful outcome would include moving the Java/PyOBJus code
    from p4a/kivy-ios to plyer and implementing some or all
    of the new facades to be decided with the student.

  - **Mentors**: Akshay Arora
  - **Requirements**: Access to Linux, Windows, OS X, iOS device,
    Android device.
  - **Task level**: Intermediate
  - **Desired Skills**: Familiarity with PyJNIus, PyOBJus.


**Font Reshaping and Font Fallback Support**

  Description:
    Currently Kivy does not support reshaping for alphabets such as Arabic,
    Persian, Thai, or Devanagari. The solution is to integrate a text shaping
    and layout engine (Pango and Harfbuzz). You would need to ensure that
    Pango and Harfbuzz can be compiled on every platform, and integrate it
    as a core text provider.

    The second part of the same project would involve font fallback support.
    If a particular character/glyph is missing, currently we show a [] box.
    The solution for this would involve either using an OS API if available
    or maintaining a hashtable for the default fonts on each OS which can be
    used for glyph fallback.

  References:
    - http://www.pango.org
    - https://www.freedesktop.org/wiki/Software/HarfBuzz/
    - https://github.com/kivy/kivy/tree/master/kivy/core/text

  Expected outcome:
    Font fallback and text reshaping support in Kivy, compilation recipes for Python-For-Android and packaging on desktop platforms.

  - **Mentors**: Akshay Arora, Jacob Kovac, Matthew Einhorn
  - **Requirements:** Access to a desktop OS and ideally at least one mobile
    platform
  - **Task level**: Intermediate
  - **Desired Skills**: Familiarity with text rendering, Pango, HarfBuzz
    and Kivy's provider abstraction.


Advanced Projects
~~~~~~~~~~~~~~~~~
These projects may involve very in-depth knowledge of Kivy's existing
internals, the hairy details of cross-platform compilation, or other fairly
advanced topics. If you are comfortable with the internals of Python, working
with C code, and using Cython to build your own C extensions these projects
may appeal to you.


**Kivent: Chipmunk 7 Integration**

  Description:
    KivEnt is a modular entity-component based game engine built on top of
    Kivy. KivEnt provides a highly performant approach to building games in
    Python that avoids some of the worst overhead of Python using specialized
    Cython constructs.

    At the moment, KivEnt internally makes use of the cymunk library
    (https://github.com/tito/cymunk) for physics simulation and collision
    detection. Cymunk is based on Chipmunk2d 6.x, recently Chipmunk 7 has
    released and brought many previously premium features into the core library.
    In addition to the API changes present in the newest Chipmunk, the
    KivEnt - Cymunk bridging does not make most efficient use of the KivEnt
    API for handling C level objects and data. The student will be responsible
    for creating a new wrapper over Chipmunk2d 7 that better matches KivEnt's
    approach to handling game data.

  References:
    - http://chipmunk-physics.net/
    - https://github.com/kivy/kivent
  Expected Outcome:
    A successful outcome involves a new kivent_tiled module being released for
    the KivEnt game engine.

  - **Mentors**: Jacob Kovac
  - **Requirements**: Access to at least one Kivy platform.
  - **Task level**: Advanced
  - **Desired Skills**: Familiarity with Cython, Python, and game dev related
    math concepts.


**KV Compiler: A compiler for the KV language**

  Description:
    The KV language is a fundamental component of Kivy. The KV language allows one
    to describe a GUI; from the creation of a Widget tree to the actions that should be
    taken in response value changes and events. In effect it is a concise way to create
    rule bindings using the Kivy properties and events. Internally, python code that
    reflects these rules are created and bound to the properties and events. Currently,
    these bindings are not at all optimized because upon each widget creation all of
    these rules are re-evaluated and bound. This process can be significantly optimized
    by pre-compiling the kv code, especially the bindings. A compiler would also allow
    us to update and fix some of the long-standing kv language issues.

    Work on a kv-compiler has already progressed quite far, in fact a PR in the pre-alpha
    stage, is currently open. However, it is out of sync with the current codebase due to
    some unrelated kv changes in the meantime. Also, that PR would require a significant
    re-write to make things more modular, self-contained, and extensible. So there is much
    work still to be done on it.

    Theming has also been a prepatual issue in Kivy, a KV compiler may help implement bindings
    that facilitate theming.

  References:
    - https://kivy.org/docs/guide/lang.html
    - https://github.com/kivy/kivy/pull/3456
    - https://github.com/kivy/kivy/wiki/KEP001:-Instantiate-things-other-than-widgets-from-kv
    - https://github.com/kivy/kivy/issues/691
    - https://github.com/kivy/kivy/issues/2727
  Expected Outcome:
    A successful outcome would be a compiler which compiles kv code into python
    code. The compiler should be modular and extensible so that we can continue to
    improve the kv language. The compiler should have the common debug/optimization
    options. The compiled code should also be human readable so issues could be traced
    back to the original kv code. The compiler should also be a drop in replacement for the
    current KV runtime compiler, and would require extensive testing.

  - **Mentors**: Matthew Einhorn
  - **Requirements**: Access to at least one Kivy platform.
  - **Task level**: Advanced
  - **Desired Skills**: Familiarity with Cython, Python, and Kivy. Familiarity
    with typical computer science concepts and data structures is also desired.



How to Contact devs
-------------------
All communication must happen via public channels, private emails
and Discord private messages are discouraged.

Ask your questions on the Kivy Users forum https://groups.google.com/group/kivy-users
or send a mail at kivy-users@googlegroups.com

Make sure to join the kivy-dev user group too:
https://groups.google.com/forum/#!forum/kivy-dev.

You can also try to contact us on Discord, to get the Discord handles of
the devs mentioned above visit https://kivy.org/#aboutus.

Make sure to read the `Discord rules <https://kivy.org/docs/contact.html>`_ before
connecting. `Connect to Discord <https://chat.kivy.org>`_.


Most of our developers are located in Europe, India, and North America so keep
in mind typical waking hours for these areas.


How to be a good student
------------------------

If you want to participate as a student and want to maximize your chances of
being accepted, start talking to us today and try fixing some smaller problems
to get used to our workflow. If we know you can work well with us, you will
have much better chances of being selected.

Here's a checklist:

* Make sure to read through the website and at least skim the documentation.
* Look at the source code.
* Read our contribution guidelines.
* Make a contribution! Kivy would like to see how you engage with the
  development process. Take a look at the issue tracker for a Kivy project
  that interests you and submit a Pull Request. It can be a simple bug or a
  documentation change. We are looking to get a feel for how you work, not
  evaluating your capabilities. Don't worry about trying to pick something
  to impress us.
* Pick an idea that you think is interesting from the ideas list or come up
  with your own idea.
* Do some research **yourself**. GSoC is about give and take, not just one
  sided interaction. It is about you trying to achieve agreed upon goals with
  our support. The main driving force in this should be, obviously, yourself.
  Many students pop up and ask what they should do. You should base that
  decision on your interests and your skills. Show us you're serious about it
  and take the initiative.
* Write a draft
  `proposal <https://wiki.python.org/moin/SummerOfCode/ApplicationTemplate2016>`_
  about what you want to do. Include what you understand the current state of
  the project to be, what you would like to improve, how, etc.
* Discuss that proposal with us in a timely manner. Get feedback.
* Be patient! Especially on Discord. We will try to get to you if we're available.
  If not, send an email and just wait. Most questions are already answered in
  the docs or somewhere else and can be found with some research. Your
  questions should reflect that you've actually thought through what you're
  asking and done some rudimentary research.
* Most of all don't forget to have fun and interact with the community. The
  community is as big a part of Open Source as the code itself.

What to expect if you are chosen
--------------------------------

* All students should join the #support and the #dev Discord channels daily,
  this is how the development team communicates both internally and with the
  users.
* You and your mentors will agree on two week milestones for the duration of
  the summer.
* Development will occur in your fork of the master branch of Kivy, we expect
  you to submit at least one PR a week from your branch into a branch reserved
  for you in the primary repo. This will be your forum for reporting progress
  as well as documenting any struggles you may have encountered.
* Missing 2 weekly PR or 2 milestones will result in your failure unless there
  have been extenuating circumstances. If something comes up, please inform
  your mentors as soon as possible. If a milestone seems out of reach we will
  work with you to reevaluate the goals.
* Your changes will be merged into master once the project has been completed
  and we have thoroughly tested on every platform that is relevant.
