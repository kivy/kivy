'''
Css styling basic tests
'''

from init import test, import_kivy_no_window

def unittest_css():
    import_kivy_no_window()
    from kivy import MTWidget, Label
    from kivy import css_add_sheet
    css_add_sheet('''
    .style {
        bg-color: rgba(255, 255, 255, 255);
        }
    #my { bg-color : rgba(255, 0, 255, 0);}
    ''')
    w = MTWidget(cls='style')
    x = MTWidget(id='my',cls='style')
    test(w.style['bg-color'] == [1.0 ,1.0 ,1.0 ,1.0])
    test(x.style['bg-color'] == [1.0 ,0.0 ,1.0 ,0.0])
    x.style['bg-color'] = [0, 0, 0, 0]
    test(x.style['bg-color'] == [0 ,0 ,0 ,0])

def unittest_css_label():
    import_kivy_no_window()
    from kivy import MTLabel, css_add_sheet
    css_add_sheet('''
    .style {
        color: rgba(0, 255, 0, 255);
    }
    ''')
    l = MTLabel(label='test', cls='style')
    test(l.style['color'] == [0.0, 1.0, 0.0, 1.0])

def unittest_css_multiclass():
    import_kivy_no_window()
    from kivy import MTLabel, css_add_sheet
    css_add_sheet('''
    .test1 {
        font-color : rgba(255,255,255,255);
    }
    .test2 {
        font-size: 24;
    }
    ''')
    l = MTLabel(label = 'test', cls=('test1', 'test2'))
    test(l.style['font-size'] == 24)
