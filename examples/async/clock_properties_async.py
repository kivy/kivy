import os
os.environ['KIVY_EVENTLOOP'] = 'async'

import asyncio

from kivy.app import App
from kivy.lang.builder import Builder
from kivy.clock import Clock

kv = '''
BoxLayout:
    orientation: 'vertical'
    Button:
        id: btn
        text: 'Prezzz me a few timez'
    BoxLayout:
        Label:
            id: label1
        Label:
            id: label2
        Label:
            id: label3
        Label:
            id: label4

'''


async def update_label1(root):
    label = root.ids.label1

    i = 0
    async for _ in root.ids.btn.async_bind('on_release'):
        label.text = 'Ouch x{}'.format(i)
        if i == 7:
            break
        i += 1
    print('Done with update_label1')


async def update_label2_from_label1(root):
    label1 = root.ids.label1
    label2 = root.ids.label2

    i = 0
    async for instance, value in label1.async_bind(
            'text', filter=lambda x: x[1] in ['Ouch x3', 'Ouch x6']):
        if not i:
            label2.text = "Stop it! I can't take it anymore!"
        elif i == 1:
            label2.text = "Why are you still doing it?"
            break
        i += 1
    print('Done with update_label2_from_label1')


async def watch_label1(root):
    label1 = root.ids.label1
    async for value in label1.async_bind('text', convert=lambda x: x[1]):
        print('Label 1 got "{}"'.format(value))
    print('Done with watch_label1')


async def watch_periodic_dental_callback(event, root):
    label3 = root.ids.label3

    i = 0
    async for dt, in event.async_event():
        label3.text = 'Cleanup {} ({})'.format(i, dt)
        if i == 5:
            event.cancel()
        i += 1
    print('Done with watch_periodic_dental_callback')


async def watch_single_callback(event, root):
    label4 = root.ids.label4

    i = 0
    async for dt, in event.async_event():
        label4.text = 'Single {} ({})'.format(i, dt)
        i += 1
    print('Done with watch_single_callback')


async def watch_canceled_callback(event):
    async_event = event.async_event()
    # have to cancel after getting the async event, otherwise we wait forever
    event.cancel()
    async for dt, in async_event:
        print('Executed single callback - should not occur')
    print('Done with watch_canceled_callback')


class MyApp(App):

    def build(self):
        return Builder.load_string(kv)

    def periodic_dental_callback(self, dt):
        print('peridoic callback was {}'.format(dt))

    def single_yearly_callback(self, dt):
        print('single callback was {}'.format(dt))

    def on_start(self):
        periodic_ev = Clock.schedule_interval(
            self.periodic_dental_callback, 2.5)
        single_ev = Clock.schedule_once(self.single_yearly_callback, 2.5)
        cancel_ev = Clock.schedule_once(self.single_yearly_callback, 2.5)

        loop = asyncio.get_event_loop()
        loop.create_task(update_label1(self.root))
        loop.create_task(update_label2_from_label1(self.root))
        loop.create_task(watch_label1(self.root))

        loop.create_task(
            watch_periodic_dental_callback(periodic_ev, self.root))
        loop.create_task(watch_single_callback(single_ev, self.root))
        loop.create_task(watch_canceled_callback(cancel_ev))


if __name__ == '__main__':
    MyApp().run()
