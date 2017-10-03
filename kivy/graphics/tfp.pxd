include "common.pxi"
from kivy.graphics.cgl cimport *

cdef GLXPixmap bindTexImage(Pixmap pixmap)
cdef void releaseTexImage(GLXDrawable drawable)