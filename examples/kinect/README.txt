Kinect Viewer
=============

You must have libfreenect installed on your system to make it work.

How it's working
----------------

1. viewer is taking depth value from freenect
2. depth are multiply per 32 to use the full range of 16 bits
3. depth are uploaded in a "luminance" texture
4. we are using a shader for mapping the depth to a special color

