from kivy.core.window import Window
from kivy.graphics.svg import Svg
from time import time
import sys
import os

filename = sys.argv[1]
if "PROFILE" in os.environ:
    import pstats
    import cProfile
    cProfile.runctx("Svg(filename)", globals(), locals(), "Profile.prof")
    s = pstats.Stats("Profile.prof")
    s.sort_stats("time").print_callers()
else:
    print("Loading {}".format(filename))
    start = time()
    svg = Svg(filename)
    end = time()
    print("Loaded in {:.2f}s".format((end - start)))
