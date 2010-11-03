from kivy import *

scatter_test_xml = '''
<MTBoxLayout>
<MTGridLayout cols='2'>
        <MTLabel label='"Scale:"' color='(1,1,1)' />
        <MTSlider id='"scale"' orientation='"horizontal"' min='0.2' max='5.0'/>
        <MTLabel label='"Rotation:"' color='(1,1,1)' />
        <MTSlider id='"rotation"' min='0' max='360' orientation='"horizontal"'/>
</MTGridLayout>
<MTButton id='"pos"' label='"pos=(100,500)"' size_hint='(1,1)'/>
<MTButton id='"center"' label='"center=(500,200)"' size_hint='(1,1)' />
<MTToggleButton id='"transform"' label='"Save Transform"' size_hint='(1,1)' />
</MTBoxLayout>
'''

class ScatterTest(MTWidget):
    def __init__(self, **kwargs):
        super(ScatterTest, self).__init__(**kwargs)
        self.xml = XMLWidget(xml=scatter_test_xml)
        self.xml.root.width=getWindow().width
        self.xml.autoconnect(self)

        self.scatter = MTScatterWidget(style={'draw-background':1})
        self.scatter.connect('on_transform', self.update_values)

        self.add_widget(self.xml.root)
        self.add_widget(self.scatter)

    def update_values(self, *args):
        self.xml.getById('scale').value = self.scatter.scale
        self.xml.getById('rotation').value = self.scatter.rotation

    def on_scale_value_change(self, val):
        self.scatter.scale = val

    def on_rotation_value_change(self, val):
        self.scatter.rotation = val

    def on_pos_release(self, *args):
        anim = Animation(pos=(100,500))
        self.scatter.do(anim)

    def on_center_release(self, *args):
        anim = Animation(center=(500,200), scale=4)
        self.scatter.do(anim)

    def on_transform_release(self, *args):
        toggle = self.xml.getById('transform')
        if toggle.state == 'down':
            self.saved_transform = (self.scatter.pos, self.scatter.rotation, self.scatter.scale)
            toggle.label = "Restore Transform"
        else:
            p,r,s = self.saved_transform
            anim = Animation(pos=p, rotation=r, scale=s)
            self.scatter.do(anim)
            toggle.label = "Save Transform"


    def draw(self):
        set_color(0,0,0,8)
        drawRectangle((0,0), getWindow().size)

        set_color(1,0,0)
        bbox = self.scatter.bbox
        drawRectangle(*bbox)

        set_color(0,1,0)
        drawCircle(bbox[0], radius=20)
        drawLabel("pos", pos=self.scatter.pos)

        set_color(0,0,1)
        drawCircle(self.scatter.center, radius=20)
        drawLabel("center", pos=self.scatter.center)

        set_color(1,0,1)
        drawCircle((500,200), radius=20)
        drawLabel("(500,200)", pos=(500,200))

        set_color(1,0,1)
        drawCircle((100,500), radius=20)
        drawLabel("(100,500)", pos=(100,500))




runTouchApp(ScatterTest())
