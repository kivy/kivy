import kivy
kivy.require('1.3.0')

import math
import time

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.scatter import Scatter
from kivy.clock import Clock
from kivy.vector import Vector
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Rectangle, Triangle
from kivy.logger import Logger

#from android import orientation_enable,orientation_reading
from jnius import autoclass

Logger.info('COMPASS: STARTED')

def LoggerCompleteObj(text,obj):
    import types
    Logger.info('COMPASS: ----- [%s] ----- ----- %s -----'%(text,str(obj)))
    for k in dir(obj):
        if not isinstance(getattr(obj,k), (types.FunctionType, types.BuiltinFunctionType, types.BuiltinMethodType, types.MethodType, types.UnboundMethodType)) and \
           not k.startswith('__'):
            Logger.info('COMPASS: %s = %s'%(str(k),str(getattr(obj,k))))

def LoggerSizeObj(text,obj):
    import types
    for k in ['pos','size','width','height','center','pos_hint','size_hint','rotation']:
        try:
            Logger.info('COMPASS: - [%s] - %s = %s'%(text,k,str(getattr(obj,k))))
        except:
            pass

def LoggerDisplayMetrics(metrics):
    display = {'Default':metrics.DENSITY_DEFAULT,
                    'Device':metrics.DENSITY_DEVICE,
                    'High':metrics.DENSITY_HIGH,
                    'Low':metrics.DENSITY_LOW,
                    'Medium':metrics.DENSITY_MEDIUM,
                    #'TV':metrics.DENSITY_TV,
                    'XHIGH':metrics.DENSITY_XHIGH,
                    'density':metrics.density,
                    'densityDpi':metrics.densityDpi,
                    'heightPixels':metrics.heightPixels,
                    'scaledDensity':metrics.scaledDensity,
                    'widthPixels':metrics.widthPixels,
                    'xdpi':metrics.xdpi,
                    'ydpi':metrics.ydpi}
    #Logger.info('COMPASS: DisplayMetrics display %r'%(display)) 
    for (k,v) in display.items():
        Logger.info('COMPASS: display %s = %s'%(k,v)) 

class CompassWidget(FloatLayout):
    
    def __init__(self, **kwargs):
        super(CompassWidget, self).__init__(**kwargs)

    def build(self,pos,size):
        with self.canvas:
            self.pos = pos
            self.size = size
            self.windrose = Ellipse(source="500px-Windrose.svg.png", pos=pos, size=size)
        #LoggerCompleteObj('CompassWidget build self',self)

class NeedleWidget(Scatter):
    
    def __init__(self, **kwargs):
        super(NeedleWidget, self).__init__(**kwargs)

        self.do_rotation = False
        self.do_translation = False
        self.do_scale = False
        self.auto_bring_to_front = True

    def rotateNeedle(self,angle):
        self.rotation = angle - 90
        #Logger.info('COMPASS: rotateNeedle angle=%s rotation=%s '%(str(angle),str(self.rotation)))
        #LoggerSizeObj('NeedleWidget rotateNeedle',self)

    def build(self,center,needleSize):
        self.pos = center - needleSize/2.
        self.size = needleSize
        self.size_hint = [None, None]
        #LoggerSizeObj('NeedleWidget build',self)
        with self.canvas:
            Color(1., 0, 0)            
            needleTP1 = Vector(needleSize[0]/2.,needleSize[1])
            needleTP2 = Vector(needleSize[0]/2.,0)
            needleTP3 = Vector(-needleSize[0],needleSize[1]/2.)
            needlePoints = (needleTP1[0],needleTP1[1],
                            needleTP2[0],needleTP2[1],
                            needleTP3[0],needleTP3[1])
            self.needleT1 = Triangle(points=needlePoints)
            Color(0.5, 0.5, 0.5)            
            needleTP3 = Vector(2*needleSize[0],needleSize[1]/2.)
            needlePoints = (needleTP1[0],needleTP1[1],
                            needleTP2[0],needleTP2[1],
                            needleTP3[0],needleTP3[1])
            self.needleT2 = Triangle(points=needlePoints)
        #LoggerCompleteObj('NeedleWidget init self',self)

class CompassApp(App):

    def __init__(self, **kwargs):
        super(CompassApp, self).__init__(**kwargs)
        DisplayMetrics = autoclass('android.util.DisplayMetrics')
        metrics = DisplayMetrics()
        metrics.setToDefaults()
        LoggerDisplayMetrics(metrics)
        self.densityDpi = metrics.densityDpi

        Hardware = autoclass('org.renpy.android.Hardware')
        self.hw = Hardware()
        Logger.info('COMPASS: Hardware dir %s'%(str(dir(self.hw))))

    def viewCompass(self, *largs):
        (x, y, z) = self.hw.magneticFieldSensorReading()
        declination = Vector(x,y).angle((0,1))
        #Logger.info('COMPASS: viewCompass x=%s y=%s z=%s declination=%s'%(x,y,z,declination))
        self.needle.rotateNeedle(declination)

    def stopApp(self,*largs):
        self.hw.magneticFieldSensorEnable(False)
        Logger.info('COMPASS: stop largs '+str(largs))
        self.stop()

    def build(self):
        parent = FloatLayout(size=(500,500)) 
        Window.clearcolor = (1, 1, 1, 1)

        self.Compass = CompassWidget()
        parent.add_widget(self.Compass)
        if self.densityDpi == 240:
            CompassPos = Vector(50., 200.)
            CompassSize = Vector(400., 400.)
            needleSize = Vector(100., 60.)
            stopButtonHeight = 60
        elif self.densityDpi == 320:
            CompassPos = Vector(75., 300.)
            CompassSize = Vector(600., 600.)
            needleSize = Vector(150., 90.)
            stopButtonHeight = 80
        else:
            Logger.info('COMPASS: widget size should be adopted - minimum used for densityDpi=%s'%(str(self.densityDpi)))
            CompassPos = Vector(50., 200.)
            CompassSize = Vector(400., 400.)
            needleSize = Vector(100., 60.)
            stopButtonHeight = 60
        self.Compass.build(pos=CompassPos,size=CompassSize)

        self.needle = NeedleWidget()
        parent.add_widget(self.needle)
        self.needle.build(center=CompassPos+CompassSize/2.,needleSize=needleSize)

        self.stopButton = Button(text='Stop', pos_hint={'right':1}, size_hint=(None,None), height=stopButtonHeight)
        parent.add_widget(self.stopButton)
        self.stopButton.bind(on_press=self.stopApp)

        LoggerCompleteObj('CompassApp build parent',parent)
        self.hw.magneticFieldSensorEnable(True)
        Clock.schedule_interval(self.viewCompass, 1.)
        return parent

if __name__ in ('__main__', '__android__'):
    CompassApp().run()


