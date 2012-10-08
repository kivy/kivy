Compass
=======

Demonstrate the combination of the Android Magnetic Field Sensor and the Kivy functionality viewing a Compass.

Kivy Python-For-Android
-----------------------

Please look at the lastest docs of the
`Kivy Python-For-Android Project <http://python-for-android.readthedocs.org/en/latest/>`__

Building an APK
---------------

:: 

   ./distribute.sh -m "pyjnius kivy"


::

   ./build.py --package org.test.compass --name compass \
   --version 1.0 --dir ~/code/kivy/examples/android/compass debug

