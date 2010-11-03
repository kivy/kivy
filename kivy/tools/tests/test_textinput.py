'''
test usage of MTTextInput widget
'''

from init import test, import_kivy_window

def instance():
    import_kivy_window()
    from kivy import MTTextInput
    from kivy import css_add_sheet, css_reload
    try:
        t = MTTextInput()
        return True
    except:
        return False

def unittest_mttextinput():
    test(instance())

