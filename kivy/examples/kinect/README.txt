Kinect Viewer
=============

You must have libfreenect installed on your system to make it work.

How it works
------------

1. The viewer gets the depth value from freenect.
2. Depths are multiplied by 32 to use the full range of 16 bits.
3. Depths are uploaded into a "luminance" texture.
4. We use a shader for mapping the depth to a special color.

