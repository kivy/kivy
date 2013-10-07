!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
READ THIS FIRST
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

This version of Kivy is a portable win32 version, 32 bits. (it work also for
64 bits Windows.) This means everything you need to run kivy (including 
python and all other dependencies etc) are included.

This README only addresses the things specific to the portable version of kivy.  
For general information on how to get started, where to find the documentation 
and configuration see the README file in the kivy directory about Kivy.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


Running portable Kivy
=====================

The same directory that has this README file in it, contains a file called kivy.bat
running this kivy.bat file will set up the environment for kivy and starts the 
python interpreter with any arguments you passed

Example
~~~~~~~

If you open a command line and go to the directory (or add it to your PATH) 
You can run the following:

kivy test.py -w  <-- will run test.py as a python script with kivy ready to use


Run a Kivy application without going to the command line
========================================================

Three options :

1. You can drag your python script on top the kivy.bat file and it will launch

2. If you right click on your python script (.py ending or whatever you named it), 
you can select properties and select an application to open this type of file with.
Navigate to the folder that includes this README and select the kivy.bat file.  
Now all you have to do is double click (check do this always for this file type 
to make this the default)

3. Install the Python Launcher for Windows. (Comes with Python 3.3 -- See Python PEP-397)
* in each of your main.py files, add a first line of:
   #!/usr/bin/kivy
* create a file named C:\Windows\py.ini containing something like:
   [commands]
   kivy="c:\<path>\<to>\<your>\kivy.bat"

If you already have Python installed
====================================

The portable Kivy version shouldn't cause any conflicts and cooperate fairly well 
(at least if it's Python 2.6, otherwise some modules might cause problems if there
is entries on PYTHONPATH)


Install Kivy as a standard python module
========================================

Please refer to the install instructions in the complete README :
* Inside the kivy folder inside this one
* Kivy documentation at http://kivy.org/docs/


Install development environment inside your current shell
=========================================================

If you want to develop with Kivy's python, you may just want to load the
environment, and stay in your console. Inside a git bash / mingsys console, you
can type :

  source /path/to/kivyenv.sh

And it will load the whole enviroment of Kivy. This will give you an access to:

  * Python binaries (python, pythonw, easy_install)
  * Cython binaries (cython)
  * Gstreamer binaries (gst-inspect, gst-launch, ...)
  * Pre-configured PYTHONPATH for gst and Kivy

Please note that if you already have a Python installed on your system, it will be
not used.
