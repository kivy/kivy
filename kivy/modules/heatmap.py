'''
Create/fill an heatmap in database
'''

from kivy import MTWidget, Logger
import sys
import os
import sqlite3

class HeatMap(MTWidget):
    def __init__(self, **kwargs):
        super(HeatMap, self).__init__(**kwargs)
        self.appname = sys.argv[0]
        if self.appname == '':
            self.appname = 'python'
        elif self.appname[-3:] == '.py':
            self.appname = self.appname[:-3]
        self.filename = 'heatmap-%s.db' % self.appname
        self.db = sqlite3.connect(self.filename)
        try:
            self.db.execute('''
                CREATE TABLE heatmap (
                    x NUMERIC,
                    y NUMERIC,
                    time NUMERIC
                )
            ''')
            self.db.commit()
            Logger.info('Heatmap: Create new database for heatmap in %s' % self.filename)
        except sqlite3.OperationalError:
            Logger.info('Heatmap: Fill heatmap database in %s' % self.filename)

    def on_touch_down(self, touch):
        self.db.execute('''
            INSERT INTO heatmap
            VALUES (%f, %f, %f)
        ''' % (touch.sx, touch.sy, touch.time_start))
        self.db.commit()

    def on_update(self):
        self.bring_to_front()


def start(win, ctx):
    ctx.w = HeatMap()
    win.add_widget(ctx.w)

def stop(win, ctx):
    win.remove_widget(ctx.w)
