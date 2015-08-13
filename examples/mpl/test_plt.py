#!/usr/bin/env python
# a bar plot with errorbars
import matplotlib
## matplotlib.use('Gtk')
matplotlib.use('module://kivy.ext.mpl.backend_kivy')
#matplotlib.use('Gtk')

import numpy as np
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
menStd = (2, 3, 4, 1, 2)

ind = np.arange(N)  # the x locations for the groups
width = 0.35       # the width of the bars

figure, ax = plt.subplots()

figure.canvas.mpl_connect('button_press_event', press)
figure.canvas.mpl_connect('button_release_event', release)
figure.canvas.mpl_connect('key_press_event', keypress)
figure.canvas.mpl_connect('key_release_event', keyup)
figure.canvas.mpl_connect('motion_notify_event', motionnotify)
figure.canvas.mpl_connect('resize_event', resize)
figure.canvas.mpl_connect('scroll_event', scroll)
figure.canvas.mpl_connect('figure_enter_event', figure_enter)
figure.canvas.mpl_connect('figure_leave_event', figure_leave)
figure.canvas.mpl_connect('close_event', close)

fig1 = plt.gcf()
rects1 = ax.bar(ind, menMeans, width, color='r', yerr=menStd)

womenMeans = (25, 32, 34, 20, 25)
womenStd = (3, 5, 2, 3, 3)
rects2 = ax.bar(ind + width, womenMeans, width, color='y', yerr=womenStd)

# add some text for labels, title and axes ticks
ax.set_ylabel('---------------------------Scores----------------------------')
ax.set_title('Scores by group and gender')
ax.set_xticks(ind + width)
ax.set_yticklabels(('Ahh', '-----------G1------', 'G2', 'G3', 'G4', 'G5', 'G5',
                    'G5', 'G5'), rotation=90)
ax.legend((rects1[0], rects2[0]), ('Men', 'Women'))


def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2., 1.05 * height, '%d' %
                int(height), ha='center', va='bottom')

autolabel(rects1)
autolabel(rects2)


plt.draw()
#fig1.set_size_inches(18.5, 10.5, forward = True)
plt.show()
