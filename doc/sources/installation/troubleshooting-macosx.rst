.. _troubleshooting-macosx:

Troubleshooting on Mac OS X
===========================

Having trouble installing Kivy on Mac OS X? This page contains issues 

"Unable to find any valuable Window provider" Error
---------------------------------------------------

If you get an error like this::

    $ python main.py 
    [INFO   ] Kivy v1.8.0-dev
    [INFO   ] [Logger      ] Record log in /Users/audreyr/.kivy/logs/kivy_13-07-07_2.txt
    [INFO   ] [Factory     ] 143 symbols loaded
    [DEBUG  ] [Cache       ] register <kv.lang> with limit=None, timeout=Nones
    [DEBUG  ] [Cache       ] register <kv.image> with limit=None, timeout=60s
    [DEBUG  ] [Cache       ] register <kv.atlas> with limit=None, timeout=Nones
    [INFO   ] [Image       ] Providers: img_imageio, img_tex, img_dds, img_pil, img_gif (img_pygame ignored)
    [DEBUG  ] [Cache       ] register <kv.texture> with limit=1000, timeout=60s
    [DEBUG  ] [Cache       ] register <kv.shader> with limit=1000, timeout=3600s
    [DEBUG  ] [App         ] Loading kv <./pong.kv>
    [DEBUG  ] [Window      ] Ignored <egl_rpi> (import error)
    [DEBUG  ] [Window      ] Ignored <pygame> (import error)
    [WARNING] [WinPygame   ] SDL wrapper failed to import!
    [DEBUG  ] [Window      ] Ignored <sdl> (import error)
    [DEBUG  ] [Window      ] Ignored <x11> (import error)
    [CRITICAL] [Window      ] Unable to find any valuable Window provider at all!
    [CRITICAL] [App         ] Unable to get a Window, abort.

Then most likely Kivy cannot import PyGame for some reason. Continue on to the next section.

Check for Problems with Your PyGame Installation
------------------------------------------------

First, check that you have a working version of PyGame.

Start up the interactive Python interpreter and try to import pygame::

    $ python
    Python 2.7.3 (v2.7.3:70274d53c1dd, Apr  9 2012, 20:52:43) 
    [GCC 4.2.1 (Apple Inc. build 5666) (dot 3)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    Python 2.7.3 (v2.7.3:70274d53c1dd, Apr  9 2012, 20:52:43) 
    Type "copyright", "credits" or "license" for more information.
    >>> import pygame

If you can import pygame without problems, then skip to the next section.

But if you get an error, then PyGame is not working as it should. 

Here's an example of a PyGame error::

    ImportError                               Traceback (most recent call last)
    <ipython-input-1-4a415d16fbed> in <module>()
    ----> 1 import pygame

    /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/pygame/__init__.py in <module>()
         93 
         94 #first, the "required" modules
    ---> 95 from pygame.base import *
         96 from pygame.constants import *
         97 from pygame.version import *

    ImportError: dlopen(/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/pygame/base.so, 2): Symbol not found: _SDL_EnableUNICODE
      Referenced from: /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/pygame/base.so
      Expected in: flat namespace
     in /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/pygame/base.so

And here is another example of a PyGame error::

    ImportError                               Traceback (most recent call last)
    <ipython-input-1-4a415d16fbed> in <module>()
    ----> 1 import pygame

    /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/pygame/__init__.py in <module>()
         93 
         94 #first, the "required" modules
    ---> 95 from pygame.base import *
         96 from pygame.constants import *
         97 from pygame.version import *

    ImportError: dlopen(/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/pygame/base.so, 2): no suitable image found.  Did find:
        /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/pygame/base.so: no matching architecture in universal wrapper

The easiest way to resolve these PyGame import errors is:

1. Delete the ``pygame`` package. (For example, if you get the error above, 
    delete /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/pygame/ 
    and the accompanying egg.
2. Try installing a PyGame binary for your version of Mac OS X. Download it 
    from http://www.pygame.org/download.shtml.
3. Repeat this process and try different PyGame Mac OS X binaries until you find one that works.
