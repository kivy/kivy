'''
Display Metrics
===============

This module give you access to multiple display values, and some conversion
functions.
'''

__all__ = ('pt', 'inch', 'cm', 'mm', 'dp')

from kivy.properties import dpi2px

def pt(value):
    return dpi2px(value, 'pt')

def inch(value):
    return dpi2px(value, 'in')

def cm(value):
    return dpi2px(value, 'cm')

def mm(value):
    return dpi2px(value, 'mm')

def dp(value):
    return dpi2px(value, 'dp')

