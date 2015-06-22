from matplotlib.figure import Figure
from numpy import arange, sin, pi
from kivy.app import App

import numpy as np
from kivy.ext.mpl.backend_kivyagg import FigureCanvasKivyAgg as FigureCanvas
#from backend_kivy import FigureCanvasKivy as FigureCanvas
from kivy.uix.floatlayout import FloatLayout
from matplotlib.transforms import Bbox

import matplotlib.pyplot as plt

def press(event):
    print('press released from test', event.x, event.y, event.button)

def release(event):
    print('release released from test', event.x, event.y, event.button)

def keypress(event):
    print('key down', event.key)

def keyup(event):
    print('key up', event.key)

def motionnotify(event):
    print('mouse move to ', event.x, event.y)

def resize(event):
    print('resize from mpl ', event)

def scroll(event):
    print('scroll event from mpl ', event.x, event.y, event.step)

def figure_enter(event):
    print('figure enter mpl')

def figure_leave(event):
    print('figure leaving mpl')

def close(event):
    print('closing figure')

N = 5
menMeans = (20, 35, 30, 35, 27)
menStd =   (2, 3, 4, 1, 2)

ind = np.arange(N)  # the x locations for the groups
width = 0.35       # the width of the bars

fig, ax = plt.subplots()
rects1 = ax.bar(ind, menMeans, width, color='r', yerr=menStd)

fig.canvas.mpl_connect('button_press_event', press)
fig.canvas.mpl_connect('button_release_event', release)
fig.canvas.mpl_connect('key_press_event', keypress)
fig.canvas.mpl_connect('key_release_event', keyup)
fig.canvas.mpl_connect('motion_notify_event', motionnotify)
fig.canvas.mpl_connect('resize_event', resize)
fig.canvas.mpl_connect('scroll_event', scroll)
fig.canvas.mpl_connect('figure_enter_event', figure_enter)
fig.canvas.mpl_connect('figure_leave_event', figure_leave)
fig.canvas.mpl_connect('close_event', close)

womenMeans = (25, 32, 34, 20, 25)
womenStd =   (3, 5, 2, 3, 3)
rects2 = ax.bar(ind+width, womenMeans, width, color='y', yerr=womenStd)

# add some text for labels, title and axes ticks
ax.set_ylabel('Scores')
ax.set_title('Scores by group and gender')
ax.set_xticks(ind+width)
ax.set_xticklabels( ('G1', 'G2', 'G3', 'G4', 'G5') )

ax.legend( (rects1[0], rects2[0]), ('Men', 'Women') )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

autolabel(rects1)
autolabel(rects2)

canvas = FigureCanvas(fig)
#canvas.blit(Bbox(np.array([[0, 0], [400, 400]], np.int32)))
canvas.draw()

class MatplotlibTest(App):
    title = 'Matplotlib Test'

    def build(self):
        fl = FloatLayout()
        fl.add_widget(canvas)
        return fl

if __name__ == '__main__':
    MatplotlibTest().run()
