from kivy._event cimport EventObservers

cdef EventObservers pixel_scale_observers

cpdef float dpi2px(value, str ext) except *
