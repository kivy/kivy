The files in teh win32 and osx subdirectories are 
source and resource files that are used in the respective 
portable packaged versions of kivy for each OS.  Here, they
are under version controll.  

setup.py copies these files into the portable distribution 
package that is created when you launch 
'setup.py build_portable'


For example the win32 dir has the READMEand bat file which 
sets up the ENV variables and launches the python interpreter.