The files in the win32 and osx subdirectories are
source and resource files that are used to build the respective
portable packaged versions of kivy for each OS. Here they
are under version control.

setup.py copies these files into the portable distribution 
package that is created when you launch 
'setup.py build_portable'


For example, the win32 directory has the README and bat file which 
sets up the ENV variables and launches the python interpreter.
