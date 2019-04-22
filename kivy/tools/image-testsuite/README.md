Generating the image test suite
-------------------------------

On Linux/unix systems, you can use the `imagemagick-testsuite.sh` script
to create an image test suite using the `convert` command line utility. You
must have ImageMagick installed ("apt install imagemagick" on debian
derivatives). There is also a rule in the Makefile, `make image-testsuite`.

A more comprehensive test suite can be generated using Gimp (tested on
version 2.8.18). To install the plugin, copy `gimp28-testsuite.py` to your
gimp plugins directory, on linux/unix systems usually `~/.gimp-2.8/plug-ins`.
You can find the plugin location via the Gimp menu `Edit` - `Preferences` -
`Folders` - `Plug-Ins`. Once installed, the plugin should appear in "Tools"
menu, named "Kivy image testsuite".

Test images must be saved in the `kivy/tests/image-testsuite` directory,
after this you can run the test. It is (currently) preferable to run it
directly as a script, instead of via `make test`, since the latter won't
give you useful debug output.

    cd kivy/tests
    python test_imageloader.py | less

or to get only the summary report:

    python test_imageloader.py | grep REPORT | less


Kivy ImageLoader testsuite
--------------------------

These tools generate a wide range of images for testing Kivy's ImageLoaders.
The pixel data is encoded in the file name, and reproduced "from the sideline"
in order to verify the pixel data loaded from file. This is used to expose
issues in the Kivy core and underlying provider libraries.

The filenames consist of sections separated by an underscore `_`:

    v0_ <W> x <H> _ <pat> _ <alpha> _ <fmt> _ <testname> _ <encoder> . <ext>

Variables are enclosed in pointy brackets. The leading `v0_` indicates that
it conforms to version 0 of the test protocol (described in this document)
and must be present.

    v0_5x1_rgb_FF_PNG24_OPAQUE_magick.png

This is a 5x1 image, pattern is "rgb", alpha is "FF". `PNG24` is the internal
file format name (ImageMagick-specific), and `OPAQUE` is the test we  are
performing (drawing opaque pixels only), see test names below.

* <pattern> indicates the pixel colors (in order), as they are drawn in the
  image file.

* <alpha> is the global alpha from 00-FF (2 bytes, ascii) which is applied to
  all pixels except 't' (transparent) which have fixed alpha at 00

* <fmt> (aka fmtinfo) is an encoder-specific string with information about the
  format or process that generated the file. For example, if the same image
  is saved with and without interlacing, it will contain "I1" and "I0" to
  distinguish the files.
  * ImageMagick test suite generator uses magick format name, such as `PNG24`
  * The Gimp generator plugin adds information about the layer that was
    exported to form the image:
      * BPP1G = 1 byte per pixel, gray
      * BPP2GA = 2 bytes per pixel, gray + alpha
      * BPP3 = 3 bytes per pixel, rgb
      * BPP4 = 4 bytes per pixel, rgba
      * IX = indexed, IXA = indexed+alpha
      * Note: Indexed images are drawn in RGB or GRAY images (with alpha if
        needed), and converted to indexed before export. These values
        represent the layer type at time of export, it affects the parameters
        used for encoding the output data.

* <testname> is a special string that indicates what type of data is expected
  in the file. Options are OPAQUE, BINARY, ALPHA and repeated for grayscale,
  GRAY-OPAQUE, GRAY-BINARY, GRAY-ALPHA. We expect BINARY and ALPHA tests to
  result in an alpha channel (details below)

* <encoder> identifies the software that created the file, "magick", "gimp" ..

* <ext> is the extension, must be lowercase and match the extensions
  supported by Kivy image loaders (or they will be ignored)


Test names
----------

* `OPAQUE` tests opaque pixels (normal RGB) (lossess formats)
* `BINARY` tests opaque + fully transparent pixels (GIF etc)
* `ALPHA` tests semi-transparent pixels (normal RGBA) (PNG32 etc)
* `GRAY-OPAQUE` tests opaque grayscale only (various PNG, tga, )
* `GRAY-BINARY` tests opaque grayscale + fully transparent pixels (PNGs)
* `GRAY-ALPHA` tests semi-transparent grayscale pixels (TGA, XCF)

Patterns must conform to the specific test. For example, the pattern "rgb" has
undefined behavior for a grayscale test, since r/g/b can't be represented
in grayscale. So all grayscale formats must use 0-9A-F only, and optionally 
't' for transparent pixels in GRAY-BINARY/GRAY-ALPHA.


| Test name    | Valid pattern characters                                    |
| -----------: | :---------------------------------------------------------- |
| OPAQUE       | `wxrgbcyp`, and full grayscale\*\*                          |
| GRAY-OPAQUE  | `0123456789ABCDEF` (full grayscale)                         |
| BINARY       | `t` REQUIRED + `wrgbcyp`, limited grayscale (no 0/x!!!)     |
| GRAY-BINARY  | `t` REQUIRED + limited grayscale (no 0/x!!!)                |
| ALPHA        | `t`, `wxrbgcyp` and full grayscale\*\*                      |
| GRAY-ALPHA   | `t`, `0123456789ABCDEF` (full grayscale)                    |

* `**`: While grayscale is supported here, it is generally better to use
  colors, since all the bytes in a grayscale pixel represented as rgb are
  identical. For example, 'A' or \xAA\xAA\xAA will pass despite a byte
  order problem.

* `!!!`: In some cases, black color is used for binary transparency. So
  if you use "0" (or "x"), test_imageloader will expect #000000FF in RGBA,
  but the pixel becomes transparent (a=00) and test fails. All BINARY tests
  **MUST** include at least one "t" pixel to ensure that the image is
  saved with an alpha channel.


Pixel values
------------

Each character in the pattern represents the color of a single pixel. It is
important that you include only the correct type of pixel values for the
different test types (see table above). Individual pixel values get their
alpha from global setting (<alpha> in filename), but 't' pixels always have
alpha = 0x00 regardless of the test's alpha setting.


    OPAQUE, BINARY, ALPHA (lowercase)
    -----------------------------------------
    "w" White (#fff)     "x" Black  (#000)!!!
    "r" Red   (#f00)     "g" Green  (#0f0)
    "b" Blue  (#00f)     "y" Yellow (#ff0)
    "c" Cyan  (#0ff)     "p" Purple (#f0f)


    GRAY-OPAQUE, GRAY-BINARY, GRAY-ALPHA (uppercase)
    ------------------------------------------------
    "0" #000!!!  "1" #111     "2" #222     "3" #333
    "4" #444     "5" #555     "6" #666     "7" #777
    "8" #888     "9" #999     "A" #AAA     "B" #BBB
    "C" #CCC     "D" #DDD     "E" #EEE     "F" #FFF

    !!! See warnings above regarding BINARY tests

