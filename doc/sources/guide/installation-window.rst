Installation on Windows
=======================

The windows stable version is what we call a portable package. You don't have
to install anything in "system" wide. Just unzip & run:

    1. Download the latest version from http://kivy.org/#downloads
    2. Unzip the package
    3. Then, in the unzipped package, you have a script called `kivy.bat`,
       use it for launching any kivy application


Start any Kivy's application
----------------------------

If you want to double-click and make it just "work", you need to use the
`kivy.bat` included in the package for starting Kivy application. To make
it work, do

    1. Right click on the python file of the application
    2. Open With
    3. Select the default software
    4. Browse your files to select the `kivy.bat`
    5. Select "Always open the file with..." if you want
    6. Ok !

Next time, your python file will be executed with the Kivy's python !


Start from commandline
----------------------

If you want just to use or develop with latest stable kivy, we offer you an
alternative way with a console. You need a minimalist GNU system installed on
your system. Use `msysGit <http://code.google.com/p/msysgit/>`_.

When you install the msysGit, you must select theses options:

    * Don't replace windows shell
    * Checkout at-is, commit at-is (no clrf replacement !)

You'll have an icon "Git bash" on your desktop, this is the console we want:

    1. Start "Git bash"
    2. cd "directory of portable kivy"
    3. source kivyenv.sh "full directory of portable kivy" (don't use .)

You are now ready to launch python/kivy in commande line ! Just do::

    python <filename.py>

Also, all other scripts and binary are available such as:

    * cython
    * gcc / make...
    * easy_install
    * gst-inspect-0.10


Content of the package
----------------------

The latest windows package contain:

    * Latest kivy stable version
    * Python 2.7.1
    * Glew 1.5.7
    * Pygame 1.9.2
    * Cython 0.14
    * MingW
    * Gstreamer
    * Setuptools


